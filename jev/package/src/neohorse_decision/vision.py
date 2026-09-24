"""Local image decisions using the unified NeoHorse multimodal backbone.

Local PIL image inference; HTTP transport is implemented in image_input.py/server.py.
"""
import json
from pathlib import Path
import torch
from neohorse_decision import DecisionEngine
from neohorse_decision.engine import BusyError
from neohorse_decision._vendor.schema import SystemOneRequest, to_record
from neohorse_decision.systemone import MODEL_ID, MODEL_NAMES, with_confidence


class VisionDecisionEngine:
    """One local image and one Choice/Noul/Score question per visual request."""

    def __init__(self, model_dir, device='cuda', *, text_engine=None):
        from transformers.models.qwen2_vl.image_processing_pil_qwen2_vl import Qwen2VLImageProcessorPil
        self.root=Path(model_dir)
        self.text=text_engine if text_engine is not None else DecisionEngine(self.root,device=device)
        self.device=device
        if not hasattr(self.text.model,'multimodal'):
            raise ValueError('VisionDecisionEngine requires the unified multimodal backbone')
        self.wrapper=self.text.model.multimodal
        config=self.wrapper.config
        self.visual_tensor_count=len(self.wrapper.visual.state_dict())
        self.processor=Qwen2VLImageProcessorPil.from_pretrained(self.root/'backbone',local_files_only=True,
            size={'shortest_edge':65536,'longest_edge':1048576})
        for token,expected in (('<|image_pad|>',config.image_token_id),('<|vision_start|>',config.vision_start_token_id),('<|vision_end|>',config.vision_end_token_id)):
            if self.text.tokenizer.convert_tokens_to_ids(token)!=expected:
                raise ValueError('Vision token ID mismatch: '+token)

    def predict(self,request,image=None,*,through_wrapper=False):
        if image is None and not through_wrapper:
            return with_confidence(self.text.predict(request))
        req=SystemOneRequest(**request)
        if req.model not in MODEL_NAMES:raise ValueError('Unknown model; use '+MODEL_ID)
        if len(req.questions)!=1:raise ValueError('Visual adapter currently supports one question per request')
        if len(json.dumps(request,ensure_ascii=False).encode())>1024*1024:raise ValueError('Request exceeds 1 MiB')
        if image is not None:
            from PIL import Image
            if not isinstance(image,Image.Image):raise TypeError('image must be a locally decoded PIL image')
            if image.width*image.height>4194304:raise ValueError('Source image exceeds 4 megapixels')
        if not self.text._lock.acquire(blocking=False):raise BusyError('Model busy; retry later')
        try:
            rec,metadata=to_record(req)
            enc=self.text.model.encode(self.text.tokenizer,rec,strict=True,max_state=self.text.max_state,max_branch=self.text.max_branch)
            prefix=[];extra={};image_tokens=0
            if image is not None:
                batch=self.processor(images=image.convert('RGB'),return_tensors='pt')
                image_tokens=int(batch['image_grid_thw'][0].prod())//self.processor.merge_size**2
                if not 0<image_tokens<=1024:raise ValueError('Processed image exceeds 1024 visual tokens')
                prefix=[self.wrapper.config.vision_start_token_id]+[self.wrapper.config.image_token_id]*image_tokens+[self.wrapper.config.vision_end_token_id]
                extra={k:batch[k].to(self.device) for k in ('pixel_values','image_grid_thw')}
            if len(enc['ids'])+len(prefix)>12288:raise ValueError('Expanded multimodal input exceeds 12288 tokens')
            ids=torch.tensor([[enc['ids'][0]]+prefix+enc['ids'][1:]],device=self.device)
            # Do not carry positional state across independent images/requests.
            self.wrapper.rope_deltas=None
            with torch.inference_mode():
                h=self.wrapper(input_ids=ids,attention_mask=torch.ones_like(ids),
                    mm_token_type_ids=(ids==self.wrapper.config.image_token_id).long(),use_cache=False,**extra).last_hidden_state[0].float()
                delta=len(prefix)
                z=self.text.model.head(h[enc['decide_idx'][0]+delta],h[torch.tensor(enc['opt_idx'][0],device=self.device)+delta])
                p=z.softmax(-1).cpu().tolist()
            m=metadata[0]
            if not all(torch.isfinite(torch.tensor(p))):raise RuntimeError('Non-finite output probabilities')
            if m['type']=='choice':
                answer=dict(type='choice',choice=m['keys'][max(range(len(p)),key=p.__getitem__)],probabilities=dict(zip(m['keys'],p)))
            elif m['type']=='noul':
                answer=dict(type='noul',noul=p[1],probabilities={'false':p[0],'true':p[1]})
            else:
                answer=dict(type='score',score=sum(i*v for i,v in enumerate(p)),legend=m['legend'],probabilities={str(i):v for i,v in enumerate(p)})
            return with_confidence(dict(model=MODEL_ID,answers={m['id']:answer},input_tokens=len(enc['ids'])+delta,image_tokens=image_tokens))
        finally:
            self.text._lock.release()
