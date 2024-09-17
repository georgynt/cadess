import asyncio
import logging
import multiprocessing
import sys
from asyncio import CancelledError
from pathlib import Path

import uvicorn
from fastapi import FastAPI

from config import Config
from const import SRV_PORT
from db import create_tables
from logger import formatter, info, logger
from middleware import middleware
from router import CadesLogic, router
from sender import handle_documents, init_repeat_task


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
        self.app.on_event("startup")(init_repeat_task)
        self.uvconf = uvicorn.Config(self.app,
                                     host="0.0.0.0",
                                     port=SRV_PORT,
                                     use_colors=False,
                                     ssl_keyfile=self.keyfile,
                                     ssl_certfile=self.certfile)
        info("UvicornServer created")
        asyncio.run(create_tables())
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
    stm_h = logging.StreamHandler(sys.stdout)
    stm_h.setFormatter(formatter)
    logger.addHandler(stm_h)

    # logger.addHandler(logging.FileHandler(join(os.getcwd(), 'cades.log'))) наверное это не надо
    us = UvicornServer()
    try:
        us.run()
    except CancelledError as e:
        logger.info("stop")
    except KeyboardInterrupt as e:
        logger.info("stop")
