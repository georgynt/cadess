import asyncio
import multiprocessing
from pathlib import Path

import uvicorn
from fastapi import FastAPI

from const import SRV_PORT
from middleware import middleware
from router import router

KEYFILE_NAME = './certs/server.key'
CERTFILE_NAME = './certs/server.crt'

class UvicornServer(uvicorn.Server):
    # server: uvicorn.Server
    config: uvicorn.Config
    app: FastAPI

    def __init__(self):
        # with (open(KEYFILE_NAME, 'r') as fk, open(CERTFILE_NAME, 'r') as fc):
        #     keyfile = fk.read()
        #     certfile = fc.read()

        if not Path(KEYFILE_NAME).exists():
            raise FileNotFoundError(KEYFILE_NAME)
        if not Path(CERTFILE_NAME).exists():
            raise FileNotFoundError(CERTFILE_NAME)


        self.app = FastAPI(middleware=middleware)
        self.app.include_router(router)
        self.config = uvicorn.Config(self.app,
                                     host="0.0.0.0",
                                     port=8080,
                                     ssl_keyfile=KEYFILE_NAME,
                                     ssl_certfile=CERTFILE_NAME)
        super().__init__(self.config)

    def stop(self):
        self.force_exit = True
        self.should_exit = True


class ForkService(multiprocessing.Process):

    def run(self):
        us = UvicornServer()
        us.run()

    def start(self):
        from db import create_tables
        asyncio.run(create_tables())

        super().start()

    def stop(self):
        self.terminate()


if __name__ == '__main__':
    us = ForkService()
    us.start()
    try:
        while us.is_alive():
            us.join(10)
    except KeyboardInterrupt as e:
        print('stop')
        us.stop()
        us.join()
