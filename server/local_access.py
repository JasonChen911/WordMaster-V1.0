"""Keep the desktop API accessible only from its own loopback origin."""
from urllib.parse import urlsplit
from ipaddress import ip_address

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import PlainTextResponse


_LOOPBACK = {"127.0.0.1", "localhost", "::1", "testserver"}


class LocalAccessMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, dev_origin: str = ""):
        super().__init__(app)
        self.dev_origin = dev_origin

    async def dispatch(self, request, call_next):
        host = urlsplit("//" + request.headers.get("host", "")).hostname
        if host not in _LOOPBACK:
            return PlainTextResponse("Forbidden host", status_code=403)
        peer = request.client.host if request.client else ""
        if peer != "testclient":
            try:
                if not ip_address(peer).is_loopback:
                    return PlainTextResponse("Forbidden peer", status_code=403)
            except ValueError:
                return PlainTextResponse("Forbidden peer", status_code=403)

        origin = request.headers.get("origin")
        if origin:
            parsed = urlsplit(origin)
            request_port = urlsplit("//" + request.headers["host"]).port
            if origin != self.dev_origin and (parsed.scheme != "http" or parsed.hostname != host or parsed.port != request_port):
                return PlainTextResponse("Forbidden origin", status_code=403)
        return await call_next(request)
