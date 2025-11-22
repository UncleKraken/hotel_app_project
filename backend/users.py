# backend/users.py

from typing import Optional, Dict
from .db import get_connection


def get_user_by_username(username: str) -> Optional[Dict]:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT user_id, username, password, full_name, role FROM users WHERE username = ?",
        (username,),
    )
    row = cur.fetchone()
    conn.close()
    if not row:
        return None
    return {
        "user_id": row[0],
        "username": row[1],
        "password": row[2],
        "full_name": row[3],
        "role": row[4],
    }


def create_user(username: str, password: str, full_name: str, role: str) -> int:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO users (username, password, full_name, role)
        VALUES (?, ?, ?, ?)
        """,
        (username, password, full_name, role),
    )
    user_id = cur.lastrowid
    conn.commit()
    conn.close()
    return user_id


def ensure_default_users():
    """
    Optional: create a few demo users if table is empty.
    """
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM users")
    count = cur.fetchone()[0]
    if count == 0:
        # username, password, full_name, role
        cur.execute(
            "INSERT INTO users (username, password, full_name, role) VALUES (?, ?, ?, ?)",
            ("reception", "1234", "Front Desk", "Receptionist"),
        )
        cur.execute(
            "INSERT INTO users (username, password, full_name, role) VALUES (?, ?, ?, ?)",
            ("waiter", "1234", "Waiter One", "Bar & Restaurant"),
        )
        cur.execute(
            "INSERT INTO users (username, password, full_name, role) VALUES (?, ?, ?, ?)",
            ("clean", "1234", "Cleaning Staff", "Cleaning"),
        )
        cur.execute(
            "INSERT INTO users (username, password, full_name, role) VALUES (?, ?, ?, ?)",
            ("finance", "1234", "Finance Staff", "Finance"),
        )
        conn.commit()
    conn.close()
