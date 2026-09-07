import argparse
import json

import requests


tools = [
    {
        "type": "function",
        "function": {
            "name": "get_current_weather",
            "description": "Get the current weather for a specified city.",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "Name of the city.",
                    }
                },
                "required": ["city"],
            },
        },
    }
]


def main():
    parser = argparse.ArgumentParser(
        description="Run a tool-calling example with a deployed model."
    )
    parser.add_argument(
        "--url",
        required=True,
        help=(
            "Base URL of the deployed model server, e.g. "
            "http://127.0.0.1:8000."
        ),
    )
    parser.add_argument(
        "--model",
        required=True,
        help=(
            "Name of the deployed model, e.g. neohorse-1-4B. "
            "It must match the SGLang --served-model-name value."
        ),
    )
    args = parser.parse_args()

    base_url = args.url.rstrip("/")
    if not base_url.startswith(("http://", "https://")):
        base_url = f"http://{base_url}"

    if base_url.endswith("/v1"):
        url = f"{base_url}/chat/completions"
    else:
        url = f"{base_url}/v1/chat/completions"

    payload = {
        "model": args.model,
        "messages": [
            {
                "role": "user",
                "content": "北京现在天气怎么样？",
            }
        ],
        "tools": tools,
        "tool_choice": "auto",
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

    message = response.json()["choices"][0]["message"]

    if message.get("tool_calls"):
        print(json.dumps(message["tool_calls"], ensure_ascii=False, indent=2))
    else:
        print(message.get("content", ""))


if __name__ == "__main__":
    main()
