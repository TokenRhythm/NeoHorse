"""Multimodal config view of original weights; no tensor conversion."""
import json
from pathlib import Path
import tempfile


def make_model_view(bundle):
    root = Path(bundle).resolve()
    temporary = tempfile.TemporaryDirectory(prefix='jev-model-view-')
    view = Path(temporary.name)
    config = json.loads((root / 'backbone/config.json').read_text(encoding='utf-8'))
    config['architectures'] = ['Qwen3_5ForConditionalGeneration']
    config['tie_word_embeddings'] = True
    config['text_config']['tie_word_embeddings'] = True
    (view / 'config.json').write_text(json.dumps(config), encoding='utf-8')
    for path in (root / 'backbone').iterdir():
        if path.name.endswith('.safetensors') or path.name.endswith('.safetensors.index.json') or path.name == 'preprocessor_config.json':
            (view / path.name).symlink_to(path)
    for path in (root / 'tokenizer').iterdir():
        if path.is_file() and not (view / path.name).exists():
            (view / path.name).symlink_to(path)
    return temporary


def multimodal_weights(weights):
    """Forward the same tensor objects, with only a prefix change."""
    for name, tensor in weights:
        if not name.startswith(('language_model.', 'visual.')):
            raise ValueError('Unexpected unified-bundle weight: ' + name)
        yield 'model.' + name, tensor
