import sys
from enum import Enum, StrEnum


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


class DiadocServiceStatus(StrEnum):
    NOT_AVAILABLE = 'not_available'
    OK = 'OK'
    # some others

class AppCase(str, Enum):
    PY = 'py'
    EXE = 'exe'
    SRV = 'srv'


class DocumentStatus(StrEnum):
    PROGRESS = 'progress'
    SENT = 'sent'
    FAIL = 'fail'
    NOT_FOUND = 'not-found'
    RECEIVED = 'received'
    UNKNOWN = 'unkwnown'
