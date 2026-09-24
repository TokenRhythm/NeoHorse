"""Import the external loader in spawned workers via vLLM's extension hook."""
from vllm_loader import register

register()


class RegisterLoader:
    pass
