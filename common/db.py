
from typing import Any, Sequence
import psycopg2
import psycopg2.extras
from common.config import POSTGRES_DSN

def get_conn():
    return psycopg2.connect(POSTGRES_DSN)

def fetch_one(query: str, params: Sequence[Any] = ()):
    with get_conn() as conn, conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(query, params)
        return cur.fetchone()

def fetch_all(query: str, params: Sequence[Any] = ()):
    with get_conn() as conn, conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(query, params)
        return cur.fetchall()

def execute(query: str, params: Sequence[Any] = ()):
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(query, params)
        conn.commit()
