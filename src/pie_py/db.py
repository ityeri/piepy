import os

from sqlalchemy import Engine, create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, AsyncEngine, async_sessionmaker
from sqlalchemy.orm import declarative_base


_engine: Engine
_async_engine: AsyncEngine
Base = declarative_base()
_Session: async_sessionmaker[AsyncSession]

def db_setup():
    global _engine, _async_engine, _Session

    db_path = (
        f'{os.getenv("DB_USER")}:{os.getenv("DB_PASSWORD")}'
        f'@{os.getenv("DB_HOST")}'
        f':3306/{os.getenv("DB_NAME")}'
    )
    db_url = 'mysql+pymysql://' + db_path
    async_db_url = 'mysql+aiomysql://' + db_path

    _engine = create_engine(db_url, echo=True)
    _async_engine = create_async_engine(async_db_url, echo=True)
    _Session = async_sessionmaker(bind=_async_engine, autoflush=False)

def get_engine() -> Engine:
    if _engine is None:
        RuntimeError("Engine is not been initialized")
    return _engine

def get_async_engine() -> AsyncEngine:
    if _async_engine is None:
        RuntimeError("Engine is not been initialized")
    return _async_engine

def get_session_instance() -> AsyncSession:
    return _Session()


__all__ = [
    'get_engine',
    'get_async_engine',
    'get_session_instance',
    'Base',
    'db_setup',
]