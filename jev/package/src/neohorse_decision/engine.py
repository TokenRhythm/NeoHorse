import json
import threading
from ._inference import load_bundle, predict
from ._vendor.schema import SystemOneRequest, to_record
from .systemone import MODEL_ID, MODEL_NAMES


class BusyError(RuntimeError):
    pass


class DecisionEngine:
    """One serialized GPU worker. Requests are never silently truncated."""
    model_id = MODEL_ID

    def __init__(self, model_dir, device='cuda', max_state=2048, max_branch=8192,
                 max_questions=16, max_tokens=32768):
        self.model_dir, self.device = model_dir, device
        self.tokenizer, self.model = load_bundle(model_dir, device)
        self.max_state, self.max_branch = max_state, max_branch
        self.max_questions, self.max_tokens = max_questions, max_tokens
        self._lock = threading.Lock()

    def predict(self, request):
        if len(json.dumps(request, ensure_ascii=False).encode()) > 1024 * 1024:
            raise ValueError('Request exceeds 1 MiB')
        req = SystemOneRequest(**request)
        if req.model not in MODEL_NAMES:
            raise ValueError('Unknown model; use ' + self.model_id)
        if len(req.questions) > self.max_questions:
            raise ValueError('Too many questions')
        if not self._lock.acquire(blocking=False):
            raise BusyError('Model busy; retry later')
        try:
            rec, _ = to_record(req)
            enc = self.model.encode(self.tokenizer, rec, strict=True,
                                    max_state=self.max_state, max_branch=self.max_branch)
            # Hybrid execution repeats the state in each independent question row.
            state_length = sum(s == 0 for s in enc['seg'])
            effective_tokens = len(enc['ids']) + (len(req.questions) - 1) * state_length
            if effective_tokens > self.max_tokens:
                raise ValueError('Request exceeds total expanded token budget')
            result = predict(self.tokenizer, self.model, request, self.max_state, self.max_branch)
            return dict(model=self.model_id, **result)
        finally:
            self._lock.release()
