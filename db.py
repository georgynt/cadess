from uuid import uuid4

from sqlalchemy import Boolean, Column, String, Uuid, exists, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine, create_async_pool_from_url
from sqlalchemy.orm import declarative_base



DB_URL = "sqlite+aiosqlite:///./cades.db"

engine = create_async_engine(DB_URL)
# pool = create_async_pool_from_url(DB_URL)
Session = async_sessionmaker(engine, expire_on_commit=True)

Base = declarative_base()


class User(Base):
    __tablename__ = 'users'
    username = Column(String(32), primary_key=True)
    password = Column(String(64))
    token = Column(String(512))

    def __str__(self):
        return self.username

    def __repr__(self):
        return f"<User {self.username}>"


class Setting(Base):
    __tablename__ = 'settings'
    name = Column(String(32), primary_key=True)
    value = Column(String(64))


class Document(Base):
    __tablename__ = 'documents'
    guid = Column(Uuid(), primary_key=True, default=uuid4)
    name = Column(String(64))


class IPAddress(Base):
    __tablename__ = 'ipaddresses'
    addr = Column(String(64), primary_key=True)
    enabled = Column(Boolean(), default=True, nullable=False)

    def __str__(self):
        return f"{self.addr}{'+' if self.enabled else '-'}"

    def __repr__(self):
        return f"<IPAddress {self.addr} {'+' if self.enabled else '-'}>"


async def create_tables():
    async with engine.begin() as cnx:
        await cnx.run_sync(Base.metadata.create_all)
        async with Session.begin() as ss:
            if not (await ss.execute(exists(User).select())).scalar():
                ss.add(User(username='admin', password='123'))
            if not (await ss.execute(exists(IPAddress).select())).scalar():
                ss.add(IPAddress(addr='127.0.0.1'))
            if not (pinkey := (await ss.execute(select(Setting).where(Setting.name=='pinkey'))).scalar()):
                ss.add(Setting(name='pinkey', value='ar43n3my'))

