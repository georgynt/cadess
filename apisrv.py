import asyncio
import logging
import multiprocessing
import os
from asyncio import CancelledError
from os.path import join

from logger import info, logger
from pathlib import Path

import uvicorn
from fastapi import FastAPI

from config import Config
from const import SRV_PORT
from middleware import middleware
from router import CadesLogic, router

KEYFILE_NAME = './certs/server.key'
CERTFILE_NAME = './certs/server.crt'



class UvicornServer(uvicorn.Server):
    # server: uvicorn.Server
    uvconf: uvicorn.Config
    app: FastAPI

    def __get_file(self, name):
        config = Config()
        if filename := config.settings.get(name):
            pass
        else:
            cfp = Path(__file__).parent.resolve()
            if name == 'keyfile':
                filename = str(cfp / KEYFILE_NAME)
            elif name == 'certfile':
                filename = str(cfp / CERTFILE_NAME)
            else:
                filename = str(cfp / name)

        if not Path(filename).exists():
            raise FileNotFoundError(f"{filename} NOT FOUND!")
        return filename

    keyfile = property(lambda x: x.__get_file('keyfile'))
    certfile = property(lambda x: x.__get_file('certfile'))

    def __init__(self):
        Config()
        CadesLogic()

        self.app = FastAPI(middleware=middleware)
        self.app.include_router(router)
        self.uvconf = uvicorn.Config(self.app,
                                     host="0.0.0.0",
                                     port=SRV_PORT,
                                     use_colors=False,
                                     ssl_keyfile=self.keyfile,
                                     ssl_certfile=self.certfile)
        info("UvicornServer created")
        super().__init__(self.uvconf)

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
    logger.addHandler(logging.FileHandler(join(os.getcwd(), 'cades.log')))
    us = UvicornServer()
    try:
        us.run()
    except CancelledError as e:
        logger.info("stop")
    except KeyboardInterrupt as e:
        logger.info("stop")

    #try:
    #    while us.is_alive():
    #        us.join(10)
    #except KeyboardInterrupt as e:
    #    print('stop')
    #    us.stop()
    #    us.join()
