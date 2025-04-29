from fastapi import FastAPI 
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.routes import chat_route
from app.database.async_db import async_engine, async_session
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker 
from app.database.async_db import check_database_connection





@asynccontextmanager
async def lifespan(app: FastAPI):
    print("startup")
    connection_status = await check_database_connection()
    if connection_status:
        print("Database connection successful!")
    else:
        print("Database connection failed!")
        raise Exception("Database connection failed!")
    yield





app = FastAPI(lifespan=lifespan)

CORSMiddleware(
    app,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

app.include_router(chat_route.router)

