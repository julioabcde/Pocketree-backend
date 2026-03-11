from fastapi import FastAPI
from loguru import logger

from app.modules.auth.router import router as auth_router
from app.modules.accounts.router import router as accounts_router

app = FastAPI(title="Pocketree API", version="1.0.0")

app.include_router(auth_router)
app.include_router(accounts_router)

@app.get("/")
async def root():
    logger.info("Pocketree API running")
    return {"message": "Pocketree API running"}
