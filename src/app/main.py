from fastapi import FastAPI

from app.database import init_db
from app.routers import images


app = FastAPI()

app.include_router(images.router, prefix="/images")


@app.on_event("startup")
async def on_startup():
    await init_db()
