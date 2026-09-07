import argparse

import requests


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--url",
        required=True,
        help=(
            "Base URL of the deployed model server, e.g. "
            "http://127.0.0.1:8000. The script sends requests "
            "to the /v1/chat/completions endpoint."
        ),
    )
    parser.add_argument(
        "--model",
        required=True,
        help=(
            "Name of the deployed model, e.g. neohorse-1-4B. "
            "It must match the value specified by "
            "--served-model-name when launching SGLang."
        ),
    )
    args = parser.parse_args()

    base_url = args.url.rstrip("/")
    if not base_url.startswith(("http://", "https://")):
        base_url = f"http://{base_url}"

    url = f"{base_url}/v1/chat/completions"

    payload = {
        "model": args.model,
        "messages": [
            {
                "role": "user",
                "content": "你是谁？",
            }
        ],
        "max_tokens": 4096,
        "chat_template_kwargs": {
            "enable_thinking": True,
        },
        "stream": False,
    }

    response = requests.post(
        url,
        headers={"Content-Type": "application/json"},
        json=payload,
        timeout=500,
    )
    response.raise_for_status()

    result = response.json()
    print(result["choices"][0]["message"]["content"])


if __name__ == "__main__":
    main()
