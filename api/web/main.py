from datetime import datetime
from typing import Dict, List, Optional, Any

from fastapi import Depends, FastAPI
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from ..domain.handler import DomainHandler
from ..repository.repository import Log
from .binding import handler

app = FastAPI()


class PostData(BaseModel):
    time: datetime
    data: Dict[str, Any]


class PostElement(BaseModel):
    priority: int
    keys: List[str]
    html: str


@app.get("/")
async def get_logs(
    key: str = "",
    value: str = "",
    group: str = "",
    groupval: str = "",
    page: int = 1,
    domain: DomainHandler = Depends(handler),
):
    r = JSONResponse(content=jsonable_encoder(await domain.get_logs(key, value, group, groupval, page)))
    r.headers["Access-Control-Allow-Origin"] = "*"
    return r


@app.post("/")
async def post_logs(data: PostData, domain: DomainHandler = Depends(handler)):
    return await domain.make_log(data)


@app.get("/keys")
async def get_keys(domain: DomainHandler = Depends(handler)):
    r = JSONResponse(content=jsonable_encoder(await domain.get_keys()))
    r.headers["Access-Control-Allow-Origin"] = "*"
    return r


@app.get("/values/{key}")
async def get_values(key: str, domain: DomainHandler = Depends(handler)):
    r = JSONResponse(content=jsonable_encoder(await domain.get_values(key)))
    r.headers["Access-Control-Allow-Origin"] = "*"
    return r


@app.get("/metrics/{key}")
async def get_metrics(key: str, domain: DomainHandler = Depends(handler)):
    r = JSONResponse(content=jsonable_encoder(await domain.get_metrics(key)))
    r.headers["Access-Control-Allow-Origin"] = "*"
    return r
