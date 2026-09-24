import hmac
import json
import threading
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from starlette.concurrency import run_in_threadpool
from . import __version__
from .engine import BusyError
from .systemone import validate_request, format_response, with_confidence
from .image_input import decode_image


def create_app(engine, api_key=None, *, vision_engine=None):
    app = FastAPI(title='NeoHorse Decision', version=__version__)
    if vision_engine is None and hasattr(getattr(engine, 'model', None), 'multimodal'):
        from .vision import VisionDecisionEngine
        vision_engine = VisionDecisionEngine(engine.model_dir, engine.device, text_engine=engine)
    image_lock = threading.Lock()

    def image_predict(value, encoded):
        if not image_lock.acquire(blocking=False):
            raise BusyError('Image worker busy')
        try:
            image = decode_image(encoded)
            try:
                return vision_engine.predict(value, image)
            finally:
                image.close()
        finally:
            image_lock.release()

    @app.get('/health')
    def health():
        return {'status': 'ready', 'model': engine.model_id,
                'input_modalities': ['text', 'image'] if vision_engine is not None else ['text']}

    async def handle(request: Request, systemone=False):
        if api_key and not hmac.compare_digest(request.headers.get('authorization', ''), 'Bearer ' + api_key):
            raise HTTPException(401, 'Invalid bearer token')
        body = bytearray()
        async for chunk in request.stream():
            body.extend(chunk)
            if len(body) > 8 * 1024 * 1024:
                raise HTTPException(413, 'Request exceeds 8 MiB')
        try:
            try:
                value = json.loads(body)
            except (ValueError, UnicodeError, RecursionError):
                if len(body) > 1024 * 1024:
                    raise HTTPException(413, 'Text request exceeds 1 MiB')
                raise ValueError('Invalid JSON')
            if not isinstance(value, dict):
                raise ValueError('Request must be an object')
            if any(k in value for k in ('images', 'image_url', 'image_base64', 'video')):
                raise ValueError('Use the single top-level image data URL field')
            has_image = 'image' in value
            encoded = value.pop('image', None)
            if (not has_image and len(body) > 1024 * 1024) or len(json.dumps(value, ensure_ascii=False).encode()) > 1024 * 1024:
                raise HTTPException(413, 'Text request fields exceed 1 MiB')
            if has_image:
                if vision_engine is None:
                    raise ValueError('This model has no enabled vision adapter')
                if not isinstance(value.get('questions'), dict) or len(value['questions']) != 1:
                    raise ValueError('Image requests require exactly one question')
            if systemone:
                value = validate_request(value)
            if has_image:
                result = await run_in_threadpool(image_predict, value, encoded)
            else:
                result = await run_in_threadpool(engine.predict, value)
            if systemone:
                result = format_response(result, engine.tokenizer)
                return JSONResponse(result, headers={
                    'X-NeoHorse-Confidence': 'local-distribution-statistic-v1',
                    'X-NeoHorse-Usage': 'local-tokenizer-not-jev-billing'})
            return JSONResponse(with_confidence(result), headers={
                'X-NeoHorse-Confidence': 'local-distribution-statistic-v1'})
        except BusyError:
            return JSONResponse({'detail': 'Model busy; retry later'}, status_code=529 if systemone else 429, headers={'Retry-After': '1'})
        except (ValueError, TypeError, ValidationError) as e:
            raise HTTPException(422, str(e)) from e
    @app.post('/v1/decision')
    async def decision(request: Request):
        return await handle(request)

    @app.post('/v1/systemone')
    async def systemone(request: Request):
        return await handle(request, systemone=True)
    return app
