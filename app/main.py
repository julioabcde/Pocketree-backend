from contextlib import asynccontextmanager

from fastapi import FastAPI
from loguru import logger

from app.db.session import AsyncSessionLocal
from app.modules.auth.router import router as auth_router
from app.modules.accounts.router import router as accounts_router
from app.modules.category.router import router as category_router
from app.modules.transactions.router import router as transactions_router
from app.modules.category.service import seed_default_categories


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with AsyncSessionLocal() as db:
        await seed_default_categories(db)
        logger.info("Default categories seeded")
    yield


app = FastAPI(
    title="Pocketree API",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(auth_router, prefix='/api')
app.include_router(accounts_router, prefix='/api')
app.include_router(category_router, prefix='/api')
app.include_router(transactions_router, prefix='/api')


@app.get("/")
async def root():
    logger.info("Pocketree API running")
    return {"message": "Pocketree API running"}
