from abc import ABCMeta, abstractmethod, abstractproperty
from base64 import b64encode
from enum import property
from time import sleep

import pytz
import random
import sys
from datetime import datetime, timedelta
from logging import info, warning, error

from config import Config
from logger import logger



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


class NoAvailableCertificateException(Exception): ...


class LogicAbstract(metaclass=ABCMeta):
    @property
    @abstractmethod
    def certs(self):
        raise NotImplemented("property certs not implemented")

    @property
    @abstractmethod
    def actual_certs(self):
        raise NotImplemented("property actual_certs not implemented")

    @property
    @abstractmethod
    def default_cert(self):
        raise NotImplemented("property default_cert not implemented")

    def find_cert(self, number_or_subject: str|None = None):
        for cert in self.actual_certs:
            if (number_or_subject is None or
                        cert.SerialNumber == number_or_subject or
                        number_or_subject in cert.SubjectName):
                yield cert

    @abstractmethod
    def sign_data(self, data: bytes|str, key_pin: str, detached_sign: bool = True):
        raise NotImplemented("method sign_data not implemented")

    @abstractmethod
    def prepare_data(self, data: str|bytes) -> str|bytes:
        raise NotImplemented("abstract method prepare_data not implemented")


if sys.platform == 'win32':
    import win32com.client as win32
    import win32timezone as w32tz
    import pythoncom
    from win32com.client import CDispatch

    class Logic(LogicAbstract):
        def __init__(self):
            self.conf = Config()
            pythoncom.CoInitialize()
            self.store = win32.Dispatch(STORE)
            for _ in range(10):
                capicom_store = self.conf.capicom_store or CAPICOM_SMART_CARD_USER_STORE
                match capicom_store:
                    case capicom_store if capicom_store in [2,1]:
                        self.store.Open(capicom_store)
                    case CAPICOM_SMART_CARD_USER_STORE:
                        self.store.Open(capicom_store,
                                        CAPICOM_MY_STORE,
                                        CAPICOM_STORE_OPEN_READ_ONLY)

                if len(self.certs) > 0:
                    logger.info('Found RuToken store. Found certificates:')
                    for c in self.certs:
                        logger.info(f"{c.SerialNumber}\n {c.SubjectName}")
                    break
                else:
                    logger.warning("a STORE not ready yet. Try after 10 seconds")
                    sleep(10)
                    self.store.Close()
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
                self._def_cert = next(self.find_cert(self.conf.certnumber))
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

        def sign_data(self,
                      data: bytes|str,
                      key_pin: str|None = None,
                      detached_sign: bool = True) -> bytes:
            signer = win32.Dispatch(SIGNER)
            signer.Certificate = self.default_cert
            if key_pin:
                signer.KeyPin = key_pin
            sd = win32.Dispatch(SIGNED_DATA)
            sd.Content = data
            sign = sd.SignCades(signer, CADES_BES,
                                detached_sign, CAPICOM_ENCODE_BASE64)
            if isinstance(sign, str):
                sign = sign.encode()
            return sign

        def prepare_data(self, data: str|bytes) -> bytes:
            import base64
            return base64.b64decode(data)


elif sys.platform == 'linux':
    import pycades
    from pycades import Certificate

    CDispatch = object

    class Logic(LogicAbstract):
        def __init__(self):
            self.conf = Config()
            self.store = pycades.Store()
            for _ in range(10):
                capicom_store = self.conf.capicom_store or CAPICOM_SMART_CARD_USER_STORE
                match capicom_store:
                    case capicom_store if capicom_store in (2,1):
                        self.store.Open(capicom_store)
                    case CAPICOM_SMART_CARD_USER_STORE:
                        self.store.Open(capicom_store,
                                        pycades.CAPICOM_MY_STORE,
                                        CAPICOM_STORE_OPEN_READ_ONLY)

                if len(self.certs) > 0:
                    logger.info('Found certificates:')
                    for c in self.certs:
                        logger.info(f"{c.SerialNumber}\n {c.SubjectName}")
                    break
                else:
                    logger.warning("a STORE not ready yet. Try after 10 seconds")
                    sleep(10)
                    self.store.Close()
            else:
                logger.warning("NO CERTIFICATES FOUND!")

        @property
        def certs(self):
            return [self.store.Certificates.Item(i+1)
                        for i in range(self.store.Certificates.Count)]

        @property
        def actual_certs(self):
            for cert in self.certs:
                valid_to_date = datetime.strptime(cert.ValidToDate, '%d.%m.%Y %H:%M:%S')
                if valid_to_date > datetime.now():
                    yield cert

        @property
        def default_cert(self) -> Certificate:
            if not hasattr(self,'_def_cert'):
                try:
                    self._def_cert = next(self.find_cert(self.conf.certnumber))
                except StopIteration as e:
                    raise NoAvailableCertificateException("No available certificate")
            logger.info(f'Using default cert {self._def_cert.SerialNumber}')
            return self._def_cert

        @default_cert.setter
        def default_cert(self, value: str|Certificate):
            if isinstance(value, str):
                self._def_cert = next(self.find_cert(value))
            elif isinstance(value, Certificate):
                self._def_cert = value
            else:
                raise ValueError(f"{value} is not instance of pycades.Certificate or str")

        def sign_data(self, data: bytes|str, key_pin: str|None=None, detached_sign: bool = True) -> bytes:
            signer = pycades.Signer()
            signer.Certificate = self.default_cert
            if key_pin:
                signer.KeyPin = key_pin
            sd = pycades.SignedData()

            if isinstance(data, bytes):
                data = data.decode('ascii')
                sd.ContentEncoding = pycades.CADESCOM_BASE64_TO_BINARY

            sd.Content = data
            sign = sd.SignCades(signer, pycades.CADESCOM_CADES_BES,
                                detached_sign, pycades.CAPICOM_ENCODE_BASE64)
            if isinstance(sign, str):
                sign = sign.encode()
            return sign

        def prepare_data(self, data: str|bytes) -> str:
            return data

else:
    CDispatch = object


class MockCert:
    def __init__(self):
        self.SerialNumber = '12345'
        self.SubjectName = "My Certificate"
        self.ValidToDate = datetime.now(tz=pytz.UTC) + timedelta(days=2)

    @property
    def __class__(self):
        return CDispatch


class LogicMock(LogicAbstract):
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

    def sign_data(self, data: bytes|str, key_pin: str,
                  detached_sign: bool = True) -> bytes:
        return b64encode(random.randbytes(1000))
