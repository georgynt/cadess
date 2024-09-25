from os.path import join
from uuid import uuid4

from sqlalchemy import BINARY, Column, DECIMAL, Date, String, Uuid, create_engine, Enum, INT
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
    uuid = Column(Uuid(), primary_key=True, default=uuid4)
    message_id = Column(Uuid(), nullable=True)
    entity_id = Column(Uuid(), nullable=True)

    source_box = Column(Uuid(), nullable=False)
    dest_box = Column(Uuid(), nullable=True) # Может быть пустым, пока не нашли
    dest_inn = Column(String(20), nullable=False)
    dest_kpp = Column(String(20), nullable=True) # Может быть пустым у ИП

    name = Column(String(128))
    number = Column(String(64))
    amount = Column(DECIMAL(17, 5))
    vat = Column(DECIMAL(17, 5), default=0)
    grounds = Column(String(256), nullable=True)
    date = Column(Date())
    data = Column(BINARY)
    sign = Column(BINARY)
    signed_data = Column(BINARY)
    status = Column(Enum(DocumentStatus), default=DocumentStatus.RECEIVED, nullable=False)
    tries = Column(INT, default=0, nullable=False)
    error_msg = Column(String(512), nullable=True)
    login = Column(String(128), nullable=True)
    password = Column(String(128), nullable=True)

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
