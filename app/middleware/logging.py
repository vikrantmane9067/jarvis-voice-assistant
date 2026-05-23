from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        print(f"[REQUEST] {request.method} {request.url}")
        response = await call_next(request)
        print(f"[RESPONSE] {request.method} {request.url} -> {response.status_code}")
        return response
