import asyncio
import os

import pytest
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from app.database import get_db
from app.settings import update_settings, get_settings
from src.app.main import app
from testcontainers.postgres import PostgresContainer
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import SQLModel
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.pool import NullPool
from shutil import rmtree


@pytest.fixture(scope="session", autouse=True)
def override_settings():
    update_settings(
        database_url="postgresql+asyncpg://none:none@none:123/none",
        sentinelsat_user="null",
        sentinelsat_pass="null",
        image_directory="test/images",
        temp_image_directory="test/temp_images",
    )


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def db_container(event_loop):
    postgres = PostgresContainer("postgres:14")
    postgres.start()
    postgres.driver = "asyncpg"
    yield postgres
    postgres.stop()


@pytest.fixture(scope="module")
async def db(db_container, event_loop):
    test_engine = create_async_engine(
        db_container.get_connection_url(),
        poolclass=NullPool,
    )

    async with test_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    async def get_db_override() -> AsyncSession:
        async_session = sessionmaker(
            test_engine, class_=AsyncSession, expire_on_commit=False
        )
        async with async_session() as session:
            yield session

    app.dependency_overrides[get_db] = get_db_override

    yield test_engine
    async with test_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)


@pytest.fixture(scope="module", autouse=True)
async def image_folder():
    try:
        rmtree(get_settings().image_directory)
    except:
        pass
    os.makedirs(get_settings().image_directory)
    yield
    rmtree(get_settings().image_directory)


@pytest.fixture(scope="module")
async def client(db):
    return TestClient(app=app, base_url="http://test")
