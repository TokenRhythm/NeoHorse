"""System One wire adapter; not official Jev calibration or billing."""
import json
from ._vendor.schema import SystemOneRequest, choice_confidence, score_confidence

MODEL_ID = 'NeoHorse-Jev-4B'
MODEL_NAMES = {MODEL_ID, 'TokenRhythm/' + MODEL_ID, 'neohorse-jev',
               'NeoHorse-JEV-4B', 'TokenRhythm/NeoHorse-JEV-4B'}

def validate_request(value):
    if not isinstance(value.get('model'), str) or value['model'] not in MODEL_NAMES:
        raise ValueError('model is required; use NeoHorse-Jev-4B (not a Jev model alias)')
    if not isinstance(value.get('state'), (str, dict, list)):
        raise ValueError('state must be string, object or array')
    req = SystemOneRequest(**{**value, 'model': 'neohorse-jev'})
    def description(v):
        return v is None or isinstance(v, (str, dict, list))
    for q in req.questions.values():
        if not description(q.instructions):
            raise ValueError('instructions must be string, object, array or null')
        if q.type == 'score':
            if not 2 <= len(q.criteria) <= 10:
                raise ValueError('System One Score requires 2..10 levels')
            values = q.criteria
        elif q.type == 'noul':
            if q.criteria and not set(q.criteria) <= {'true', 'false'}:
                raise ValueError('Noul criteria keys must be true or false')
            values = (q.criteria or {}).values()
        else:
            values = q.criteria.values()
        if any(not description(v) for v in values):
            raise ValueError('criteria descriptions must be string, object, array or null')
    return req.model_dump()

def with_confidence(result):
    """Add the same local confidence statistic without removing native fields."""
    answers = {}
    for name, answer in result['answers'].items():
        a = dict(answer)
        if a['type'] in ('choice', 'score'):
            p = list(a['probabilities'].values())
            confidence = choice_confidence(p) if a['type'] == 'choice' else score_confidence(p)
            a['confidence'] = min(1.0, max(0.0, confidence))
        answers[name] = a
    return {**result, 'answers': answers}

def format_response(result, tokenizer):
    answers = with_confidence(result)['answers']
    for name, a in answers.items():
        if a['type'] == 'noul':
            answers[name] = {'type': 'noul', 'noul': a['noul']}
    output_tokens = len(tokenizer(json.dumps(answers, ensure_ascii=False, separators=(',', ':')),
                                  add_special_tokens=False).input_ids)
    usage = {'input_tokens': result['input_tokens'], 'output_tokens': output_tokens}
    if 'image_tokens' in result:
        usage['image_tokens'] = result['image_tokens']
    return {'model': MODEL_ID, 'answers': answers, 'usage': usage}
