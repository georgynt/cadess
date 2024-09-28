from os.path import join
from uuid import uuid4

from sqlalchemy import BINARY, Column, DECIMAL, Date, DateTime, String, Uuid, create_engine, Enum, INT
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base

from const import DocumentStatus
from tools import get_installation_dir


DB_URL = f"sqlite+aiosqlite:///{join(get_installation_dir(), 'cades.db')}"
# DB_URL
# DB_URL = f"sqlite:///cades.db"

engine = create_async_engine(DB_URL)
Session = async_sessionmaker(engine, expire_on_commit=True)

Base = declarative_base()


class Document(Base):
    __tablename__ = 'documents'
    # IDS
    uuid = Column(Uuid(), primary_key=True)
    message_id = Column(Uuid())
    entity_id = Column(Uuid())
    # source\dest
    source_box = Column(Uuid(), nullable=False)
    dest_box = Column(Uuid()) # Может быть пустым, пока не нашли
    dest_inn = Column(String(20)) # Может быть пустым! (а если передали dest_box?)
    dest_kpp = Column(String(20)) # Может быть пустым у ИП
    # doc requisites
    name = Column(String(128))
    number = Column(String(64))
    amount = Column(DECIMAL(17, 5))
    vat = Column(DECIMAL(17, 5))
    grounds = Column(String(256))
    date = Column(Date())
    send_time = Column(DateTime())
    # content
    data = Column(BINARY)
    sign = Column(BINARY)
    signed_data = Column(BINARY)
    # lifecycle
    status = Column(Enum(DocumentStatus), default=DocumentStatus.RECEIVED, nullable=False)
    tries = Column(INT, default=0, nullable=False)
    error_msg = Column(String(512))
    # rudiments
    login = Column(String(128))
    password = Column(String(128))
    # diadoc lifecycle
    diadoc_status = Column(String(32))
    diadoc_status_descr = Column(String(256))

    @property
    def date_as_str(self):
        return self.date.isoformat()

    def __str__(self):
        return f"doc:id={self.uuid},name={self.name},status={self.status}"

    def __repr__(self):
        return f"<Document uuid={self.uuid} name={self.name} number={self.number} status={self.status}>"


async def create_tables():
    async with engine.begin() as cnx:
        await cnx.run_sync(Base.metadata.create_all)
