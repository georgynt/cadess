from os.path import join
from uuid import uuid4

from sqlalchemy import BINARY, Column, DECIMAL, Date, String, Uuid, create_engine
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base

from tools import get_installation_dir


DB_URL = f"sqlite+aiosqlite:///{join(get_installation_dir(), 'cades.db')}"
# DB_URL
# DB_URL = f"sqlite:///cades.db"

engine = create_async_engine(DB_URL)
Session = async_sessionmaker(engine, expire_on_commit=True)

Base = declarative_base()


class Document(Base):
    __tablename__ = 'documents'
    guid = Column(Uuid(), primary_key=True, default=uuid4)
    name = Column(String(128))
    number = Column(String(64))
    amount = Column(DECIMAL(17, 5))
    date = Column(Date())
    data = Column(BINARY)
    sign = Column(BINARY)


async def create_tables():
    async with engine.begin() as cnx:
        await cnx.run_sync(Base.metadata.create_all)
