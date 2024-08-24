# import sys

import servicemanager  # Simple setup and logging
import win32service  # Events
import win32serviceutil  # ServiceFramework and commandline helper
import socket
import win32event
import os, time, sys

from apisrv import ForkService


class CadesWinService(win32serviceutil.ServiceFramework):
    _svc_name_ = 'CadesService'
    _svc_display_name_ = 'CadesService'
    _svc_description_ = 'API Service for CAdES Subscription documents'

    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)
        socket.setdefaulttimeout(120)

    @property
    def is_alive(self) -> bool:
        if hasattr(self,'uvisrv'):
            return self.uvisrv.is_alive()
        return False

    def SvcStop(self):
        """Stop the service"""
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        self.uvisrv.stop()
        self.ReportServiceStatus(win32service.SERVICE_STOPPED)

    def SvcDoRun(self):
        """Start the service; does not return until stopped"""
        try:
            self.ReportServiceStatus(win32service.SERVICE_START_PENDING)
            self.uvisrv = ForkService()
            self.ReportServiceStatus(win32service.SERVICE_RUNNING)
            # Run the service
            self.uvisrv.start()
            # while self.uvisrv.is_alive():
            #     self.uvisrv.join(10)
        except Exception as e:
            print(e)
            self.ReportServiceStatus(win32service.SERVICE_ERROR_CRITICAL)


def init():
    print(sys.argv)

    if len(sys.argv) == 1:
        servicemanager.Initialize()
        servicemanager.PrepareToHostSingle(CadesWinService)
        servicemanager.StartServiceCtrlDispatcher()
    else:
    # if True:
        win32serviceutil.HandleCommandLine(CadesWinService)


if __name__ == '__main__':
    init()
