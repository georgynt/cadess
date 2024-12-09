from fastapi import HTTPException
from fastapi.routing import APIRouter
from sqlalchemy import select

import logger
from config import Config
from const import DocumentStatusRus
from db import Document, Session
from diadoc.connector import AuthdDiadocAPI, DiadocAPI
from diadoc.enums import CounteragentStatus
from logic import Logic, LogicMock
from router.types import *
from sender import send_document


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
        raise HTTPException(404, "DIADOC service is not available")


def get_msg(doc: Document) -> str:
    match doc.status:
        case DocumentStatus.PROGRESS:
            return 'Документ находится в процессе отправки в ДИАДОК'
        case DocumentStatus.FAIL:
            return doc.error_msg or "Ошибка отправки документа"
        case DocumentStatus.SENT:
            return "Документ отправлен в ДИАДОК"
        case DocumentStatus.RECEIVED:
            return "Документ получен и скоро перейдёт в обработку"
        case _:
            return doc.error_msg or "Документ в неизвестном статусе"


@router.get("/documents/{guid}/status", tags=['status'])
async def document_status(guid: UUID) -> DocStatusResponse:
    try:
        async with Session() as ss:
            if doc := (await ss.execute(select(Document).where(Document.uuid == guid))).scalar():
                dd = AuthdDiadocAPI()
                dsr = DocStatusResponse(status=doc.status, uuid=doc.uuid, dte=doc.send_time, msg=get_msg(doc))

                if stt := dd.get_document_status(doc.source_box, doc.message_id, doc.entity_id):
                    if doc.diadoc_status != stt.Severity or doc.diadoc_status_descr != stt.StatusText:
                        doc.diadoc_status = stt.Severity
                        doc.diadoc_status_descr = stt.StatusText
                        ss.add(doc)
                        ss.commit()

                    dsr.edo_status = stt.Severity
                    dsr.edo_status_descr = stt.StatusText

                return dsr

            else:
                return DocStatusResponse(status=None, uuid=guid,
                                         msg='Документ не найден.')
    except Exception as e:
        raise HTTPException(500, str(e))


async def gen_doc_status_response(dd: DiadocAPI, doc: Document) -> DocStatusResponse:
    doc_stt = await dd.aget_document_status(doc.source_box, doc.message_id, doc.entity_id)
    return DocStatusResponse(status=doc.status,
                             edo_status=doc_stt.Severity if doc_stt else None,
                             edo_status_descr=doc_stt.StatusText if doc_stt else None,
                             uuid=doc.uuid,
                             dte=doc.send_time,
                             msg=get_msg(doc))


@router.post("/documents/status", tags=['status'])
async def document_status(request: DocsStatusRequest) -> list[DocStatusResponse]:
    try:
        async with Session() as ss:
            if docs := (await ss.execute(select(Document).where(Document.uuid.in_(request.uuids)))).all():
                docs = [x for (x,) in docs]
                dd = AuthdDiadocAPI()

                return [
                    await gen_doc_status_response(dd, doc)
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
    config = Config()
    try:
        cades = CadesLogic()
        data = cades.prepare_data(item.data)
        sign = cades.sign_data(data, config.pincode)

        async with Session() as ss:

            docs = (await ss.execute(
                select(Document).where(Document.uuid == item.uuid).with_for_update(skip_locked=True))).scalars()

            for doc in docs:
                if doc.status == DocumentStatus.FAIL:
                    doc.status = DocumentStatus.PROGRESS
                    for k, v in dict(item).items():
                        if k in ['uuid', 'data']: continue
                        setattr(doc, k, v)
                    doc.sign = sign
                    doc.signed_data = item.data

                    ss.add(doc)
                    await ss.commit()
                    await ss.refresh(doc)
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
                doc = Document(**dict(filter(lambda x: x[0] != 'data', item)),
                               sign=sign,
                               signed_data=item.data,
                               status=DocumentStatus.RECEIVED)
                ss.add(doc)
                await ss.flush()
                await ss.refresh(doc, with_for_update=True)

                await send_document(doc)

                ss.add(doc)
                await ss.commit()

                logger.info(f"Document {item.name} № {item.number} signed and sent to upstream")

    except Exception as e:
        logger.error(f"Document {item.uuid} has errors: {str(e)}")
        raise HTTPException(422, str(e))

    return SignedResponse(status=ServiceStatus.OK,
                          msg='Document signed and sent to upstream',
                          uuid=item.uuid)


@router.get("/check-relationship", tags=['contragents'])
async def check_relationship(srcboxid: str|UUID, dstboxid: str|UUID) -> RelationStatus:
    """Получить статус клиента, может ли он участвовать в ЭДО"""
    dd = AuthdDiadocAPI()
    ctg = await dd.aget_ctg(srcboxid, dstboxid)

    return RelationStatus(srcboxid=srcboxid,
                          dstboxid=dstboxid,
                          status=ctg.CurrentStatus,
                          established=ctg.CurrentStatus == CounteragentStatus.IsMyCounteragent)


@router.get("/check-relationship-inn-kpp", tags=['contragents'])
async def check_relationship_inn_kpp(srcboxid: str|UUID, inn: str, kpp: str) -> RelationStatus:
    """Получить статус клиента по ИНН + КПП"""
    dd = AuthdDiadocAPI()
    if len(orgs := await dd.aget_orgs_by_innkpp(inn, kpp)):
        org = orgs[0]
        box = org.Boxes[0]
        if boxid := box.BoxIdGuid:
            if isinstance(ctg := await dd.aget_ctg(srcboxid, boxid), str):
                return RelationStatus(
                    srcboxid=srcboxid,
                    dstboxid=boxid,
                    status=CounteragentStatus.NotInCounteragentList,
                    established=False
                )
            return RelationStatus(srcboxid=srcboxid,
                                  dstboxid=boxid,
                                  status=ctg.CurrentStatus,
                                  established=ctg.CurrentStatus == CounteragentStatus.IsMyCounteragent)


@router.get("/connected-contragents", tags=['contragents'])
async def connected_contragents(srcboxid: str|UUID) -> list[Contragent]:
    """Получить статусы клиентов"""
    dd = AuthdDiadocAPI()
    if isinstance(ctgs := await dd.aget_ctgs(srcboxid), list):
        return [
            Contragent(inn=c.Organization.Inn,
                       kpp=c.Organization.Kpp,
                       boxid=[b.BoxIdGuid for b in c.Organization.Boxes],
                       name=c.Organization.FullName,
                       status=c.CurrentStatus,
                       established=c.CurrentStatus == CounteragentStatus.IsMyCounteragent)
            for c in ctgs
        ]
    elif isinstance(ctgs, str):
        return []
