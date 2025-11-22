# backend/rooms.py

from typing import List, Dict
from .db import get_connection


def get_all_rooms() -> List[Dict]:
    """
    Returns list of dicts:
    {
      "id": room_id,
      "number": room_number,
      "type": type,
      "status": status,
      "price": price,
      "floor": floor
    }
    """
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT room_id, room_number, type, status, price, floor
        FROM rooms
        ORDER BY floor, room_number
        """
    )
    rows = cur.fetchall()
    conn.close()

    rooms = []
    for r in rows:
        rooms.append(
            {
                "id": r[0],
                "number": r[1],
                "type": r[2],
                "status": r[3],
                "price": r[4],
                "floor": r[5],
            }
        )
    return rooms
