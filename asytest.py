import asyncio
import requests as rq
from random import randbytes
from io import BytesIO


URL = 'http://cades-host:8000/cades/sign'

async def makerequest():
    def fetch():
        data = randbytes(1000)
        bio = BytesIO(data)
        res = rq.post(URL, files={'file': bio, 'body': 'somefilename.txt'})
        return res.json()
    return await asyncio.to_thread(fetch)

async def dowork():
    for i in range(100):
        j = await makerequest()
        print(j)

asyncio.run(dowork())

