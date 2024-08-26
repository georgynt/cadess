# import sys
import logging
from asyncio import CancelledError

import servicemanager  # Simple setup and logging
import win32service  # Events
import win32serviceutil  # ServiceFramework and commandline helper
import socket
import win32event
import os, time, sys

from apisrv import ForkService, UvicornServer
from logger import formatter, logger


def win_excepthook(excType, excValue, traceback, logger=logger):
    logger.error("Logging an uncaught exception",
                 exc_info=(excType, excValue, traceback))

sys.excepthook = win_excepthook


class CadesWinService(win32serviceutil.ServiceFramework):
    _svc_name_ = 'CasCAdES'
    _svc_display_name_ = 'CasCAdES'
    _svc_description_ = 'API Service for CAdES sign documents'

    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)
        socket.setdefaulttimeout(120)

    def SvcStop(self):
        """Stop the service"""
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.hWaitStop)
        self.uvisrv.stop()
        self.ReportServiceStatus(win32service.SERVICE_STOPPED)

    # def SvcDoRun(self):
    #     """Start the service; does not return until stopped"""
    #     try:
    #         self.ReportServiceStatus(win32service.SERVICE_START_PENDING)
    #         self.uvisrv = ForkService()
    #         self.ReportServiceStatus(win32service.SERVICE_RUNNING)
    #         # Run the service
    #         self.uvisrv.start()
    #         # while self.uvisrv.is_alive():
    #         #     self.uvisrv.join(10)
    #         win32event.WaitForSingleObject(self.hWaitStop, win32event.INFINITE)
    #     except Exception as e:
    #         print(e)
    #         self.ReportServiceStatus(win32service.SERVICE_ERROR_CRITICAL)
    def SvcDoRun(self):
        logger.debug('SvcDoRun')
        try:
            servicemanager.LogMsg(servicemanager.EVENTLOG_INFORMATION_TYPE,
                                  servicemanager.PYS_SERVICE_STARTED,
                                  (self._svc_name_, ''))
            self.ReportServiceStatus(win32service.SERVICE_START_PENDING)
            self.uvisrv = UvicornServer()
            self.ReportServiceStatus(win32service.SERVICE_RUNNING)
            self.uvisrv.run()
            win32event.WaitForSingleObject(self.hWaitStop, win32event.INFINITE)
        except Exception as e:
            logger.error(f"{e} (in SvcDoRun)")
            self.ReportServiceStatus(win32service.SERVICE_ERROR_CRITICAL)


def init():
    file_h = logging.FileHandler(r'C:\cades_sm.log' if len(sys.argv) == 1 else r'C:\cades_wsu.log')
    file_h.setFormatter(formatter)
    logger.addHandler(file_h)
    logger.debug(sys.argv)

    try:
        if len(sys.argv) == 1:
            servicemanager.Initialize()
            servicemanager.PrepareToHostSingle(CadesWinService)
            servicemanager.StartServiceCtrlDispatcher()
        else:
            win32serviceutil.HandleCommandLine(CadesWinService)
    except CancelledError as e:
        logger.info("stop")
        exit(0)
    except KeyboardInterrupt as ki:
        logger.info("stop")
        exit(0)
    except Exception as e:
        logger.error(e, exc_info=e, stack_info=True)



if __name__ == '__main__':
    init()
