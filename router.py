from base64 import b64decode
from uuid import UUID

from sqlalchemy import select

import logger
from datetime import date
from decimal import Decimal

from fastapi import File, HTTPException, UploadFile
from fastapi.routing import APIRouter
from pydantic import BaseModel

from config import Config
from const import DiadocServiceStatus, DocumentStatus, ServiceStatus
from db import Document, Session
from diadoc.connector import AuthdDiadocAPI
from logic import LogicMock, Logic


__cades = None

def CadesLogic():
    global __cades

    cfg = Config()
    if not __cades:
        if cfg.fake_logic:
            __cades = LogicMock()
        else:
            __cades = Logic()
    return __cades

router = APIRouter(prefix="/cades")
# CadesLogic() так делать нельзя. При установке/удалении сервиса происходит попытка считывания. Оно не надо

class Cert(BaseModel):
    number: str
    name: str


class Status(BaseModel):
    code: int
    name: ServiceStatus|DiadocServiceStatus


class DocumentRequest(BaseModel):
    source_box: UUID
    dest_box: UUID | None = None
    dest_inn: str | None = None
    dest_kpp: str | None = None

    name: str
    number: str
    date: date
    amount: Decimal
    data: str
    login: str
    password: str


class SignedResponse(BaseModel):
    status: ServiceStatus
    msg: str
    uuid: UUID | None = None


class DocStatusResponse(BaseModel):
    status: DocumentStatus
    guid: UUID
    msg: str


@router.get("/keys", tags=['keys'])
async def list_keys() -> list[Cert]:
    cades = CadesLogic()

    return [
        Cert(number=c.SerialNumber, name=c.SubjectName)
        for c in cades.actual_certs
    ]


@router.get("/keys/{number}", tags=['keys'])
async def get_key_description(number: str) -> Cert|str:
    cades = CadesLogic()

    if cert := next(cades.find_cert(number)):
        return Cert(number=cert.SerialNumber, name=cert.SubjectName)
    else:
        raise HTTPException(404, "KEY NOT FOUND")


@router.post("/keys/{number}", tags=['keys'])
async def set_default_key(number: str) -> str:
    cades = CadesLogic()
    cades.default_cert = number

    return "OK"


@router.get("/status", tags=['status'])
async def status() -> Status:
    return Status(code=1, name=ServiceStatus.OK)


@router.get("/diadoc", tags=['diadoc'])
async def diadoc() -> Status:
    dd = AuthdDiadocAPI()
    if dd.authenticate():
        return Status(code=1, name=DiadocServiceStatus.OK)
    else:
        # return Status(code=-1, name=DiadocServiceStatus.NOT_AVAILABLE)
        raise HTTPException(404, "DIADOC service is not available")


@router.get('/client-id', tags=['client-id'])
async def client_id() -> dict[str, str]:
    config = Config()
    return {"value": config.client_id or ""}


@router.post('/client-id', tags=['client-id'])
async def client_id(data: dict[str, str]) -> str:
    config = Config()
    config.client_id = data.get('value', config.client_id)
    return "OK"


@router.get('/diadoc-url', tags=['client-id'])
async def diadoc_url() -> dict[str, str]:
    config = Config()
    return {"url": config.diadoc_url or ""}


@router.post('/diadoc-url', tags=['client-id'])
async def diadoc_url(data: dict[str, str]) -> str:
    config = Config()
    config.diadoc_url = data.get('url', config.diadoc_url)
    return "OK"


@router.get("/documents/{guid}/status", tags=['status'])
async def document_status(guid: UUID) -> DocStatusResponse:
    ss = Session()
    if doc := (await ss.execute(select(Document).where(Document.guid==guid))).scalar():
        match doc.status:
            case DocumentStatus.PROGRESS:
                msg = 'Документ находится в процессе отправки в ДИАДОК'
            case DocumentStatus.FAIL:
                msg = "Ошибка отправки документа"
            case DocumentStatus.SENT:
                msg = "Документ отправлен в ДИАДОК"
            case DocumentStatus.RECEIVED:
                msg = "Документ получен и скоро перейдёт в обработку"
            case _:
                return DocStatusResponse(status=DocumentStatus.UNKNOWN, msg="Документ в неизвестном статусе")
        return DocStatusResponse(status=doc.status, guid=doc.guid, msg=msg)
    else:
        return DocStatusResponse(status=DocumentStatus.NOT_FOUND, guid=doc.guid,
                                 msg='Документ не найден. Возможно он был отправлен в ДИАДОК')


# @router.post("/sign", tags=['sign'])
# async def sign(file: UploadFile = File(...)) -> SignedResponse:
#     # Этот метод пока что не нужен, мы не отдаём ЭЦП клиенту, мы просто отправляем подписанный док. в ДИАДОК
#     data = await file.read()
#     config = Config()
#     try:
#         cades = CadesLogic()
#         sign = cades.sign_data(data, config.pincode)
#         signed_data = cades.sign_data(data, config.pincode, False)
#     except Exception as e:
#         raise HTTPException(422, str(e))
#
#     return SignedResponse(status=ServiceStatus.OK, msg='Document signed and sent to upstream')


@router.post("/senddoc", tags=['send'])
async def senddoc(item: DocumentRequest) -> SignedResponse:
    data = b64decode(item.data)
    config = Config()
    try:
        cades = CadesLogic()
        sign = cades.sign_data(data, config.pincode)
        signed_data = cades.sign_data(data, config.pincode, False)

        ss = Session()
        doc = Document(**dict(item,
                              data=data,
                              sign=sign,
                              signed_data=signed_data,
                              status=DocumentStatus.RECEIVED))
        ss.add(doc)
        await ss.flush()
        await ss.commit()
        await ss.refresh(doc, ['guid'])

        logger.info(f"Document {item.name} № {item.number} signed and sent to upstream")

    except Exception as e:
        raise HTTPException(422, str(e))

    return SignedResponse(status=ServiceStatus.OK,
                          msg='Document signed and sent to upstream',
                          uuid=doc.guid)

