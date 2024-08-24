import sys
from enum import Enum


if sys.platform == 'win32':
    SRV_PORT = 443
else:
    SRV_PORT = 8080

LOG_LEVEL = "debug"
WORKERS = 4



class ServiceStatus(str, Enum):
    BUSY = 'busy'
    NO_KEYS = 'no_keys'
    OK = 'OK'


class AppCase(str, Enum):
    PY = 'py'
    EXE = 'exe'
    SRV = 'srv'
