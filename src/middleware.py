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
    DIADOC_CLIENT_ID = 'DiadocClientId'

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

        if self.DIADOC_CLIENT_ID in request.headers and \
                (client_id := request.headers.get(self.DIADOC_CLIENT_ID)):
            if config.client_id != client_id:
                config.client_id = client_id

        if pretoken := request.headers.get('authorization'):
            method, token = pretoken.split(' ')
            if method == self.AUTH_METHOD:
                tokens = (md5_hex(f"{u}:{p}") for u,p in config.users.items())
                if token in tokens:
                    return await call_next(request)
                tokens = config.users.values()
                if token in tokens:
                    return await call_next(request)

        return Response("NOT AUTHORIZED!", status_code=403)
        # return await call_next(request)


middleware = [
    Middleware(IPAddrMiddleware),
    # Middleware(AuthenticationMiddleware, backend=None)
    Middleware(AuthMiddleware)
]
