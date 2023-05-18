from datetime import datetime, timedelta
from typing import Any
from pydantic import BaseModel
from enum import Enum


class Log(BaseModel):
    time: datetime
    data: dict[str, Any]


class Operator(Enum):
    GT = ">"
    LT = "<"
    GTE = ">="
    LTE = "<="
    EQ = "="
    RE = "ILIKE"
    NEQ = "!="


class LogFilter(BaseModel):
    key: str
    op: Operator
    value: str


class DomainHandler:
    def __init__(self, repository) -> None:
        self.repository = repository

    async def get_logs(self, filter_id):
        filter_list = await self.repository.get_filters(filter_id)
        time_to = datetime.utcnow()
        time_from = time_to - timedelta(days=7)
        return await self.repository.get_logs(time_from, time_to, filter_list)

    async def store_filters(self, filters: list[LogFilter]):
        return await self.repository.store_filters(filters)
