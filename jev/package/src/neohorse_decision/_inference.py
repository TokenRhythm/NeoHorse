"""Offline loader for the merged NeoHorse decision model (not a chat LM)."""
import json
from pathlib import Path

import torch
from safetensors.torch import load_file
from transformers import AutoModel, AutoTokenizer
from ._vendor.model import DecisionModel, PointerHead
from ._vendor.schema import SystemOneRequest, to_record


def load_bundle(bundle, device='cuda'):
    root = Path(bundle)
    meta = json.loads((root / 'model_manifest.json').read_text())
    torch.set_num_threads(4)
    torch.backends.cuda.matmul.allow_tf32 = False
    torch.backends.cudnn.allow_tf32 = False
    torch.backends.cuda.enable_flash_sdp(True)
    torch.backends.cuda.enable_mem_efficient_sdp(True)
    tok = AutoTokenizer.from_pretrained(root / 'tokenizer', local_files_only=True)
    backbone, info = AutoModel.from_pretrained(
        root / 'backbone', dtype=torch.bfloat16, attn_implementation='sdpa',
        local_files_only=True, output_loading_info=True)
    assert not info.get('missing_keys') and not info.get('unexpected_keys'), info
    assert not info.get('mismatched_keys') and not info.get('error_msgs'), info
    assert type(backbone).__name__ == meta['backbone_class']
    # Bypass the training constructor: it loads the original base checkpoint.
    # This bundle instead supplies the complete, already merged backbone.
    model = DecisionModel.__new__(DecisionModel)
    torch.nn.Module.__init__(model)
    # Some Transformers modules are kept FP32 during from_pretrained even when
    # dtype=BF16. The evaluated serving loader explicitly cast the WHOLE merged
    # backbone after merging, so reproduce that cast after reload as well.
    backbone = backbone.to(device=device, dtype=torch.bfloat16)
    if type(backbone).__name__ == 'Qwen3_5Model':
        model.multimodal = backbone
        model.lm = backbone.language_model
    else:
        model.lm = backbone
    text_config = model.lm.config
    model.head = PointerHead(text_config.hidden_size, dp=meta['head_dim'])
    model.head.load_state_dict(load_file(str(root / 'pointer_head.safetensors')))
    model.head = model.head.to(device=device, dtype=torch.float32)
    model.pad_id = tok.pad_token_id if tok.pad_token_id is not None else 0
    model.hybrid = 'linear_attention' in set(getattr(text_config, 'layer_types', None) or [])
    model.option_isolation = meta['option_isolation']
    model.device = device
    assert model.hybrid == meta['hybrid']
    assert not (model.hybrid and model.option_isolation)
    model.eval()
    return tok, model


def predict(tok, model, request, max_state=2048, max_branch=8192):
    rec, meta = to_record(SystemOneRequest(**request))
    enc = model.encode(tok, rec, strict=True, max_state=max_state, max_branch=max_branch)
    with torch.inference_mode():
        ps = [p.tolist() for p in model.probs(enc)]
    answers = {}
    for p, m in zip(ps, meta):
        if m['type'] == 'choice':
            answers[m['id']] = dict(type='choice', choice=m['keys'][max(range(len(p)), key=p.__getitem__)],
                                    probabilities=dict(zip(m['keys'], p)))
        elif m['type'] == 'noul':
            answers[m['id']] = dict(type='noul', noul=p[1], probabilities={'false': p[0], 'true': p[1]})
        else:
            answers[m['id']] = dict(type='score', score=sum(i * v for i, v in enumerate(p)),
                                    legend=m['legend'], probabilities={str(i): v for i, v in enumerate(p)})
    return dict(answers=answers, input_tokens=len(enc['ids']))

