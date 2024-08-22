import sqlalchemy as db
from sqlalchemy import Column, Integer, ForeignKey, String
from sqlalchemy.ext.declarative import declarative_base, declared_attr

engine = db.create_engine("sqlite:///cades.db")

cnx = engine.connect()


Base = declarative_base()


class User(Base):
    __tablename__ = 'users'
    username = Column(String())
    password = Column(String())

class Setting(Base):
    name = Column(String())
    value = Column(String())

class
