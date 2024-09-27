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
    ALREADY = 'already'


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
    FAKELY_SENT = 'fake_sent'
    FAIL = 'fail'
    # NOT_FOUND = 'not-found'
    RECEIVED = 'received'
    UNKNOWN = 'unkwnown'

    @classmethod
    def bad(cls, status: "DocumentStatus") -> bool:
        return status in (cls.FAIL, cls.UNKNOWN)

    @classmethod
    def good(cls, status: "DocumentStatus") -> bool:
        return status in (cls.SENT, cls.PROGRESS, cls.RECEIVED)


class DocumentStatusRus(StrEnum):
    PROGRESS = 'В обработке'
    SENT = "Отправлено"
    FAKELY_SENT = "Фейк. отправлено"
    FAIL = "Неудача"
    NOT_FOUND = "Не найден"
    RECEIVED = "Получен"
    UNKNOWN = "Неизвестно"
