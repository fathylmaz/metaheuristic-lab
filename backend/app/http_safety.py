"""Bound the educational API request size and set defensive response headers.

This is a local research application, not a multi-tenant authenticated service.
The request limit protects memory against accidental oversized JSON uploads; it
is not a substitute for rate limiting or an internet-facing reverse proxy.
"""
from __future__ import annotations

from starlette.datastructures import Headers, MutableHeaders
from starlette.responses import JSONResponse

MAX_API_JSON_BYTES = 1024 * 1024  # 1 MiB: well above all supported request schemas


class ApiSafetyMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope['type'] != 'http':
            await self.app(scope, receive, send)
            return

        path = scope.get('path', '')
        method = scope.get('method', '')
        needs_limit = path.startswith('/api/') and method == 'POST'

        async def safe_send(message):
            if message['type'] == 'http.response.start':
                headers = MutableHeaders(scope=message)
                headers['X-Content-Type-Options'] = 'nosniff'
                headers['Referrer-Policy'] = 'no-referrer'
                headers['X-Frame-Options'] = 'DENY'
                if path.startswith('/api/'):
                    headers['Cache-Control'] = 'no-store'
            await send(message)

        if not needs_limit:
            await self.app(scope, receive, safe_send)
            return

        try:
            length = int(Headers(scope=scope).get('content-length', '0'))
        except ValueError:
            length = 0
        if length > MAX_API_JSON_BYTES:
            await JSONResponse(status_code=413, content={'detail': 'İstek gövdesi 1 MiB sınırını aşıyor'})(scope, receive, safe_send)
            return

        # Enforce the limit even for chunked requests without Content-Length.
        chunks = []
        count = 0
        while True:
            message = await receive()
            if message['type'] == 'http.disconnect':
                return
            if message['type'] != 'http.request':
                continue
            chunk = message.get('body', b'')
            count += len(chunk)
            if count > MAX_API_JSON_BYTES:
                await JSONResponse(status_code=413, content={'detail': 'İstek gövdesi 1 MiB sınırını aşıyor'})(scope, receive, safe_send)
                return
            chunks.append(chunk)
            if not message.get('more_body', False):
                break
        body = b''.join(chunks)
        replayed = False

        async def replay():
            nonlocal replayed
            if not replayed:
                replayed = True
                return {'type': 'http.request', 'body': body, 'more_body': False}
            return {'type': 'http.disconnect'}

        await self.app(scope, replay, safe_send)
