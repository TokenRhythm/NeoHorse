"""Request backbone features from the persistent vLLM service, then run CPU head."""
import argparse
import json
from pathlib import Path
import requests
from head import CPUHead


class VLLMCPU:
    def __init__(self, bundle, url='http://127.0.0.1:30000', timeout=1800):
        self.head = CPUHead(bundle)
        self.url, self.timeout = url.rstrip('/'), timeout

    def predict(self, request):
        rows = self.head.prepare(request)
        payload = {
            'model': 'NeoHorse-Jev-4B', 'input': [row['ids'] for row in rows],
            'task': 'token_embed', 'use_activation': False,
            'encoding_format': 'float', 'add_special_tokens': False}
        if 'image' in rows[0]:
            row = rows[0]
            del payload['input']
            payload['messages'] = [{'role': 'user', 'content': [
                {'type': 'text', 'text': row['before']},
                {'type': 'image_url', 'image_url': {'url': row['image']}},
                {'type': 'text', 'text': row['after']}]}]
            payload['add_generation_prompt'] = False
        response = requests.post(self.url + '/pooling', json=payload, timeout=self.timeout)
        response.raise_for_status()
        outputs = response.json()['data']
        if len(outputs) != len(rows) or sorted(item['index'] for item in outputs) != list(range(len(rows))):
            raise ValueError('Unexpected pooling response indices')
        outputs = sorted(outputs, key=lambda item: item['index'])
        return self.head.result(rows, [item['data'] for item in outputs])


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--bundle', required=True)
    parser.add_argument('--url', default='http://127.0.0.1:30000')
    parser.add_argument('--request', required=True)
    args = parser.parse_args()
    print(json.dumps(VLLMCPU(args.bundle, args.url).predict(
        json.loads(Path(args.request).read_text(encoding='utf-8'))), ensure_ascii=False, indent=2))
