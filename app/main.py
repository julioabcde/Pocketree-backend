from fastapi import FastAPI
from loguru import logger

app = FastAPI(title="Pocketree API", version="1.0.0")


@app.get("/")
async def root():
    logger.info("Pocketree API running")
    return {"message": "Pocketree API running"}
