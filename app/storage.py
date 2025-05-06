import os
import json
import sqlite3
from threading import Lock
from datetime import datetime
from typing import List, Optional

from .models import HL7Log, AppConfig, Destination, Protocol

BASE_DIR    = os.path.dirname(__file__)
DB_PATH     = os.path.join(BASE_DIR, '..', 'logs', 'hl7.db')
CONFIG_PATH = os.path.join(BASE_DIR, '..', 'config', 'config.json')
_db_lock    = Lock()

# ---------------------------------------------------------------------------
# Conexión y creación de tablas
# ---------------------------------------------------------------------------
def _get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def _init_db():
    with _db_lock:
        conn = _get_conn()
        # Tabla de mensajes
        conn.execute('''
          CREATE TABLE IF NOT EXISTS hl7_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            dest_id INTEGER NOT NULL,
            payload TEXT NOT NULL,
            status TEXT NOT NULL,
            created_at TEXT NOT NULL,
            forwarded_at TEXT,
            response_code INTEGER,
            response_text TEXT,
            error_type TEXT,
            error_detail TEXT,
            http_status INTEGER,
            parent_log_id INTEGER
          )''')
        # Tabla de destinos
        conn.execute('''
          CREATE TABLE IF NOT EXISTS destinations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            protocol TEXT NOT NULL,
            host TEXT NOT NULL,
            port INTEGER NOT NULL,
            path TEXT,
            use_tls INTEGER,
            cert_path TEXT
          )''')
        conn.commit()
        conn.close()

_init_db()

# ---------------------------------------------------------------------------
# Destinations CRUD
# ---------------------------------------------------------------------------

def list_destinations() -> List[Destination]:
    with _db_lock:
        conn = _get_conn()
        rows = conn.execute('SELECT * FROM destinations ORDER BY id').fetchall()
        conn.close()
    return [Destination(
        id=r['id'],
        name=r['name'],
        protocol=Protocol(r['protocol']),
        host=r['host'],
        port=r['port'],
        path=r['path'] or "",
        use_tls=bool(r['use_tls']),
        cert_path=r['cert_path'] or ""
    ) for r in rows]


def get_destination(dest_id: int) -> Optional[Destination]:
    with _db_lock:
        conn = _get_conn()
        r = conn.execute('SELECT * FROM destinations WHERE id=?', (dest_id,)).fetchone()
        conn.close()
    if not r:
        return None
    return Destination(
        id=r['id'],
        name=r['name'],
        protocol=Protocol(r['protocol']),
        host=r['host'],
        port=r['port'],
        path=r['path'] or "",
        use_tls=bool(r['use_tls']),
        cert_path=r['cert_path'] or ""
    )


def save_destination(data: dict) -> Destination:
    with _db_lock:
        conn = _get_conn()
        if data.get('id'):
            conn.execute(
                '''UPDATE destinations SET
                     name=?, protocol=?, host=?, port=?, path=?, use_tls=?, cert_path=?
                   WHERE id=?''',
                (
                    data['name'], data['protocol'], data['host'], data['port'],
                    data.get('path', ''), int(data.get('use_tls', False)),
                    data.get('cert_path', ''), data['id']
                )
            )
            dest_id = data['id']
        else:
            cur = conn.execute(
                '''INSERT INTO destinations
                     (name,protocol,host,port,path,use_tls,cert_path)
                   VALUES (?,?,?,?,?,?,?)''',
                (
                    data['name'], data['protocol'], data['host'], data['port'],
                    data.get('path', ''), int(data.get('use_tls', False)),
                    data.get('cert_path', '')
                )
            )
            dest_id = cur.lastrowid
        conn.commit()
        conn.close()
    return get_destination(dest_id)


def delete_destination(dest_id: int) -> None:
    with _db_lock:
        conn = _get_conn()
        conn.execute('DELETE FROM destinations WHERE id=?', (dest_id,))
        conn.commit()
        conn.close()

# ---------------------------------------------------------------------------
# HL7 Logs CRUD
# ---------------------------------------------------------------------------

def save_message(payload: str, dest_id: int) -> HL7Log:
    created = datetime.utcnow().isoformat()
    with _db_lock:
        conn = _get_conn()
        cur = conn.cursor()
        cur.execute(
            '''INSERT INTO hl7_messages
                  (dest_id,payload,status,created_at)
               VALUES (?,?,?,?)''',
            (dest_id, payload, 'pending', created)
        )
        msg_id = cur.lastrowid
        conn.commit()
        conn.close()
    return HL7Log(
        id=msg_id, dest_id=dest_id, message=payload,
        status='pending', created_at=created
    )


def update_message(
    id: int,
    status: Optional[str] = None,
    forwarded_at: Optional[str] = None,
    response_code: Optional[int] = None,
    response: Optional[str] = None,
    error_type: Optional[str] = None,
    error_detail: Optional[str] = None,
    http_status: Optional[int] = None,
    parent_log_id: Optional[int] = None,
):
    fields, params = [], []
    if status is not None:
        fields.append('status = ?'); params.append(status)
    if forwarded_at is not None:
        fields.append('forwarded_at = ?'); params.append(forwarded_at)
    if response_code is not None:
        fields.append('response_code = ?'); params.append(response_code)
    if response is not None:
        fields.append('response_text = ?'); params.append(response)
    if error_type is not None:
        fields.append('error_type = ?'); params.append(error_type)
    if error_detail is not None:
        fields.append('error_detail = ?'); params.append(error_detail)
    if http_status is not None:
        fields.append('http_status = ?'); params.append(http_status)
    if parent_log_id is not None:
        fields.append('parent_log_id = ?'); params.append(parent_log_id)
    params.append(id)
    with _db_lock:
        conn = _get_conn()
        conn.execute(
            f"UPDATE hl7_messages SET {', '.join(fields)} WHERE id = ?", params
        )
        conn.commit()
        conn.close()


def list_messages() -> List[HL7Log]:
    with _db_lock:
        conn = _get_conn()
        rows = conn.execute(
            'SELECT * FROM hl7_messages ORDER BY created_at DESC'
        ).fetchall()
        conn.close()
    return [HL7Log(
        id=r['id'], dest_id=r['dest_id'], message=r['payload'],
        status=r['status'], created_at=r['created_at'],
        forwarded_at=r['forwarded_at'] or "", response=r['response_text'] or "",
        response_code=r['response_code'], error_type=r['error_type'] or "",
        error_detail=r['error_detail'] or "", http_status=r['http_status'],
        parent_log_id=r['parent_log_id']
    ) for r in rows]


def get_message(msg_id: int) -> Optional[HL7Log]:
    with _db_lock:
        conn = _get_conn()
        r = conn.execute(
            'SELECT * FROM hl7_messages WHERE id = ?', (msg_id,)
        ).fetchone()
        conn.close()
    if not r:
        return None
    return HL7Log(
        id=r['id'], dest_id=r['dest_id'], message=r['payload'],
        status=r['status'], created_at=r['created_at'],
        forwarded_at=r['forwarded_at'] or "", response=r['response_text'] or "",
        response_code=r['response_code'], error_type=r['error_type'] or "",
        error_detail=r['error_detail'] or "", http_status=r['http_status'],
        parent_log_id=r['parent_log_id']
    )

# ---------------------------------------------------------------------------
# Config CRUD (JSON)
# ---------------------------------------------------------------------------

def get_config() -> AppConfig:
    with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return AppConfig(**data)


def save_config(cfg: dict) -> None:
    with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
        json.dump(cfg, f, indent=2)
