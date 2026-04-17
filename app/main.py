from contextlib import asynccontextmanager

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI
from loguru import logger

from app.db.session import AsyncSessionLocal
from app.modules.auth.router import router as auth_router
from app.modules.accounts.router import router as accounts_router
from app.modules.category.router import router as category_router
from app.modules.transactions.router import router as transactions_router
from app.modules.category.service import seed_default_categories
from app.modules.split_bills.router import router as split_bills_router
from app.modules.recurring.service import process_due_recurring
from app.modules.recurring.router import router as recurring_router
from app.modules.reports.router import router as reports_router
from app.modules.reports.service import close_redis_client


async def run_recurring_scheduler():
    async with AsyncSessionLocal() as db:
        summary = await process_due_recurring(db)
        logger.info(f"Scheduler run: {summary}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with AsyncSessionLocal() as db:
        await seed_default_categories(db)
        logger.info("Default categories seeded")

    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        run_recurring_scheduler,
        "interval",
        hours=1,
        id="recurring_transactions",
        name="Process recurring transactions",
    )
    scheduler.start()
    logger.info("APScheduler started (recurring transactions every 1 hour)")

    yield

    scheduler.shutdown()
    logger.info("APScheduler stopped")

    await close_redis_client()
    logger.info("Redis client closed")


app = FastAPI(
    title="Pocketree API",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(auth_router, prefix="/api")
app.include_router(accounts_router, prefix="/api")
app.include_router(category_router, prefix="/api")
app.include_router(transactions_router, prefix="/api")
app.include_router(split_bills_router, prefix="/api")
app.include_router(recurring_router, prefix="/api")
app.include_router(reports_router, prefix="/api")


@app.get("/")
async def root():
    logger.info("Pocketree API running")
    return {"message": "Pocketree API running"}
