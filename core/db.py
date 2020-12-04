from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base, DeclarativeMeta
from sqlalchemy.orm import sessionmaker

from settings import POSTGRES_HOST, POSTGRES_PASSWORD, POSTGRES_PORT, DATABASE

SQLALCHEMY_DATABASE_URL = (
    f"postgres://{DATABASE}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/chat"
)

engine = create_engine(
    SQLALCHEMY_DATABASE_URL
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base: DeclarativeMeta = declarative_base()
