# NeoHorse-Jev Inference

Choose vLLM or SGLang for text-only or single-image-plus-text requests. From the NeoHorse repository root, run `cd jev` before the commands below and replace `/path/to/model` with the complete model directory downloaded from [Hugging Face](https://huggingface.co/TokenRhythm/NeoHorse-Jev-4B/tree/main) or [ModelScope](https://www.modelscope.cn/models/TokenRhythm/NeoHorse-Jev-4B).

Use an existing environment for your chosen backend. If example dependencies are missing, install the corresponding requirements; skip this step when they are already installed:

```bash
# Choose one; do not install both into the same environment
python -m pip install -r infer/vllm/requirements.txt
python -m pip install -r infer/sglang/requirements.txt
```

Both backends use the bundled [request.json](request.json):

```json
{
  "state": "The left path is clear; the path ahead is blocked.",
  "questions": {
    "move": {
      "type": "choice",
      "instructions": "Choose a clear direction.",
      "criteria": {"left": "Turn left", "forward": "Go forward"}
    }
  }
}
```

## vLLM 0.28.0

Use an environment with **vLLM 0.28.0** and the example dependencies already installed. `launch.py` starts native `vllm serve`; `infer.py` calls the native `/pooling` endpoint.

Start the server and keep this terminal running:

```bash
CUDA_VISIBLE_DEVICES=0 python infer/vllm/launch.py \
  --bundle /path/to/model --port 30000
```

Once the server is ready, run this from another terminal:

```bash
python infer/vllm/infer.py --bundle /path/to/model \
  --url http://127.0.0.1:30000 --request infer/request.json
```

Results are printed to the terminal. Read `answers.move.choice` and `answers.move.probabilities`. Repeated requests do not reload the backbone.

## SGLang 0.5.17

Use an environment with **SGLang 0.5.17** and the example dependencies already installed.

Start the server:

```bash
CUDA_VISIBLE_DEVICES=0 python infer/sglang/launch.py \
  --bundle /path/to/model --port 30000
```

Once the server is ready, run this from another terminal:

```bash
python infer/sglang/infer.py --bundle /path/to/model \
  --url http://127.0.0.1:30000 --request infer/request.json
```

Results are printed to the terminal. Read `answers.move.choice` and `answers.move.probabilities`. Repeated requests do not reload the backbone. Both backends accept the same request format and return the same fields, although probability values may differ slightly.

## Image Input (Both Backends)

Add the optional `image` field and save the request as `request-image.json`. The server startup command stays the same:

```json
{
  "state": "Use the image to determine which path is clear.",
  "image": "/path/to/road.jpg",
  "questions": {
    "move": {
      "type": "choice",
      "instructions": "Choose a clear direction.",
      "criteria": {"left": "Turn left", "forward": "Go forward"}
    }
  }
}
```

`image` accepts a client-local PNG/JPEG path (relative to the current working directory), `data:image/png;base64,...`, or `data:image/jpeg;base64,...`. The client reads and transmits the image contents; the file does not need to exist on the server. Omit `image` or set it to `null` for text-only input.

```bash
# Choose the matching backend and reuse the running server
python infer/vllm/infer.py --bundle /path/to/model \
  --url http://127.0.0.1:30000 --request request-image.json

python infer/sglang/infer.py --bundle /path/to/model \
  --url http://127.0.0.1:30000 --request request-image.json
```

Both return `answers.move.choice` and `answers.move.probabilities`. Image requests currently support one image and one question, with limits of 8 MiB, 16 million pixels, and 1,024 visual tokens. Resize images that exceed these limits. You may include one `<image>` marker in `state` to choose the insertion point; without it, the image is placed at the beginning of the background.

> The model directory must include the complete language and vision weights in `backbone/` (including `preprocessor_config.json`), plus `tokenizer/`, `pointer_head.safetensors`, and `model_manifest.json`. The supplied adapters have passed text and image smoke tests in the existing environments at the versions above. Model results and the backend used for each measurement are listed in [Evaluation](../README.md#evaluation). Fresh installation and production concurrency have not yet been validated.
