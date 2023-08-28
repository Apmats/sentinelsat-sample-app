from app.settings import get_settings
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine

engine = None


async def init_db():
    global engine
    engine = create_async_engine(get_settings().database_url, echo=True, future=True)
    async with engine.begin() as conn:
        # await conn.run_sync(SQLModel.metadata.drop_all)
        await conn.run_sync(SQLModel.metadata.create_all)


async def get_db() -> AsyncSession:
    global engine
    async_session = sessionmaker(
        bind=engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session() as session:
        yield session
