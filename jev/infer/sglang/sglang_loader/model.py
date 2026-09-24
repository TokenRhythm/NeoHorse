"""External SGLang loader; inherited forward uses native Qwen3.5 operators."""
from sglang.srt.models.qwen3_5 import Qwen3_5ForConditionalGeneration as Native
from weight_mapping import multimodal_weights


class Qwen3_5ForConditionalGeneration(Native):
    def load_weights(self, weights):
        loaded = super().load_weights(multimodal_weights(weights))
        missing = set(dict(self.named_parameters())) - loaded
        if missing:
            raise RuntimeError('Unloaded model parameters: ' + str(sorted(missing)))
        return loaded


EntryClass = Qwen3_5ForConditionalGeneration
