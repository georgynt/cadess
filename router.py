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
from const import DiadocServiceStatus, DocumentStatus, DocumentStatusRus, ServiceStatus
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

    uuid: UUID
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
    edo_status: str|None = None
    uuid: UUID
    msg: str


class DocsStatusRequest(BaseModel):
    uuids: list[UUID]


class DocumentStatusRef(BaseModel):
    status: DocumentStatus
    descr: str


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


@router.get('/diadoc-url', tags=['diadoc-url'])
async def diadoc_url() -> dict[str, str]:
    config = Config()
    return {"url": config.diadoc_url or ""}


@router.post('/diadoc-url', tags=['diadoc-url'])
async def diadoc_url(data: dict[str, str]) -> str:
    config = Config()
    config.diadoc_url = data.get('url', config.diadoc_url)
    return "OK"


def get_msg(doc_status: DocumentStatus) -> str:
    match doc_status:
        case DocumentStatus.PROGRESS:
            return 'Документ находится в процессе отправки в ДИАДОК'
        case DocumentStatus.FAIL:
            return "Ошибка отправки документа"
        case DocumentStatus.SENT:
            return "Документ отправлен в ДИАДОК"
        case DocumentStatus.RECEIVED:
            return "Документ получен и скоро перейдёт в обработку"
        case _:
            return "Документ в неизвестном статусе"


@router.get("/documents/{guid}/status", tags=['status'])
async def document_status(guid: UUID) -> DocStatusResponse:
    async with Session() as ss:
        if doc := (await ss.execute(select(Document).where(Document.uuid == guid))).scalar():
            msg = get_msg(doc.status)
            return DocStatusResponse(status=doc.status, uuid=doc.uuid, msg=msg)
        else:
            return DocStatusResponse(status=DocumentStatus.NOT_FOUND, uuid=guid,
                                     msg='Документ не найден. Возможно он был отправлен в ДИАДОК')


@router.post("/documents/status", tags=['status'])
async def document_status(request: DocsStatusRequest) -> list[DocStatusResponse]:
    try:
        async with Session() as ss:
            if docs := (await ss.execute(select(Document).where(Document.uuid.in_(request.uuids)))).scalars():
                return [
                    DocStatusResponse(status=doc.status,
                                      uuid=doc.uuid,
                                      msg=get_msg(doc.status)) for doc in docs
                ]
    except Exception as e:
        raise HTTPException(500, str(e))


@router.get("/status-ref", tags=['status'])
async def status_ref() -> list[DocumentStatusRef]:
    return [
        DocumentStatusRef(status=stt,
                          descr=DocumentStatusRus[stt.name])
            for stt in DocumentStatus
    ]


@router.post("/senddoc", tags=['send'])
async def senddoc(item: DocumentRequest) -> SignedResponse:
    data = b64decode(item.data)
    config = Config()
    try:
        cades = CadesLogic()
        sign = cades.sign_data(data, config.pincode)
        signed_data = cades.sign_data(data, config.pincode, False)

        async with Session() as ss:

            # if (await ss.execute(select(Document).where(Document.uuid==item.uuid).exists()))
            docs = await ss.execute(select(Document).where(Document.uuid==item.uuid))

            for doc in docs:
                logger.warning(f"Document {item.name} № {item.number} {doc.uuid} was received earlier already")
                return SignedResponse(status=ServiceStatus.ALREADY,
                                      msg='Document was received earlier already',
                                      uuid=doc.uuid)
            else:
                doc = Document(**dict(item,
                                      data=data,
                                      sign=sign,
                                      signed_data=signed_data,
                                      status=DocumentStatus.RECEIVED))
                ss.add(doc)
                # await ss.flush()
                await ss.commit()
                await ss.refresh(doc, ['uuid'])

                logger.info(f"Document {item.name} № {item.number} signed and sent to upstream")

    except Exception as e:
        logger.error(f"Document {item.uuid} has errors: {str(e)}")
        raise HTTPException(422, str(e))

    logger.info(f"Document {doc.uuid} signed and queued for send")
    return SignedResponse(status=ServiceStatus.OK,
                          msg='Document signed and sent to upstream',
                          uuid=doc.uuid)

