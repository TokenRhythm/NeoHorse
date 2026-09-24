"""Unmodified SGLang HTTP backbone -> external CPU pointer head."""
import argparse
import json
from pathlib import Path
import requests
from head import CPUHead


class SGLangCPU:
    def __init__(self, bundle, url='http://127.0.0.1:30000', timeout=1800):
        self.head = CPUHead(bundle)
        self.url, self.timeout = url.rstrip('/'), timeout

    def predict(self, request):
        rows = self.head.prepare(request)
        states = []
        for row in rows:
            payload = {
                'input_ids': row.get('prompt_ids', row['ids']),
                'return_hidden_states': True, 'stream': False,
                'sampling_params': {'temperature': 0, 'max_new_tokens': 1}}
            if 'image' in row:
                payload['image_data'] = [row['image']]
            response = requests.post(self.url + '/generate', json=payload, timeout=self.timeout)
            response.raise_for_status()
            result = response.json()
            if isinstance(result, list):
                if len(result) != 1:
                    raise ValueError('Unexpected backend batch size')
                result = result[0]
            states.append(result['meta_info']['hidden_states'])
        return self.head.result(rows, states)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--bundle', required=True)
    parser.add_argument('--url', default='http://127.0.0.1:30000')
    parser.add_argument('--request', required=True)
    args = parser.parse_args()
    print(json.dumps(SGLangCPU(args.bundle, args.url).predict(
        json.loads(Path(args.request).read_text(encoding='utf-8'))), ensure_ascii=False, indent=2))
