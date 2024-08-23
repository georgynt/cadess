import asyncio
from hashlib import md5

import requests as rq
from random import randbytes
from io import BytesIO

from requests.auth import HTTPBasicAuth


DOMAIN = 'https://cades-host:8000/cades'
DOMAIN = 'https://localhost:8000/cades'
URL = f'{DOMAIN}/sign'


class HTTPCadesAuth(HTTPBasicAuth):
    def digest(self):
        return md5(f"{self.username}:{self.password}".encode()).hexdigest()

    def __call__(self, request):
        request.headers['Authorization'] = "Cades %s" % self.digest()
        return request


def test():
    ss = rq.session()
    ss.auth = HTTPCadesAuth('admin', 'admin123')
    ss.verify = False
    res = ss.get(f"{DOMAIN}/status")
    print(res)


async def makerequest():
    def fetch():
        data = randbytes(1000)
        bio = BytesIO(data)
        res = ss.post(URL, files={'file': bio, 'body': 'somefilename.txt'})
        return res.json()
    return await asyncio.to_thread(fetch)

async def dowork():
    for i in range(100):
        j = await makerequest()
        print(j)

asyncio.run(dowork())

