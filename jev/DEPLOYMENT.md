# Deployment and API Guide

This guide covers installation and text and image inference with the `neohorse_decision` runtime. See the [README](README.md) for the model overview and quickstart, or the [backend guide](infer/README.md) for the separate vLLM and SGLang adapters.

## 1. Installation

Download the complete release from the [ModelScope model repository](https://www.modelscope.cn/models/TokenRhythm/NeoHorse-Jev-4B) and install its bundled runtime. Loading the model requires `backbone/`, `tokenizer/`, `pointer_head.safetensors`, and `model_manifest.json`. Image examples are also included in the release.

The recorded environment is Linux, Python 3.12, PyTorch 2.8.0, Transformers 5.17.0, Triton 3.7.1, and flash-linear-attention 0.5.2, with a CUDA GPU that supports BF16. Version details are in [environment.json](https://www.modelscope.cn/models/TokenRhythm/NeoHorse-Jev-4B/file/view/master/environment.json). The following commands assume these ML dependencies are already installed in an isolated environment:

```bash
export MODEL_DIR="/path/to/NeoHorse-Jev-4B"
cd "$MODEL_DIR"

python -m pip install --no-deps dist/neohorse_decision-1.0.0-py3-none-any.whl
python -m pip install 'fastapi==0.141.1' 'uvicorn==0.53.0' 'starlette==1.6.0' 'httpx==0.28.1' 'pillow==12.3.0'
```

`--no-deps` does not install ML dependencies such as Torch. When installing or upgrading Torch, check whether dependency resolution changes the Triton version. Avoid mixing in Transformers or TorchVision packages from other environments.

`backbone/` contains both language and vision parameters and occupies approximately 9.08 GB. The separate decision head occupies approximately 5.25 MB. Actual GPU memory usage also depends on the input and runtime settings. Load the complete directory with the matching runtime.

### Install from This Source Repository

With the native ML dependencies above already installed, run this from the `jev/` directory of the NeoHorse source repository:

```bash
cd /path/to/NeoHorse/jev
python -m pip install --no-deps ./package
```

`MODEL_DIR` still points to the complete model bundle downloaded from ModelScope. The source installation replaces the wheel installation step above.

### Model Composition

The unified multimodal backbone contains the language model, vision encoder, and merger (`Qwen3_5Model`, with `language_model` and `visual` components). Backbone weights use BF16; the separate pointer head uses FP32. Keep weights, tokenizer, configuration, and runtime from the same release together. Release provenance is recorded in [model_manifest.json](https://www.modelscope.cn/models/TokenRhythm/NeoHorse-Jev-4B/file/view/master/model_manifest.json).

## 2. Local Text Inference

The CLI can read the example request included in the model release:

```bash
CUDA_VISIBLE_DEVICES=0 neohorse-decision predict \
  --model-dir "$MODEL_DIR" --request "$MODEL_DIR/example_request.json"
```

Change the GPU index to match your allocation. The runtime does not schedule GPU resources across a cluster.

### Python Decision Examples

**Provide a state and get a yes/no probability, a selected candidate, or a rating.** The examples below use the same user message to demonstrate the three decision modes.

Load the model once, then reuse `engine` and `state`:

```python
import os

from neohorse_decision import DecisionEngine

engine = DecisionEngine(os.environ["MODEL_DIR"])
state = "I was charged twice for the same order. Please refund the extra charge today."
```

All output numbers below are illustrative, not measured results. Actual values depend on the model's predictions.

#### Noul: Is It True?

**Is the user requesting a refund?** Return the probability of "yes", `P(true)`.

```python
result = engine.predict({
    "state": state,
    "questions": {
        "refund": {
            "type": "noul",
            "instructions": "Is the user requesting a refund?",
        },
    },
})
print(result["answers"]["refund"]["noul"])
```

Illustrative output: `0.97` means the model assigns a 97% probability to the user requesting a refund. Your application can use this to enter a refund workflow.

#### Choice: Which One?

**Which team should handle this message?** Select from the candidates and return each candidate's probability.

```python
result = engine.predict({
    "state": state,
    "questions": {
        "team": {
            "type": "choice",
            "instructions": "Which team should handle this message?",
            "criteria": {
                "billing": "Billing, charges, or refunds",
                "technical": "Product failures or technical issues",
                "other": "Other matters",
            },
        },
    },
})
print(result["answers"]["team"]["choice"])
print(result["answers"]["team"]["probabilities"])
```

Illustrative output:

```text
billing
{'billing': 0.96, 'technical': 0.03, 'other': 0.01}
```

Read `billing` to route the message to the billing team.

#### Score: To What Degree?

**How urgent is the request?** Rate it against the levels you define. Levels start at `0`, and the result is their probability-weighted expected value.

```python
result = engine.predict({
    "state": state,
    "questions": {
        "urgency": {
            "type": "score",
            "instructions": "How soon does the user want this resolved?",
            "criteria": ["Can wait", "This week", "Today"],
        },
    },
})
print(result["answers"]["urgency"]["score"])
```

Illustrative output: `1.9` is close to level `2` ("Today"), which your application can use to raise the request's priority.

Save the four Python blocks above, in order, as `quickstart.py`, then run:

```bash
CUDA_VISIBLE_DEVICES=0 python quickstart.py
```

To make all three decisions in one text request, place `refund`, `team`, and `urgency` in the same `questions` dictionary. One request returns three answers. Set decision thresholds using data from your own tasks.


## 3. Start the HTTP Service

```bash
CUDA_VISIBLE_DEVICES=0 neohorse-decision serve --model-dir "$MODEL_DIR" --port 8080
```

The service binds to `127.0.0.1` by default. Check readiness from another terminal:

```bash
curl -sS http://127.0.0.1:8080/health
```

| Endpoint | Purpose |
| --- | --- |
| `POST /v1/decision` | Native decision API |
| `POST /v1/systemone` | Response structure containing `model`, `answers`, and `usage` |
| `GET /health` | Readiness status and `input_modalities` |

To enable authentication, set `NEOHORSE_API_KEY` in the service environment before starting it. Clients send `Authorization: Bearer <API_KEY>`. For external access, use a TLS gateway and limit concurrency and request body sizes. Only the endpoints and protocol scope described here are supported; `/v1/models` is not provided.

## 4. Text Requests

A request contains `model`, `state`, and `questions`. Each question has an application-defined key, a `type`, `instructions`, and `criteria` where required.

| Type | `criteria` | Meaning |
| --- | --- | --- |
| `noul` | Optional | Determine whether the condition is true |
| `choice` | Dictionary of candidate keys and descriptions | Select from the candidates |
| `score` | List of rating descriptions ordered from lowest to highest | Compute the rating distribution and expected value |

This request makes three decisions about the same user message:

```bash
curl -sS http://127.0.0.1:8080/v1/systemone \
  -H 'Content-Type: application/json' \
  -d '{
    "model": "NeoHorse-Jev-4B",
    "state": "I was charged twice for the same order. Please refund the extra charge today.",
    "questions": {
      "refund": {"type": "noul", "instructions": "Is the user requesting a refund?"},
      "team": {
        "type": "choice",
        "instructions": "Which team should handle this message?",
        "criteria": {"billing": "Billing, charges, or refunds", "technical": "Product failures or technical issues", "other": "Other matters"}
      },
      "urgency": {
        "type": "score",
        "instructions": "How soon does the user want this resolved?",
        "criteria": ["Can wait", "This week", "Today"]
      }
    }
  }'
```

This example assumes a local service without authentication. If authentication is enabled, add `-H "Authorization: Bearer $NEOHORSE_API_KEY"`.

Use `NeoHorse-Jev-4B` or `TokenRhythm/NeoHorse-Jev-4B` as the model name. Both HTTP endpoints also accept `neohorse-jev`, `NeoHorse-JEV-4B`, and `TokenRhythm/NeoHorse-JEV-4B`. Responses use the canonical name `NeoHorse-Jev-4B`.

## 5. Responses

Each question's result is available at `answers.<question_key>`:

| Type | Main fields |
| --- | --- |
| Choice | `type`, `choice`, `probabilities`, `confidence` |
| Noul | `type`, `noul`; the native API also retains yes/no `probabilities` |
| Score | `type`, `score`, `legend`, `probabilities`, `confidence` |

`noul` is the probability that the condition is true. Score levels are indexed from `0`; `score` is their probability-weighted expected value and can be fractional. `legend` maps level indices to their descriptions.

| Endpoint | Top-level structure and token counts |
| --- | --- |
| `/v1/decision` | `model`, `answers`, `input_tokens`; image requests also return `image_tokens` |
| `/v1/systemone` | `model`, `answers`, `usage`; token counts are in `usage.input_tokens` and `usage.output_tokens`, with `usage.image_tokens` for image requests |

Both HTTP endpoints use the same weights, encoding, and probabilities. The text Python interface, `DecisionEngine.predict`, does not currently return `confidence`.

`input_tokens` counts encoded input tokens. The shared state in a text request with multiple questions is counted once, so this is not the total number of tokens processed by the GPU after expanding the questions into separate branches. `output_tokens` is the response JSON's local tokenizer count; it does not indicate autoregressive generation. For image requests, `input_tokens` already includes image tokens and vision start/end markers. Do not add `image_tokens` again. Text responses do not include an `image_tokens` field.

### Understanding confidence

`confidence` is a local distribution statistic, not a calibrated probability of correctness:

- Choice: `(max(p) - 1/K) / (1 - 1/K)`, where `K` is the number of candidates. A single candidate returns `1`.
- Score: `1 - sum_i p_i * abs(i - argmax(p)) / (L - 1)`, where `L` is the number of rating levels.

Values are clamped to `[0, 1]`. Validate application thresholds on independent data. Both endpoints return `X-NeoHorse-Confidence: local-distribution-statistic-v1`. The System One-style endpoint also returns `X-NeoHorse-Usage: local-tokenizer-not-jev-billing`.

## 6. Image Requests

Both HTTP endpoints accept an optional top-level `image` field containing a base64 data URL for a PNG, JPEG, or WebP image. Each image request supports one static image and one Noul, Choice, or Score question. Omit `image` when no image is provided; do not send `null`. External URLs and server file paths are not accepted.

### Python Image Decisions

**Provide a page screenshot and a task goal to determine whether the task succeeded, what state the page is in, or how far the task has progressed.** The image and text jointly inform the decision, with Noul, Choice, or Score outputs.

This is a standalone image example. Save your screenshot as `screenshot.png`, then save the four Python blocks in this section, in order, as `multimodal_quickstart.py`. Load the model once and reuse the same image for all three calls, with **one question per request**. The output values below are illustrative, not measured results.

```python
import os

from PIL import Image
from neohorse_decision.vision import VisionDecisionEngine

vision_engine = VisionDecisionEngine(os.environ["MODEL_DIR"])
with Image.open("screenshot.png") as source:
    screenshot = source.convert("RGB")
state = "Goal: submit the form. Assess the current page screenshot."
```

#### Noul: Was the Form Submitted Successfully?

```python
result = vision_engine.predict({
    "model": "NeoHorse-Jev-4B",
    "state": state,
    "questions": {
        "submitted": {
            "type": "noul",
            "instructions": "Does the screenshot clearly show that the form was submitted successfully?",
        },
    },
}, screenshot)
print(result["answers"]["submitted"]["noul"])
```

For example, `0.97` means the model assigns a 97% probability to the screenshot showing a successful submission. Your workflow can use this to decide whether to move to the next step.

#### Choice: What State Is the Page In?

```python
result = vision_engine.predict({
    "model": "NeoHorse-Jev-4B",
    "state": state,
    "questions": {
        "page_status": {
            "type": "choice",
            "instructions": "Which page state does the screenshot show?",
            "criteria": {
                "success": "Submission succeeded",
                "error": "Submission failed or an error is shown",
                "processing": "Submission or loading is in progress",
                "unknown": "Cannot determine the submission status from the screenshot",
            },
        },
    },
}, screenshot)
print(result["answers"]["page_status"]["choice"])
print(result["answers"]["page_status"]["probabilities"])
```

For example, the result may be `success` alongside each candidate's probability. Route the next step according to the selected state.

#### Score: How Far Has the Task Progressed?

```python
result = vision_engine.predict({
    "model": "NeoHorse-Jev-4B",
    "state": state,
    "questions": {
        "completion": {
            "type": "score",
            "instructions": "How far has the form submission task progressed, based on the screenshot?",
            "criteria": ["Submission has not started", "Submission is in progress", "Submission clearly succeeded"],
        },
    },
}, screenshot)
print(result["answers"]["completion"]["score"])
```

For example, `1.9` is close to level `2` ("Submission clearly succeeded"). Actual results depend on the input image.

```bash
CUDA_VISIBLE_DEVICES=0 python multimodal_quickstart.py
```

Image requests currently support **one static image + text + one question**. The HTTP image formats are PNG, JPEG, and WebP. Multiple images, video, and audio are not supported.

For local image inference, run:

```bash
CUDA_VISIBLE_DEVICES=0 python "$MODEL_DIR/vision/example.py" \
  --model-dir "$MODEL_DIR" --image /path/to/image.png \
  --request "$MODEL_DIR/vision/example_request.json"
```

The Python interface is `neohorse_decision.vision.VisionDecisionEngine`, called as `engine.predict(request, pil_image)`. HTTP text and image requests share the same backbone, decision head, and GPU lock, without dynamic batching. The result is a structured decision distribution. Video and multiple-image interfaces are not provided. For the separate vLLM and SGLang adapters, including text and single-image requests, see the [backend deployment guide](infer/README.md).

### HTTP Image Requests

For the same question about whether the screenshot shows a successful submission, save this as `screenshot_request.json`:

```json
{
  "model": "NeoHorse-Jev-4B",
  "state": "Goal: submit the form. Assess the current page screenshot.",
  "questions": {
    "submitted": {
      "type": "noul",
      "instructions": "Does the screenshot clearly show that the form was submitted successfully?"
    }
  }
}
```

Once the service is running, use the bundled client to read the local screenshot and send the request:

```bash
python "$MODEL_DIR/vision/http_example.py" \
  --image screenshot.png \
  --request screenshot_request.json \
  --base-url http://127.0.0.1:8080 \
  --endpoint systemone
```

The client encodes the image as a base64 data URL in the top-level `image` field. In the response, `answers.submitted.noul` is the probability of a successful submission. Set `--endpoint` to `decision` to use the native endpoint. When authentication is enabled, the client reads the key from the `NEOHORSE_API_KEY` environment variable.

If `--request` is omitted, the bundled client asks for the image's dominant color by default.

## 7. Request Limits and Error Handling

| Item | Default limit |
| --- | --- |
| Text `state` | 2,048 tokens |
| Each question branch | 8,192 tokens |
| Questions per text request | 16 |
| Total tokens after expanding a text request into question branches | 32,768 |
| Text HTTP request body; JSON fields other than `image` in an image request | 1 MiB |
| Image HTTP request body | 8 MiB |
| Image file after base64 decoding | 4 MiB |
| Image pixel count | 4,194,304 |
| Minimum/maximum image preprocessing area budget | 65,536 / 1,048,576 pixels |
| Image tokens | 1,024 |
| Total encoded length of an image request | 12,288 tokens |
| Score levels on `/v1/systemone` | 2–10 |

Inputs that exceed these limits are rejected without silent truncation. These are deployment protection limits. Check task performance and GPU memory usage before changing them.

| HTTP status | Meaning and action |
| --- | --- |
| `401` | Authentication failed; check the Bearer token |
| `413` | The request body or text fields exceed size limits |
| `422` | Invalid JSON or fields, unknown model, or unsupported image format, dimensions, token count, multiple questions, animation, or other input constraint violations |
| `429` | The GPU worker for native `/v1/decision` is busy |
| `529` | The GPU worker for `/v1/systemone` is busy |

Busy responses include `Retry-After: 1`. Clients should back off and retry. There is no separate quota-based rate limiter; control high concurrency at the gateway and test it for your deployment.

## 8. Limitations

- **Decisions can be wrong.** Valid structure and normalized probabilities do not guarantee correct judgments. Missing evidence, candidate descriptions, candidate order, and domain shifts can all affect results.
- **Validate probabilities for your application.** NLL, Brier, and ECE calibration results have not been reported. Set thresholds on an independent dataset.
- **Scope claims to measured evidence.** Comprehensive evaluations of multilingual inputs, long inputs, and computational isolation between questions are not yet available. Multiple questions in one request do not imply a single shared forward pass.
- **Applications enforce execution constraints.** Tool permissions, business rules, and action validation remain the application's responsibility. The current materials do not provide latency, GPU memory, or cost comparisons under a common timing protocol.
