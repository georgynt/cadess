from enum import Enum


SRV_PORT = 8000
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
