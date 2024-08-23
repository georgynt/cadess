from uuid import uuid4

from sqlalchemy import Boolean, Column, String, Uuid, exists, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine, create_async_pool_from_url
from sqlalchemy.orm import declarative_base


DB_URL = "sqlite+aiosqlite:///./cades.db"

engine = create_async_engine(DB_URL)
# pool = create_async_pool_from_url(DB_URL)
Session = async_sessionmaker(engine, expire_on_commit=True)

Base = declarative_base()


class Document(Base):
    __tablename__ = 'documents'
    guid = Column(Uuid(), primary_key=True, default=uuid4)
    name = Column(String(64))


async def create_tables():
    async with engine.begin() as cnx:
        await cnx.run_sync(Base.metadata.create_all)
