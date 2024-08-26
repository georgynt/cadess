from base64 import b64encode

import pytz
import random
import sys
from datetime import datetime, timedelta
from logging import info, warning, error
from logger import logger

if sys.platform == 'win32':
    import win32com.client as win32
    import win32timezone as w32tz
    import pythoncom
    from win32com.client import CDispatch
else:
    CDispatch = object


# CAPICOM
CAPICOM_SMART_CARD_USER_STORE = 4
CAPICOM_MY_STORE = 'CAPICOM_MY_STORE'
CAPICOM_STORE_OPEN_READ_ONLY = 0
CAPICOM_ENCODE_BASE64 = 0

# CADES
CADES_BES = 1


STORE = 'CAdESCOM.Store'
SIGNER = "CAdESCOM.CPSigner"
SIGNED_DATA = "CAdESCOM.CadesSignedData"


if sys.platform == 'win32':
    class Logic:
        def __init__(self):
            pythoncom.CoInitialize()
            self.store = win32.Dispatch(STORE)
            self.store.Open(CAPICOM_SMART_CARD_USER_STORE,
                       CAPICOM_MY_STORE,
                       CAPICOM_STORE_OPEN_READ_ONLY)
            if len(self.certs) > 0:
                logger.info('Found RuToken store. Found certificates:')
                for c in self.certs:
                    logger.info(f"{c.SerialNumber}\n {c.SubjectName}")
            else:
                logger.warning("NO CERTIFICATES FOUND!")

        @property
        def certs(self):
            return list(self.store.Certificates)

        @property
        def actual_certs(self):
            for c in self.certs:
                if c.ValidToDate > w32tz.now():
                    yield c

        @property
        def default_cert(self) -> CDispatch:
            if not hasattr(self,'_def_cert'):
                self._def_cert = next(self.find_cert())
            logger.info(f'Using default cert {self._def_cert.SerialNumber}')
            return self._def_cert

        @default_cert.setter
        def default_cert(self, value: str|CDispatch):
            if isinstance(value, str):
                self._def_cert = next(self.find_cert(value))
            elif isinstance(value, CDispatch):
                self._def_cert = value
            else:
                raise ValueError(f"{value} is not instance of str or COMObject")

        def find_cert(self, number_or_subject: str|None = None):
            for cert in self.actual_certs:
                if (number_or_subject is None or
                        cert.SerialNumber == number_or_subject or
                        number_or_subject in cert.SubjectName):
                    yield cert

        def sign_data(self, data: bytes|str, key_pin: str,
                      detached_sign: bool = True) -> bytes:
            signer = win32.Dispatch(SIGNER)
            signer.Certificate = self.default_cert
            signer.KeyPin = key_pin
            sd = win32.Dispatch(SIGNED_DATA)
            sd.Content = data
            return sd.SignCades(signer, CADES_BES,
                                detached_sign, CAPICOM_ENCODE_BASE64)


class MockCert:
    def __init__(self):
        self.SerialNumber = '12345'
        self.SubjectName = "My Certificate"
        self.ValidToDate = datetime.now(tz=pytz.UTC) + timedelta(days=2)

    @property
    def __class__(self):
        return CDispatch


class LogicMock:
    def __init__(self):
        self.store = None
        self.mock_cert = MockCert()
        logger.warning("Working in Mock mode. No real Rutoken store is using")

    @property
    def certs(self):
        return [self.mock_cert]

    @property
    def actual_certs(self):
        for c in self.certs:
            if c.ValidToDate > datetime.now(tz=pytz.UTC):
                yield c

    @property
    def default_cert(self) -> CDispatch:
        if not hasattr(self,'_def_cert'):
            self._def_cert = next(self.find_cert())
        return self._def_cert

    @default_cert.setter
    def default_cert(self, value: str|CDispatch):
        if isinstance(value, str):
            self._def_cert = next(self.find_cert(value))
        elif isinstance(value, CDispatch):
            self._def_cert = value
        else:
            raise ValueError(f"{value} is not instance of str or COMObject")

    def find_cert(self, number_or_subject: str|None = None):
        for cert in self.actual_certs:
            if (number_or_subject is None or
                    cert.SerialNumber == number_or_subject or
                    number_or_subject in cert.SubjectName):
                yield cert

    def sign_data(self, data: bytes|str, key_pin: str,
                  detached_sign: bool = True) -> bytes:
        return b64encode(random.randbytes(1000))


if sys.platform != 'win32':
    Logic = LogicMock
