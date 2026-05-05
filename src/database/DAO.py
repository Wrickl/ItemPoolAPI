import os
import json
from enum import Enum
from typing import Any, List

from dotenv import load_dotenv
import psycopg
from psycopg.rows import dict_row

from ..models.Tasks.BaseTask import Task

load_dotenv()


class Collections(str, Enum):
    TASK_MATERIAL = "materials"
    TASK = "tasks"
    TASK_COLLECTION = "task_collection"
    COUNTER = "counters"


class DAO:
    __conn: psycopg.Connection

    def __init__(self):
        # Expected environment variables for PostgreSQL connection
        PG_USER = os.getenv("PG_USER") or os.getenv("POSTGRES_USER")
        PG_PW = os.getenv("PG_PW") or os.getenv("POSTGRES_PASSWORD")
        PG_DB = os.getenv("PG_DB") or os.getenv("POSTGRES_DB")
        PG_PORT = os.getenv("PG_PORT") or os.getenv("POSTGRES_PORT") or "5432"
        PG_HOST = os.getenv("PG_HOST") or os.getenv("POSTGRES_HOST") or "localhost"

        if not all([PG_USER, PG_PW, PG_DB]):
            raise RuntimeError(
                "Postgres connection info missing. Set PG_USER/PG_PW/PG_DB (or POSTGRES_*)."
            )

        conn_str = f"host={PG_HOST} port={PG_PORT} dbname={PG_DB} user={PG_USER} password={PG_PW}"
        # use dict_row to get dictionaries from queries
        self.__conn = psycopg.connect(conn_str, autocommit=True, row_factory=dict_row)

    def _isPydanticObject(self, obj: Any) -> bool:
        return hasattr(obj, "model_dump")

    def _get_next_seq(self, collection_name: str) -> int:
        # Use a simple counters table with columns: name TEXT PRIMARY KEY, seq BIGINT
        sql = (
            "INSERT INTO counters(name, seq) VALUES (%s, 1) "
            "ON CONFLICT (name) DO UPDATE SET seq = counters.seq + 1 "
            "RETURNING seq"
        )
        with self.__conn.cursor() as cur:
            cur.execute(sql, (collection_name,))
            row = cur.fetchone()
            if row and "seq" in row:
                return int(row["seq"])
        # fallback
        return 1

    # ---------- TaskMaterial ----------
    def store_task_material(self, material: Any) -> int | None:
        new_id = self._get_next_seq(Collections.TASK_MATERIAL.value)

        if self._isPydanticObject(material):
            material_obj = material.model_dump(mode="json")
        else:
            material_obj = material

        # store as JSONB in 'materials' table with columns: _id BIGINT PRIMARY KEY, data JSONB
        sql = "INSERT INTO materials(_id, data) VALUES (%s, %s) ON CONFLICT (_id) DO UPDATE SET data = EXCLUDED.data"
        with self.__conn.cursor() as cur:
            cur.execute(sql, (new_id, json.dumps(material_obj)))
        return new_id

    def get_task_material(self, id: int):
        sql = "SELECT data FROM materials WHERE _id = %s"
        with self.__conn.cursor() as cur:
            cur.execute(sql, (int(id),))
            row = cur.fetchone()
            if row and "data" in row:
                return row["data"]
        return None

    # ---------- Task ----------
    def store_task(self, task: Task) -> int | None:
        new_id = self._get_next_seq(Collections.TASK.value)

        # support pydantic or mapping-like task
        if self._isPydanticObject(task):
            task_obj = task.model_dump(mode="json")
        else:
            task_obj = task

        stimulus_ids = task_obj.get("stimulus_ids")
        solution_ids = task_obj.get("solution_ids")
        metadata = task_obj.get("metadata")

        sql = (
            "INSERT INTO tasks(_id, stimulus_ids, solution_ids, metadata) "
            "VALUES (%s, %s, %s, %s) "
            "ON CONFLICT (_id) DO UPDATE SET stimulus_ids = EXCLUDED.stimulus_ids, solution_ids = EXCLUDED.solution_ids, metadata = EXCLUDED.metadata"
        )
        with self.__conn.cursor() as cur:
            cur.execute(
                sql,
                (new_id, json.dumps(stimulus_ids), json.dumps(solution_ids), json.dumps(metadata)),
            )
        return new_id

    # ---------- Task Collection ----------
    def store_task_collection(self, task_collection: List[int], task_collection_name: str) -> int | None:
        new_id = self._get_next_seq(Collections.TASK_COLLECTION.value)
        sql = (
            "INSERT INTO task_collection(_id, task_ids, name) VALUES (%s, %s, %s) "
            "ON CONFLICT (_id) DO UPDATE SET task_ids = EXCLUDED.task_ids, name = EXCLUDED.name"
        )
        with self.__conn.cursor() as cur:
            cur.execute(sql, (new_id, json.dumps(task_collection), task_collection_name))
        return new_id

    def fetch_task_collection(self, id: int) -> List[int]:
        sql = "SELECT task_ids FROM task_collection WHERE _id = %s"
        with self.__conn.cursor() as cur:
            cur.execute(sql, (int(id),))
            row = cur.fetchone()
            if row and "task_ids" in row and row["task_ids"] is not None:
                return row["task_ids"]
        return []


dao = DAO()
