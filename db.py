from uuid import uuid4

import sqlalchemy as db
from sqlalchemy import Boolean, Column, String, Uuid
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base, sessionmaker


DB_URL = "sqlite+aiosqlite:///./cades.db"

aengine = create_async_engine(DB_URL)
ASession = async_sessionmaker(aengine, expire_on_commit=True)

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
        return self.addr

    def __repr__(self):
        return f"<IPAddress {self.addr} {'+' if self.enabled else '-'}"


def create_tables():
    DB_URL = "sqlite:///./cades.db"

    engine = db.create_engine(DB_URL)
    Base.metadata.create_all(engine)
    Session = sessionmaker(engine)
