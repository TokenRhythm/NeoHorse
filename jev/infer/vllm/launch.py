"""Start the native vllm serve frontend with an external weight loader."""
import argparse
import json
import os
from pathlib import Path
import sys
from weight_mapping import make_model_view


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--bundle', required=True)
    parser.add_argument('--port', type=int, default=30000)
    args = parser.parse_args()
    os.environ['VLLM_WORKER_MULTIPROC_METHOD'] = 'spawn'
    os.environ['PYTHONPATH'] = str(Path(__file__).resolve().parent) + os.pathsep + os.environ.get('PYTHONPATH', '')
    from vllm_loader import register
    register()
    from vllm.entrypoints.cli.main import main
    with make_model_view(args.bundle) as view:
        sys.argv = ['vllm', 'serve', view,
            '--served-model-name', 'NeoHorse-Jev-4B',
            '--host', '127.0.0.1', '--port', str(args.port),
            '--runner', 'pooling', '--convert', 'embed',
            '--chat-template', str(Path(__file__).with_name('decision.jinja')),
            '--chat-template-content-format', 'openai',
            '--limit-mm-per-prompt', '{"image":1,"video":0}',
            '--skip-mm-profiling',
            '--dtype', 'bfloat16', '--max-model-len', '12288',
            '--max-num-batched-tokens', '32768', '--max-num-seqs', '128',
            '--gpu-memory-utilization', '0.4', '--enforce-eager',
            '--no-enable-chunked-prefill', '--no-enable-prefix-caching',
            '--gdn-prefill-backend', 'triton',
            '--worker-extension-cls', 'vllm_worker.RegisterLoader',
            '--pooler-config', json.dumps({'task': 'token_embed',
                'tok_pooling_type': 'ALL', 'use_activation': False})]
        main()
