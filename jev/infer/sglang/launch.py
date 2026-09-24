"""Start unmodified SGLang with external prefix mapping and original tensors."""
import argparse
import os
from pathlib import Path
import subprocess
import sys
from weight_mapping import make_model_view

if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--bundle', required=True)
    p.add_argument('--port', type=int, default=30000)
    a = p.parse_args()
    env = os.environ.copy()
    env['SGLANG_EXTERNAL_MODEL_PACKAGE'] = 'sglang_loader'
    env['PYTHONPATH'] = str(Path(__file__).resolve().parent) + os.pathsep + env.get('PYTHONPATH', '')
    with make_model_view(a.bundle) as view:
        subprocess.run([sys.executable, '-m', 'sglang.launch_server',
            '--model-path', view, '--host', '127.0.0.1', '--port', str(a.port),
            '--dtype', 'bfloat16', '--context-length', '12289',
            '--chunked-prefill-size', '-1', '--max-prefill-tokens', '32768',
            '--max-running-requests', '128', '--mem-fraction-static', '0.4',
            '--disable-radix-cache', '--enable-return-hidden-states'], env=env, check=True)
