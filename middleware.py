from sqlalchemy.util import md5_hex
from starlette.middleware import Middleware
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from config import Config


class IPAddrMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        addr = request.client.host

        config = Config()

        if len(config.whitelist) > 0 and addr not in config.whitelist:
            return Response(f'{addr} NOT IN WHITELIST!', status_code=403)
        return await call_next(request)


class AuthMiddleware(BaseHTTPMiddleware):

    AUTH_METHOD = 'Cades'
    DEFAULT_TOKEN = "q1w2e3r4t5y6u7i8o9p0"

    UNDEFENDED_URLS = (
        '/docs',
        '/openapi.json',
    )

    def make_digest(self, username, password):
        s = f"{username}:{password}"
        return md5_hex(s)

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        config = Config()
        if config.auth_disabled:
            return await call_next(request)

        if request.url.path.startswith(self.UNDEFENDED_URLS):
            return await call_next(request)

        if pretoken := request.headers.get('authorization'):
            method, token = pretoken.split(' ')
            if method == self.AUTH_METHOD:
                if token == self.DEFAULT_TOKEN:
                    return await call_next(request)
                tokens = (md5_hex(f"{u}:{p}") for u,p in config.users.items())
                if token in tokens:
                    return await call_next(request)

        return Response("NOT AUTHORIZED!", status_code=403)


middleware = [
    Middleware(IPAddrMiddleware),
    # Middleware(AuthenticationMiddleware, backend=None)
    Middleware(AuthMiddleware)
]
