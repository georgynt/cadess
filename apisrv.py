import multiprocessing

import uvicorn
from fastapi import FastAPI

from const import SRV_PORT
from router import router


class UvicornServer(uvicorn.Server):
    # server: uvicorn.Server
    config: uvicorn.Config
    app: FastAPI

    def __init__(self):
        self.app = FastAPI()
        self.app.include_router(router)
        self.config = uvicorn.Config(self.app, host="0.0.0.0", port=SRV_PORT)
        super().__init__(self.config)

    def stop(self):
        self.force_exit = True
        self.should_exit = True


class ForkService(multiprocessing.Process):

    def run(self):
        us = UvicornServer()
        us.run()

    def stop(self):
        # self.us.stop()
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


