from sqlalchemy import exists, select
from sqlalchemy.util import md5_hex
from starlette.middleware import Middleware
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from db import ASession, IPAddress, User


# from sqlalchemy.ext.asyncio.


class IPAddrMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        addr = request.client.host
        ss = ASession()
        ext = (await ss.execute(exists(IPAddress).where(IPAddress.addr==addr).select())).scalar()

        if ext:
            response = await call_next(request)
        else:
            response = Response("DENIED BY IP ADDRESS", status_code=403)

        return response


class AuthMiddleware(BaseHTTPMiddleware):

    AUTH_METHOD = 'Cades'

    def make_digest(self, username, password):
        s = f"{username}:{password}"
        return md5_hex(s)

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:

        print(request.headers)

        if pretoken := request.headers.get('authorization'):
            method, token = pretoken.split(' ')
            if method == self.AUTH_METHOD:
                ss = ASession()
                users = await ss.execute(select(User))

                for (u,) in users:
                    if self.make_digest(u.username, u.password) == token:
                        return await call_next(request)

        return Response("NOT AUTHORIZED!", status_code=403)


middleware = [
    Middleware(IPAddrMiddleware),
    # Middleware(AuthenticationMiddleware, backend=None)
    Middleware(AuthMiddleware)
]
