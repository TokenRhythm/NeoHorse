"""Optional single-image input, using the original JEV decision template."""
import base64
from io import BytesIO
import json
from pathlib import Path
from PIL import Image
from jev_runtime.model import SPECIAL, user_tokens, encode, rows_of
from jev_runtime.schema import SystemOneRequest, to_record


def prepare_image(head, request):
    value = request['image']
    if not isinstance(value, str) or not value:
        raise ValueError('image must be a local PNG/JPEG path or a base64 data URI')
    if value.startswith('data:'):
        header, data = value.split(',', 1)
        if header not in ('data:image/png;base64', 'data:image/jpeg;base64'):
            raise ValueError('Only PNG/JPEG base64 data URIs are supported')
        if len(data) > 12 * 1024 * 1024:
            raise ValueError('Image exceeds 8 MiB')
        blob = base64.b64decode(data, validate=True)
    else:
        path = Path(value)
        if path.stat().st_size > 8 * 1024 * 1024:
            raise ValueError('Image exceeds 8 MiB')
        blob = path.read_bytes()
    if len(blob) > 8 * 1024 * 1024:
        raise ValueError('Image exceeds 8 MiB')
    with Image.open(BytesIO(blob)) as image:
        if image.format not in ('PNG', 'JPEG') or image.width * image.height > 16777216:
            raise ValueError('Expected PNG/JPEG with at most 16 megapixels')
        image.load()
        rgb = image.convert('RGB')
    stream = BytesIO()
    rgb.save(stream, format='PNG')
    uri = 'data:image/png;base64,' + base64.b64encode(stream.getvalue()).decode('ascii')
    if head.processor is None:
        from transformers.models.qwen2_vl.image_processing_pil_qwen2_vl import Qwen2VLImageProcessorPil
        head.processor = Qwen2VLImageProcessorPil.from_pretrained(
            head.root / 'backbone', local_files_only=True)
    config = json.loads((head.root / 'backbone/config.json').read_text(encoding='utf-8'))
    feature = head.processor(images=[rgb], return_tensors='pt')
    count = int(feature['image_grid_thw'].prod().item()) // config['vision_config']['spatial_merge_size'] ** 2
    if not 0 < count <= 1024:
        raise ValueError('Image exceeds 1024 visual tokens; resize the image')
    text_request = {k: v for k, v in request.items() if k != 'image'}
    record, metadata = to_record(SystemOneRequest(**text_request))
    if len(metadata) != 1:
        raise ValueError('Image requests currently require exactly one question')
    state = record['state']
    if state.count('<image>') > 1:
        raise ValueError('Only one <image> marker is supported')
    before, after = state.split('<image>', 1) if '<image>' in state else ('', '\n' + state)
    prefix = [head.tokenizer.convert_tokens_to_ids(SPECIAL[0])] + user_tokens(head.tokenizer, before)
    suffix = user_tokens(head.tokenizer, after)
    if len(prefix) + len(suffix) > 8192:
        raise ValueError('Text state exceeds 8192 tokens')
    vision = [config['vision_start_token_id'], config['image_token_id'], config['vision_end_token_id']]
    expanded = prefix + vision[:1] + [vision[1]] * count + vision[2:] + suffix
    packed = encode(head.tokenizer, {**record, 'state': ''}, strict=True,
                    option_isolation=False, max_state=8192, max_branch=12288)
    _, _, branches = rows_of(packed)
    rows = []
    for branch, meta in zip(branches, metadata, strict=True):
        ids = expanded + branch['ids']
        if len(ids) > 12288:
            raise ValueError('Complete multimodal input exceeds 12288 tokens')
        prompt_ids = prefix + vision + suffix + branch['ids']
        # vLLM's native HTTP multimodal pooling uses messages. Render only the
        # exact decision sequence, without chat role markers or a generation prompt.
        decode = lambda tokens: head.tokenizer.decode(tokens, skip_special_tokens=False,
                                                       clean_up_tokenization_spaces=False)
        before_text, after_text = decode(prefix), decode(suffix + branch['ids'])
        rendered = before_text + decode(vision) + after_text
        if head.tokenizer.encode(rendered, add_special_tokens=False) != prompt_ids:
            raise ValueError('Decision text does not round-trip through the tokenizer')
        rows.append(dict(ids=ids, prompt_ids=prompt_ids, image=uri,
                         before=before_text, after=after_text, image_tokens=count,
                         decide=len(expanded) + branch['decide'],
                         options=[len(expanded) + i for i in branch['opts']], meta=meta))
    return rows
