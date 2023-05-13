from datetime import datetime
from psycopg import AsyncConnection, OperationalError, sql
from psycopg.rows import class_row
from pydantic import BaseModel
from typing import Any, Optional, Dict, List, Union, Tuple
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
    id: int
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

    def get_filter_for_key_value(self, key, value):
        if key and value:
            return "key LIKE %s AND value LIKE %s"
        if value:
            return "(%s = '_unused' OR TRUE) AND value LIKE %s"
        if key:
            return "key LIKE %s AND (%s = '_unused' OR TRUE)"
        return "%s = %s"

    async def get_logs(self, key_filter, value_like, key_filter2, value_like2, page) -> Tuple[List[Log], int]:
        result_logs: Dict[int, Log] = {}
        cur = self.get_cursor(row_factory=class_row(Datapoint))
        filter_1 = self.get_filter_for_key_value(key_filter, value_like)
        filter_2 = self.get_filter_for_key_value(key_filter2, value_like2)
        await cur.execute(
            f"""
        SELECT ev.id,
                min(ev.time) AS time,
                array_agg(ev.key) AS key,
                array_agg(ev.value) AS value,
                array_agg(ev.metric) AS metric
            FROM event as ev
            WHERE ev.id IN (SELECT ev.id WHERE {filter_1} AND {filter_2})
            GROUP BY ev.id
            ORDER BY time
            LIMIT 20
            OFFSET 20 * (%s - 1);
            """,
            ("%" + key_filter + "%", "%" + value_like + "%", "%" + key_filter2 + "%", "%" + value_like2 + "%", page),
        )
        for point in await cur.fetchall():
            if not point.key:
                continue
            result_logs[point.id] = Log(time=point.time, id=point.id, data={})
            for key, value, metric in zip(point.key, point.value, point.metric):
                recurse: Union[Dict, List] = result_logs[point.id].data
                key_chain = key.split(".")
                for i, elem in enumerate(key_chain):
                    if elem.isnumeric():
                        elem = int(elem)
                    if i == len(key_chain) - 1:
                        if isinstance(elem, int):
                            recurse.extend([None] * (elem - len(recurse) + 1))
                            recurse[elem] = value or metric
                        else:
                            recurse[elem] = value or metric
                    elif elem not in recurse:
                        if key_chain[i + 1].isnumeric():
                            recurse[elem] = []
                        else:
                            recurse[elem] = {}
                    recurse = recurse[elem]
        cur = self.get_cursor()
        await cur.execute(
            f"""
        SELECT COUNT(DISTINCT event.id) FROM event
             WHERE {filter_1} AND {filter_2}""",
            (
                "%" + key_filter + "%",
                "%" + value_like + "%",
                "%" + key_filter2 + "%",
                "%" + value_like2 + "%",
            ),
        )
        return list(result_logs.values()), (await cur.fetchone())[0]

    async def flatten_dict(self, key, dct, prefix=""):
        value = dct[key]
        if isinstance(value, (str, int, float)):
            yield prefix + str(key), value
        elif isinstance(value, list):
            for i, v in enumerate(value):
                async for k, v2 in self.flatten_dict(i, value, prefix + str(key) + "."):
                    yield k, v2
        else:
            for k, v in value.items():
                async for k2, v2 in self.flatten_dict(k, value, prefix + str(key) + "."):
                    yield k2, v2

    async def make_log(self, post_data) -> None:
        cur = self.get_cursor()
        _id = None
        for key in post_data.data.keys():
            async for k2, v2 in self.flatten_dict(key, post_data.data):
                column_val = "value" if isinstance(v2, str) else "metric"
                query_str = """INSERT INTO event (time, key, {column_val}) VALUES (%s, %s, %s) RETURNING id;"""
                if _id:
                    query_str = """INSERT INTO event (time, key, {column_val}, id) VALUES (%s, %s, %s, %s);"""
                await cur.execute(
                    sql.SQL(query_str).format(
                        column_val=sql.Identifier(column_val),
                    ),
                    (post_data.time, k2, v2, _id) if _id else (post_data.time, k2, v2),
                )
                if not _id:
                    _id = (await cur.fetchone())[0]
        return None

    async def get_keys(self):
        cur = self.get_cursor()
        await cur.execute("""SELECT DISTINCT key FROM event;""")
        return [row[0] for row in await cur.fetchall()]

    async def get_values(self, key):
        cur = self.get_cursor()
        await cur.execute("""SELECT DISTINCT value FROM event WHERE key = %s;""", (key,))
        return [row[0] for row in await cur.fetchall()]

    async def get_metrics(self, key):
        cur = self.get_cursor()
        await cur.execute("""SELECT DISTINCT metric FROM event WHERE key = %s;""", (key,))
        return [row[0] for row in await cur.fetchall()]
