import contextlib
from typing import AsyncIterator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from src.conf.config import config


class Base(DeclarativeBase):
    pass


class DatabaseSessionManager:
    def __init__(self, url: str):
        self._engine: AsyncEngine | None = create_async_engine(url)
        self._session_maker: async_sessionmaker | None = async_sessionmaker(
            autocommit=False, autoflush=False, expire_on_commit=False, bind=self._engine
        )

    @contextlib.asynccontextmanager
    async def session(self) -> AsyncIterator[AsyncSession]:
        if self._session_maker is None:
            raise Exception("DatabaseSessionManager is not initialized")
        session = self._session_maker()
        try:
            yield session
        except Exception as err:
            print(err)
            await session.rollback()
        finally:
            await session.close()


SQLALCHEMY_DATABASE_URL = f"mysql+aiomysql://{config.mysql_user}:{config.mysql_password}@{config.mysql_host}:{config.mysql_port}/{config.mysql_db}"

sessionmanager = DatabaseSessionManager(SQLALCHEMY_DATABASE_URL)


async def get_db():
    async with sessionmanager.session() as session:
        yield session
