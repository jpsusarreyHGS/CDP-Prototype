"""FastAPI entry point for the data inventory aggregation service."""
from __future__ import annotations

from fastapi import FastAPI

from routers.inventory_aggregator import router as inventory_router

app = FastAPI(title="Customer Data Platform Inventory API")
app.include_router(inventory_router, prefix="/inventory")

@app.get("/")
async def root():
    return {"message": "Platform Inventory API"}

