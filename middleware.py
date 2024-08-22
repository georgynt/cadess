from sqlalchemy import select, exists
# from sqlalchemy.ext.asyncio.

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response


from db import ASession, IPAddress


class IPAddrMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        addr = request.client.host

        print(addr)

        ss = ASession()
        ext = (await ss.execute(exists(IPAddress).where(IPAddress.c.addr==addr).select())).scalar()

        if ext:
            response = call_next(request)
        else:
            response = Response("DENIED", status_code=403)

        return response


class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        token = request.auth

        print(token)

        return call_next(request)
