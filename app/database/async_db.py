from sqlalchemy.orm import DeclarativeBase
from app.core.config import Settings
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker
import logging
from sqlalchemy import text
import psycopg
from psycopg.rows import dict_row
from typing import AsyncGenerator

settings = Settings()

DATABASE_URL = f"postgresql+asyncpg://{settings.DATABASE_USER}:{settings.DATABASE_PASSWORD}@{settings.DATABASE_HOST}:{settings.DATABASE_PORT}/{settings.DATABASE_NAME}"
print("Database URL",DATABASE_URL)

async def check_database_connection():
    try:
        engine = create_async_engine(DATABASE_URL)
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        logging.info("Database connection successful!")
        return True
    except Exception as e:
        logging.error(f"Database connection failed: {str(e)}")
        raise e

async_engine = create_async_engine(DATABASE_URL, echo=True, pool_pre_ping=True)
async_session = sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False)


async def get_db():
    async with async_session() as session:
        yield session

# Add this function to async_db.py
async def get_psycopg_connection() -> AsyncGenerator[psycopg.AsyncConnection, None]:
    conn_string = f"postgresql://{settings.DATABASE_USER}:{settings.DATABASE_PASSWORD}@{settings.DATABASE_HOST}:{settings.DATABASE_PORT}/{settings.DATABASE_NAME}"
    conn = await psycopg.AsyncConnection.connect(conn_string,autocommit=True,prepare_threshold=0,row_factory=dict_row)
    try:
        yield conn
    finally:
        await conn.close()
        await conn.__aexit__(None, None, None)
