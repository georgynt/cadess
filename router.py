from fastapi import File, UploadFile
from fastapi.routing import APIRouter
from pydantic import BaseModel
from sqlalchemy import select

from const import ServiceStatus
from db import Session, User
from logic import LogicMock


cades = LogicMock()

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


class UserStruct(BaseModel):
    username: str
    password: str


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


@router.get("/users", tags=['users'])
async def users() -> list[str]:
    async with Session.begin() as ss:
        return [u.username for (u,) in
                (await ss.execute(select(User)))]


@router.post("/users", tags=['adduser'])
async def users(user: UserStruct) -> str:
    async with Session.begin() as ss:
        u = User(username=user.username, password=user.password)
        ss.add(u)
        return "OK"
