"""Engine-independent JEV encoding and FP32 CPU readout."""
import json
from pathlib import Path

import torch
from safetensors.torch import load_file
from transformers import AutoTokenizer
from jev_runtime.model import PointerHead, encode, rows_of
from jev_runtime.schema import SystemOneRequest, to_record


class CPUHead:
    def __init__(self, bundle):
        root = Path(bundle)
        self.root = root
        self.processor = None
        manifest = json.loads((root / 'model_manifest.json').read_text(encoding='utf-8'))
        if manifest['option_isolation'] or not manifest['hybrid'] or manifest['temperature'] != 1:
            raise ValueError('This adapter requires the hybrid, non-isolated, temperature=1 contract')
        weights = load_file(str(root / 'pointer_head.safetensors'), device='cpu')
        self.width = weights['q.weight'].shape[1]
        self.head = PointerHead(self.width, weights['q.weight'].shape[0]).cpu().float().eval()
        self.head.load_state_dict(weights, strict=True)
        self.head.requires_grad_(False)
        self.tokenizer = AutoTokenizer.from_pretrained(root / 'tokenizer')

    def prepare(self, request):
        if not isinstance(request, dict):
            raise ValueError('Request must be a JSON object')
        unknown = set(request) - {'model', 'state', 'questions', 'image'}
        if unknown:
            raise ValueError('Unknown request fields: ' + ', '.join(sorted(unknown)))
        if request.get('model', 'neohorse-jev') not in ('neohorse-jev', 'NeoHorse-Jev-4B'):
            raise ValueError('Unknown model; use NeoHorse-Jev-4B')
        questions = request.get('questions')
        if not isinstance(questions, dict) or not 1 <= len(questions) <= 16:
            raise ValueError('Expected 1..16 questions')
        for question in questions.values():
            if not isinstance(question, dict) or set(question) - {'type', 'instructions', 'criteria'}:
                raise ValueError('Unknown or invalid question fields')
            if question.get('type') == 'noul' and isinstance(question.get('criteria'), dict):
                if set(question['criteria']) - {'false', 'true'}:
                    raise ValueError('Noul criteria keys must be false and/or true')
        # Fail on invalid schemas and non-finite JSON before decoding any image.
        text_request = {k: v for k, v in request.items() if k != 'image'}
        json.dumps(text_request, allow_nan=False)
        SystemOneRequest(**text_request)
        if request.get('image') is not None:
            from vision import prepare_image
            return prepare_image(self, request)
        request = {k: v for k, v in request.items() if k != 'image'}
        record, metadata = to_record(SystemOneRequest(**request))
        if not 1 <= len(metadata) <= 16:
            raise ValueError('Expected 1..16 questions')
        packed = encode(self.tokenizer, record, strict=True, option_isolation=False,
                        max_state=8192, max_branch=12288)
        state, state_pos, branches = rows_of(packed)
        rows = []
        for branch, meta in zip(branches, metadata, strict=True):
            ids = state + branch['ids']
            if state_pos + branch['pos'] != list(range(len(ids))) or len(ids) > 12288:
                raise ValueError('Unsupported positions or question too long')
            rows.append(dict(ids=ids, decide=len(state) + branch['decide'],
                             options=[len(state) + i for i in branch['opts']], meta=meta))
        if sum(len(row['ids']) for row in rows) > 32768:
            raise ValueError('Expanded input exceeds 32768 tokens')
        return rows

    @torch.inference_mode()
    def readout(self, row, hidden):
        h = torch.as_tensor(hidden, device='cpu', dtype=torch.float32)
        # SGLang can wrap prompt states in a single batch dimension.
        while h.ndim > 2 and h.shape[0] == 1:
            h = h.squeeze(0)
        expected = (len(row['ids']), self.width)
        if tuple(h.shape) != expected or not torch.isfinite(h).all():
            raise ValueError(f'Expected finite final states {expected}, got {tuple(h.shape)}')
        logits = self.head(h[row['decide']], h[row['options']])
        if not torch.isfinite(logits).all():
            raise ValueError('Non-finite pointer logits')
        p = logits.softmax(-1).tolist()
        meta = row['meta']
        if meta['type'] == 'choice':
            answer = dict(type='choice', choice=meta['keys'][max(range(len(p)), key=p.__getitem__)],
                          probabilities=dict(zip(meta['keys'], p, strict=True)))
        elif meta['type'] == 'noul':
            if len(p) != 2:
                raise ValueError('Noul must have two candidates')
            answer = dict(type='noul', noul=p[1], probabilities=dict(zip(['false', 'true'], p)))
        elif meta['type'] == 'score':
            answer = dict(type='score', score=sum(i * x for i, x in enumerate(p)),
                          legend=meta['legend'], probabilities={str(i): x for i, x in enumerate(p)})
        else:
            raise ValueError('Unknown question type')
        return answer

    def result(self, rows, hidden_states):
        return dict(model='NeoHorse-Jev-4B', answers={
            row['meta']['id']: self.readout(row, h)
            for row, h in zip(rows, hidden_states, strict=True)},
            usage={'expanded_input_tokens': sum(len(r['ids']) for r in rows)})
