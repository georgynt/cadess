from base64 import b64decode

from fastapi import HTTPException
from fastapi.routing import APIRouter
from sqlalchemy import select

import logger
from config import Config
from const import DocumentStatusRus
from db import Document, Session
from diadoc.connector import AuthdDiadocAPI, ConfiguredDiadocAPI, DiadocAPI
from logic import Logic, LogicMock
from router.types import *


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
    try:
        async with Session() as ss:
            if doc := (await ss.execute(select(Document).where(Document.uuid == guid))).scalar():
                dd = ConfiguredDiadocAPI()
                dd.authenticate(doc.login, doc.password)
                stt = dd.get_document_status(doc.source_box, doc.message_id, doc.entity_id)
                msg = get_msg(doc.status)
                return DocStatusResponse(status=doc.status,
                                         edo_status=stt.Severity if stt else None,
                                         edo_status_descr=stt.StatusText if stt else None,
                                         uuid=doc.uuid,
                                         dte=doc.send_time,
                                         msg=msg)
            else:
                return DocStatusResponse(status=None, uuid=guid,
                                         msg='Документ не найден. Возможно он был отправлен в ДИАДОК, но затем удалён')
    except Exception as e:
        raise HTTPException(500, str(e))


async def gen_doc_status_response(dd: DiadocAPI, doc: Document, login: str, passwd: str) -> DocStatusResponse:
    doc_stt = await dd.aget_document_status(doc.source_box, doc.message_id, doc.entity_id)
    return DocStatusResponse(status=doc.status,
                             edo_status=doc_stt.Severity if doc_stt else None,
                             edo_status_descr=doc_stt.StatusText if doc_stt else None,
                             uuid=doc.uuid,
                             dte=doc.send_time,
                             msg=get_msg(doc.status))


@router.post("/documents/status", tags=['status'])
async def document_status(request: DocsStatusRequest) -> list[DocStatusResponse]:
    try:
        async with Session() as ss:
            if docs := (await ss.execute(select(Document).where(Document.uuid.in_(request.uuids)))).all():
                docs = [x for (x,) in docs]
                login, pswd = list(set((d.login, d.password) for d in docs)).pop()
                dd = ConfiguredDiadocAPI()
                dd.authenticate(login, pswd)

                return [
                    await gen_doc_status_response(dd, doc, login, pswd)
                    for doc in docs
                ]
            return []

    except Exception as e:
        logger.error(str(e))
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
            docs = (await ss.execute(select(Document).where(Document.uuid == item.uuid))).scalars()

            for doc in docs:
                if doc.status == DocumentStatus.FAIL:
                    doc.status = DocumentStatus.PROGRESS
                    for k,v in dict(item).items():
                        if k == 'uuid': continue
                        setattr(doc, k, v)

                    ss.add(doc)
                    await ss.commit()
                    logger.info(f"Document {doc.name} №{doc.number} {doc.uuid} was sent again")
                    return SignedResponse(status=ServiceStatus.OK,
                                          msg='Document is restarted for send',
                                          uuid=doc.uuid)
                else:
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
