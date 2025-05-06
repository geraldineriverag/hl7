import os
import json
import sqlite3
from threading import Lock
from datetime import datetime
from .models import HL7Log, AppConfig

BASE_DIR = os.path.dirname(__file__)
DB_PATH = os.path.join(BASE_DIR, '..', 'logs', 'hl7.db')
CONFIG_PATH = os.path.join(BASE_DIR, '..', 'config', 'config.json')
_db_lock = Lock()

# Inicializar la base de datos SQLite

def _get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def _init_db():
    with _db_lock:
        conn = _get_conn()
        conn.execute(
            '''CREATE TABLE IF NOT EXISTS hl7_messages (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   payload TEXT NOT NULL,
                   status TEXT NOT NULL,
                   created_at TEXT NOT NULL,
                   forwarded_at TEXT,
                   response_code INTEGER,
                   response_text TEXT
               )'''
        )
        conn.commit()
        conn.close()

_init_db()

# CRUD de mensajes

def save_message(payload: str) -> HL7Log:
    created = datetime.utcnow().isoformat()
    with _db_lock:
        conn = _get_conn()
        cur = conn.cursor()
        cur.execute(
            'INSERT INTO hl7_messages (payload, status, created_at) VALUES (?, ?, ?)',
            (payload, 'received', created)
        )
        msg_id = cur.lastrowid
        conn.commit()
        conn.close()
    return HL7Log(id=msg_id, message=payload, status='received', created_at=created)


def update_message(id: int, status: str = None, forwarded_at: str = None, response_code: int = None, response: str = None):
    fields, params = [], []
    if status:
        fields.append('status = ?')
        params.append(status)
    if forwarded_at:
        fields.append('forwarded_at = ?')
        params.append(forwarded_at)
    if response_code is not None:
        fields.append('response_code = ?')
        params.append(response_code)
    if response is not None:
        fields.append('response_text = ?')
        params.append(response)
    params.append(id)
    with _db_lock:
        conn = _get_conn()
        conn.execute(
            f"UPDATE hl7_messages SET {', '.join(fields)} WHERE id = ?",
            params
        )
        conn.commit()
        conn.close()


def list_messages() -> list[HL7Log]:
    with _db_lock:
        conn = _get_conn()
        rows = conn.execute(
            'SELECT * FROM hl7_messages ORDER BY created_at DESC'
        ).fetchall()
        conn.close()
    return [
        HL7Log(
            id=r['id'], message=r['payload'], status=r['status'],
            created_at=r['created_at'],
            forwarded_at=r['forwarded_at'] or "",
            response_code=r['response_code'],
            response=r['response_text'] or ""
        )
        for r in rows
    ]


def get_message(msg_id: int) -> HL7Log | None:
    with _db_lock:
        conn = _get_conn()
        r = conn.execute(
            'SELECT * FROM hl7_messages WHERE id = ?',
            (msg_id,)
        ).fetchone()
        conn.close()
    if not r:
        return None
    return HL7Log(
        id=r['id'], message=r['payload'], status=r['status'],
        created_at=r['created_at'],
        forwarded_at=r['forwarded_at'] or "",
        response_code=r['response_code'],
        response=r['response_text'] or ""
    )

# CRUD de configuración

def get_config() -> AppConfig:
    with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
        cfg = json.load(f)
    return AppConfig(**cfg)


def save_config(cfg: dict):
    with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
        json.dump(cfg, f, indent=2)