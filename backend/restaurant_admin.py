# backend/restaurant_admin.py

import sqlite3
from typing import List, Dict, Any

from . import config   # uses your existing DB_PATH


def get_connection():
    return sqlite3.connect(config.DB_PATH)


# ---------- MENU ITEMS ----------

def get_menu_items() -> List[Dict[str, Any]]:
    """Return all menu items as list of dicts."""
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute(
        """
        SELECT item_id, category, name, price
        FROM menu_items
        ORDER BY category, name
        """
    )
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


def insert_menu_item(category: str, name: str, price: float) -> int:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO menu_items (category, name, price)
        VALUES (?, ?, ?)
        """,
        (category, name, price),
    )
    conn.commit()
    new_id = cur.lastrowid
    conn.close()
    return new_id


def update_menu_item(item_id: int, category: str, name: str, price: float) -> None:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        UPDATE menu_items
        SET category = ?, name = ?, price = ?
        WHERE item_id = ?
        """,
        (category, name, price, item_id),
    )
    conn.commit()
    conn.close()


def delete_menu_item(item_id: int) -> None:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM menu_items WHERE item_id = ?", (item_id,))
    conn.commit()
    conn.close()


# ---------- RESTAURANT TABLES ----------

def get_tables() -> List[Dict[str, Any]]:
    """Return all restaurant tables as list of dicts."""
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute(
        """
        SELECT table_id, table_number, status, seats
        FROM restaurant_tables
        ORDER BY table_number
        """
    )
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


def insert_table(table_number: int, status: str, seats: int) -> int:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO restaurant_tables (table_number, status, seats)
        VALUES (?, ?, ?)
        """,
        (table_number, status, seats),
    )
    conn.commit()
    new_id = cur.lastrowid
    conn.close()
    return new_id


def update_table(table_id: int, table_number: int, status: str, seats: int) -> None:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        UPDATE restaurant_tables
        SET table_number = ?, status = ?, seats = ?
        WHERE table_id = ?
        """,
        (table_number, status, seats, table_id),
    )
    conn.commit()
    conn.close()


def delete_table(table_id: int) -> None:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM restaurant_tables WHERE table_id = ?", (table_id,))
    conn.commit()
    conn.close()
