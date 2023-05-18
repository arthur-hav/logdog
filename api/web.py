from datetime import datetime, timedelta

from fastapi import Depends, FastAPI

from .handler import DomainHandler
from .binding import handler

app = FastAPI()


@app.get("/logs")
async def get_logs(
    from_time: datetime = datetime.now() - timedelta(days=7),
    to_time: datetime = datetime.now(),
    jsonfilter: str = "{}",
    domain: DomainHandler = Depends(handler),
):
    return await domain.get_logs(from_time, to_time, jsonfilter)
