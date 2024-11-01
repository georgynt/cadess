from sqlalchemy import (BINARY, Column, DECIMAL, Date, DateTime, NullPool, QueuePool, String, Uuid, create_engine, Enum,
                        INT)
from sqlalchemy.dialects.postgresql import BYTEA
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base

from config import Config
from const import DocumentStatus

cfg = Config()

Base = declarative_base()

if 'postgre' in cfg.dbscheme or 'pg' in cfg.dbscheme:
    BINARY = BYTEA
    engine = create_async_engine(cfg.dbcnxstr, future=True, echo=True, poolclass=NullPool)
    Session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
else:
    engine = create_async_engine(cfg.dbcnxstr)
    Session = async_sessionmaker(engine, expire_on_commit=True)

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
    # data = Column(BINARY)
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


async def create_tables(eng=engine):
    async with eng.begin() as cnx:
        await cnx.run_sync(Base.metadata.create_all)

if __name__ == '__main__':
    import asyncio

    # alt_eng = create_async_engine(f"sqlite+aiosqlite:///{join('/opt/cades', 'cades.db')}")
    # alt_eng = create_async_engine(f"postgresql+asyncpg://cades:cades@localhost:5432/cades")
    alt_eng = create_async_engine(cfg.dbcnxstr)
    asyncio.run(create_tables(alt_eng))
