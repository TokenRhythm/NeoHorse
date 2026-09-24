import argparse
import json
import os
from pathlib import Path
from .engine import DecisionEngine


def main():
    p = argparse.ArgumentParser()
    p.add_argument('command', choices=['predict', 'serve'])
    p.add_argument('--model-dir', required=True)
    p.add_argument('--device', default='cuda')
    p.add_argument('--request')
    p.add_argument('--host', default='127.0.0.1')
    p.add_argument('--port', default=8080, type=int)
    a = p.parse_args()
    if a.command == 'predict' and not a.request:
        p.error('predict requires --request')
    engine = DecisionEngine(a.model_dir, a.device)
    if a.command == 'predict':
        print(json.dumps(engine.predict(json.loads(Path(a.request).read_text())), ensure_ascii=False, indent=2))
    else:
        import uvicorn
        from .server import create_app
        uvicorn.run(create_app(engine, os.environ.get('NEOHORSE_API_KEY')), host=a.host, port=a.port, workers=1)
