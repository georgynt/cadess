from base64 import b64decode

import logger
from datetime import date
from decimal import Decimal

from fastapi import File, HTTPException, UploadFile
from fastapi.routing import APIRouter
from pydantic import BaseModel

from config import Config
from const import ServiceStatus
from db import Document, Session
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
    name: ServiceStatus


class DocumentRequest(BaseModel):
    name: str
    number: str
    date: date
    amount: Decimal
    data: str


class SignedResponse(BaseModel):
    status: ServiceStatus
    msg: str
    uuid: str



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


@router.post("/sign", tags=['sign'])
async def sign(file: UploadFile = File(...)) -> SignedResponse:
    data = await file.read()
    config = Config()
    try:
        cades = CadesLogic()
        sign = cades.sign_data(data, config.pincode)
        signed_data = cades.sign_data(data, config.pincode, False)
    except Exception as e:
        raise HTTPException(422, str(e))

    return SignedResponse(status=ServiceStatus.OK, msg='Document signed and sent to upstream')

@router.post("/senddoc", tags=['send'])
async def senddoc(item: DocumentRequest) -> SignedResponse:
    data = b64decode(item.data)
    config = Config()
    try:
        cades = CadesLogic()
        sign = cades.sign_data(data, config.pincode)
        signed_data = cades.sign_data(data, config.pincode, False)

        ss = Session()
        doc = Document(**dict(item),
                     sign=sign)
        ss.add(doc)
        ss.commit()
        logger.info(f"Document {item.name} № {item.number} signed and sent to upstream")

    except Exception as e:
        raise HTTPException(422, str(e))

    return SignedResponse(status=ServiceStatus.OK,
                          msg='Document signed and sent to upstream',
                          uuid=doc.uuid)

