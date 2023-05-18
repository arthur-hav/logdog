from datetime import datetime, timedelta

from fastapi import Depends, FastAPI

from .handler import DomainHandler, LogFilter
from .binding import handler

app = FastAPI()


@app.get("/logs/{filter_id}")
async def get_logs(
    filter_id: int,
    domain: DomainHandler = Depends(handler),
):
    return await domain.get_logs(filter_id)


@app.post("/filters")
async def store_filters(
    filter_json: list[LogFilter],
    domain: DomainHandler = Depends(handler),
):
    return await domain.store_filters(filter_json)
