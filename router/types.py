from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel

from const import DiadocServiceStatus, DocumentStatus, ServiceStatus


# CadesLogic() так делать нельзя. При установке/удалении сервиса происходит попытка считывания. Оно не надо

class Cert(BaseModel):
    number: str
    name: str


class Status(BaseModel):
    code: int
    name: ServiceStatus|DiadocServiceStatus


class DocumentRequest(BaseModel):
    source_box: UUID
    dest_box: UUID|None = None
    dest_inn: str|None = None
    dest_kpp: str|None = None

    uuid: UUID
    name: str
    number: str
    date: date
    amount: Decimal
    vat: Decimal|None = None
    grounds: str|None = None

    data: bytes


class SignedResponse(BaseModel):
    status: ServiceStatus
    msg: str
    uuid: UUID|None = None


class DocStatusResponse(BaseModel):
    status: DocumentStatus|None
    edo_status: str|None = None
    edo_status_descr: str|None = None
    uuid: UUID
    dte: datetime|None = None
    msg: str


class DocsStatusRequest(BaseModel):
    uuids: list[UUID]


class DocumentStatusRef(BaseModel):
    status: DocumentStatus
    descr: str


class RelationStatus(BaseModel):
    srcboxid: str
    dstboxid: str
    status: str
    established: bool


class Contragent(BaseModel):
    inn: str
    kpp: str
    boxid: list[UUID|str]
    name: str
