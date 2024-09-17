import asyncio
from datetime import date
from hashlib import md5

import requests as rq
from random import randbytes
from io import BytesIO

from requests.auth import HTTPBasicAuth


DOMAIN = 'https://cades-host/cades'
DOMAIN = 'https://cades-win7/cades'
DOMAIN = 'https://localhost:8000/cades'
DOMAIN = 'https://localhost:8080/cades'
URL = f'{DOMAIN}/sign'


class HTTPCadesAuth(HTTPBasicAuth):
    def digest(self):
        return md5(f"{self.username}:{self.password}".encode()).hexdigest()

    def __call__(self, request):
        request.headers['Authorization'] = "Cades %s" % self.digest()
        # request.headers['DiadocClientId'] = "priceplan-50855e2a-2640-4f6f-bae8-8ffff4722a4f"
        request.headers['DiadocClientId'] = "sdfsdfsdfsdfsdf"
        return request


def test():
    ss = rq.session()
    ss.auth = HTTPCadesAuth('admin', 'admin123')
    ss.verify = False
    res = ss.get(f"{DOMAIN}/status")
    res = ss.get(f"{DOMAIN}/diadoc")
    res = ss.get(f"{DOMAIN}/client-id")
    res = ss.get(f"{DOMAIN}/diadoc-url")
    res = ss.post(f"{DOMAIN}/client-id", json={'value': "test"})
    res = ss.post(f"{DOMAIN}/diadoc-url", json={'url': "http://diadoc.service.ru"})
    res = ss.get(f"{DOMAIN}/documents/cd1e1d84-3c79-4dd1-9300-f153f5c1832b/status")

    print(res)
    print(res.content)
    print(res.json())

def send():
    ss = rq.session()
    ss.auth = HTTPCadesAuth('admin', 'admin123')
    ss.verify = False
    res = ss.post(f"{DOMAIN}/senddoc", json={
        "name": "test.pdf",
        "number": "123123",
        "date": date.today().isoformat(),
        "amount": 1000.1,
        "data": "sdfnskjdfnskjdnfksajnfwenfoweinfsodjfsoaidjfoasijdfosijdfoasijdfoi323j4482434294ref"
    })
    res
    res.content


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

