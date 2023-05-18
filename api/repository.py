from datetime import datetime
from psycopg import AsyncConnection, OperationalError, sql, rows
from pydantic import BaseModel
from typing import Any, Optional, Dict, List
import os
import time


class Datapoint(BaseModel):
    time: datetime
    id: int
    key: Optional[List[str]]
    value: Optional[List[Optional[str]]]
    metric: Optional[List[Optional[float]]]


class Log(BaseModel):
    time: datetime
    data: Dict[str, Any]


class PostgresRepository:
    @classmethod
    async def connect(cls):
        while True:
            try:
                conn = await AsyncConnection.connect(
                    host=os.environ.get("TCK_DB_HOST", "localhost"),
                    user=os.environ.get("TCK_DB_LOGIN", ""),
                    password=os.environ.get("TCK_DB_PASSWORD", ""),
                )
                await conn.set_autocommit(True)
                break
            except OperationalError:
                time.sleep(1)
        return cls(conn)

    def __init__(self, connection) -> None:
        self.conn = connection

    def get_cursor(self, *args, **kwargs):
        return self.conn.cursor(*args, **kwargs)

    async def get_logs(self, from_time, to_time, jsonfilter) -> List[Dict]:
        cur = self.get_cursor(row_factory=rows.class_row(Log))
        await cur.execute(
            f"""
            SELECT time, logdata AS data
            FROM logs
            WHERE time > %s::TIMESTAMP
              AND time < %s::TIMESTAMP
              AND logdata @> %s
            ORDER BY time
            LIMIT 20;
            """,
            (
                from_time,
                to_time,
                jsonfilter,
            ),
        )

        return list(await cur.fetchall())
