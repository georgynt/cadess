import signal
from asyncio import CancelledError
from types import FrameType
from fastapi.routing import APIRouter
from fastapi import File, UploadFile
from pydantic import BaseModel

from const import LOG_LEVEL, SRV_PORT, ServiceStatus, WORKERS
from cadessrv import CadesService


cades: CadesService = CadesService()

router = APIRouter(prefix="/cades")


class Cert(BaseModel):
    number: str
    name: str


class Status(BaseModel):
    code: int
    name: ServiceStatus


class Document(BaseModel):
    data: bytes
    signature: bytes


@router.get("/keys", tags=['keys'])
async def list_keys() -> list[Cert]:
    return [
        Cert(number=c.SerialNumber, name=c.SubjectName)
        for c in cades.actual_certs
    ]


@router.get("/keys/{number}", tags=['keys'])
async def get_key_description(number: str) -> Cert|str:
    if cert := next(cades.find_cert(number)):
        return Cert(number=cert.SerialNumber, name=cert.SubjectName)
    else:
        return "NOT FOUND"


@router.post("/keys/{number}", tags=['keys'])
async def set_default_key(number: str) -> str:
    print(number, type(number))
    cades.default_cert = number
    return "OK"


@router.get("/status", tags=['status'])
async def status() -> Status:
    return Status(code=1, name=ServiceStatus.OK)


@router.post("/sign", tags=['sign'])
async def sign(file: UploadFile = File(...)) -> Document:
    data = await file.read()
    sign = cades.sign_data(data, 'ar43n3my')
    signed_data = cades.sign_data(data, 'ar43n3my', False)
    return Document(data=signed_data,
                    signature=sign)
