"""External vLLM model registration. No engine files or operators modified."""
from vllm.model_executor.models.qwen3_5 import Qwen3_5ForConditionalGeneration as Native
from weight_mapping import multimodal_weights


class Qwen3_5ForConditionalGeneration(Native):
    def load_weights(self, weights):
        return super().load_weights(multimodal_weights(weights))


def register():
    from vllm import ModelRegistry
    # Register lazily so spawned engine workers import this external file too.
    ModelRegistry.register_model('Qwen3_5ForConditionalGeneration', 'vllm_loader:Qwen3_5ForConditionalGeneration')
