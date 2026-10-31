"""Acceso a datos PostgreSQL."""
import os
import time
import psycopg
from psycopg.rows import dict_row


def db():
    return psycopg.connect(os.environ["DATABASE_URL"], row_factory=dict_row)


def init():
    for attempt in range(30):
        try:
            with db() as con:
                con.execute("""CREATE TABLE IF NOT EXISTS campaigns (
                    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
                    brand TEXT NOT NULL, product TEXT NOT NULL, audience TEXT NOT NULL,
                    photo TEXT NOT NULL, scripts JSONB NOT NULL,
                    selected INTEGER, status TEXT NOT NULL DEFAULT 'draft',
                    error TEXT, instagram_id TEXT, created_at TIMESTAMPTZ DEFAULT now())""")
            return
        except psycopg.OperationalError:
            if attempt == 29:
                raise
            time.sleep(2)


def create(brand, product, audience, photo, scripts):
    with db() as con:
        return con.execute("""INSERT INTO campaigns (brand,product,audience,photo,scripts)
            VALUES (%s,%s,%s,%s,%s::jsonb) RETURNING id""",
            (brand, product, audience, photo, __import__('json').dumps(scripts))).fetchone()["id"]


def get(id):
    with db() as con:
        return con.execute("SELECT * FROM campaigns WHERE id=%s", (id,)).fetchone()


def latest():
    with db() as con:
        return con.execute("SELECT id,brand,product,status,created_at FROM campaigns ORDER BY id DESC LIMIT 8").fetchall()


def queue(id, selected):
    with db() as con:
        con.execute("UPDATE campaigns SET selected=%s,status='queued',error=NULL WHERE id=%s", (selected,id))


def next_job():
    with db() as con:
        row=con.execute("SELECT id FROM campaigns WHERE status='queued' ORDER BY id FOR UPDATE SKIP LOCKED LIMIT 1").fetchone()
        if row:
            con.execute("UPDATE campaigns SET status='working' WHERE id=%s", (row['id'],))
        return row['id'] if row else None


def set_status(id, status, error=None):
    with db() as con:
        con.execute("UPDATE campaigns SET status=%s,error=%s WHERE id=%s", (status,error,id))


def set_published(id, instagram_id):
    with db() as con:
        con.execute("UPDATE campaigns SET status='published',instagram_id=%s WHERE id=%s", (instagram_id,id))


def queue_publish(id):
    with db() as con:
        con.execute("UPDATE campaigns SET status='publish_queued',error=NULL WHERE id=%s AND status IN ('ready','publish_error')",(id,))


def next_publish():
    with db() as con:
        row=con.execute("SELECT id FROM campaigns WHERE status='publish_queued' ORDER BY id FOR UPDATE SKIP LOCKED LIMIT 1").fetchone()
        if row:
            con.execute("UPDATE campaigns SET status='publishing' WHERE id=%s",(row['id'],))
        return row['id'] if row else None
