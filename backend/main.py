from fastapi import FastAPI
from database.connection_db import connection
from contextlib import asynccontextmanager


@asynccontextmanager
async def lifespan(app: FastAPI):
    await connection.init_connection()
    yield
    await connection.close_connection()

app = FastAPI(lifespan=lifespan)


@app.get("/")
async def say_hello():
    return {"message": "Test"}
