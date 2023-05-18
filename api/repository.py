from psycopg import AsyncConnection, OperationalError, sql, rows
from typing import Dict, List
import os
import time
from .handler import Log, LogFilter
from psycopg.types.json import Json
from fastapi.encoders import jsonable_encoder
import json


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

    async def get_logs(self, time_from, time_to, filter_list: list[LogFilter]) -> List[Dict]:
        cur = self.get_cursor(row_factory=rows.class_row(Log))
        prepare = sql.SQL(
            """
            SELECT time, logdata AS data
            FROM logs
            WHERE time > %s::TIMESTAMP
              AND time < %s::TIMESTAMP"""
        )
        query_args = [time_from, time_to]
        for filter_json in filter_list:
            prepare += sql.SQL(""" AND logdata ->> %s {} %s """.format(filter_json["op"]))
            query_args.extend(
                [
                    filter_json["key"],
                    int(filter_json["value"]) if filter_json["value"].isnumeric() else filter_json["value"],
                ]
            )
        prepare += sql.SQL(""" ORDER BY time DESC LIMIT 20;""")
        await cur.execute(prepare, tuple(query_args))

        return list(await cur.fetchall())

    async def store_filters(self, filters: list[LogFilter]) -> int:
        cur = self.get_cursor()
        await cur.execute(
            """
            INSERT INTO filters (list_filters) VALUES (%s::JSONB)
                RETURNING id;
            """,
            (Json(jsonable_encoder(filters)),),
        )

        return (await cur.fetchone())[0]

    async def get_filters(self, filter_id: int) -> list[LogFilter]:
        cur = self.get_cursor()
        await cur.execute(
            """
            SELECT list_filters
                FROM filters WHERE id = %s;
            """,
            (filter_id,),
        )

        return (await cur.fetchone())[0]
