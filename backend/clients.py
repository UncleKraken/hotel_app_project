# backend/clients.py

import os
import sqlite3
from typing import List, Dict, Optional

# Same base as other backend files
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "database", "hotel.db")


def _get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_clients_table():
    """Create clients table if it doesn't exist yet."""
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS clients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name TEXT NOT NULL,
            last_name  TEXT NOT NULL,
            phone      TEXT,
            email      TEXT,
            notes      TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        )
        """
    )
    conn.commit()
    conn.close()


def get_all_clients() -> List[Dict]:
    init_clients_table()
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute(
        "SELECT id, first_name, last_name, phone, email, notes FROM clients ORDER BY last_name, first_name"
    )
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_client(client_id: int) -> Optional[Dict]:
    init_clients_table()
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute(
        "SELECT id, first_name, last_name, phone, email, notes FROM clients WHERE id = ?",
        (client_id,),
    )
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None


def create_client(first_name: str, last_name: str,
                  phone: str = "", email: str = "", notes: str = "") -> int:
    init_clients_table()
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO clients (first_name, last_name, phone, email, notes)
        VALUES (?, ?, ?, ?, ?)
        """,
        (first_name, last_name, phone, email, notes),
    )
    conn.commit()
    client_id = cur.lastrowid
    conn.close()
    return client_id


def update_client(client_id: int, first_name: str, last_name: str,
                  phone: str = "", email: str = "", notes: str = "") -> None:
    init_clients_table()
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        UPDATE clients
        SET first_name = ?, last_name = ?, phone = ?, email = ?, notes = ?
        WHERE id = ?
        """,
        (first_name, last_name, phone, email, notes, client_id),
    )
    conn.commit()
    conn.close()


def delete_client(client_id: int) -> None:
    init_clients_table()
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM clients WHERE id = ?", (client_id,))
    conn.commit()
    conn.close()
