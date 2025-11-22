# ui/cleaning.py

import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional

import customtkinter as ctk
from tkinter import messagebox
from datetime import datetime

# ---------- COLORS / CONSTANTS ----------

COLOR_BG = "#E6E7EA"
COLOR_HEADER_BAR = "#28D3E3"
COLOR_MAIN_CARD = "#D9D9D9"
COLOR_ROOMS_COLUMN = "#FACC15"  # yellow

STATUS_CONFIG = {
    "Clean": {
        "bg": "#16A34A",   # green
        "fg": "white",
    },
    "Needs Cleaning": {
        "bg": "#DC2626",   # red
        "fg": "white",
    },
    "Occupied": {
        "bg": "#F97316",   # orange
        "fg": "black",
    },
}
STATUS_ORDER = ["Clean", "Needs Cleaning", "Occupied"]


@dataclass
class RoomState:
    number: int
    status: str = "Needs Cleaning"
    cleaner: str = ""
    note: str = ""


class CleaningWindow(ctk.CTkToplevel):
    """
    Housekeeping / Cleaning service UI.

    - Scrollable list of rooms
    - Each row: yellow room cell + status + cleaner + note
    - Status button cycles: Clean / Needs Cleaning / Occupied
    - Management tab: simple summary per cleaning staff
    """

    def __init__(self, parent=None, user: Optional[Dict] = None):
        super().__init__()

        # Make modal over parent (like your other windows)
        self.parent = parent
        if parent is not None:
            self.transient(parent)
            self.grab_set()
        self.focus()

        self.user = user or {"username": "housekeeping"}

        self.title("InnKeeper • Cleaning Service")
        self.geometry("1400x800")
        self.minsize(1100, 650)
        ctk.set_appearance_mode("light")
        self.configure(fg_color=COLOR_BG)

        # staff demo data ---------------------------------
        self.cleaners: List[str] = [
            "Cleaning Lady 1",
            "Cleaning Lady 2",
            "Cleaning Lady 3",
            "Cleaning Lady 4",
            "Cleaning Lady 5",
        ]

        # Rooms matching Receptionist / DB:
        # 101–106, 201–206, 301–306, 401–406
        room_numbers: List[int] = []
        for floor in range(1, 5):
            base = floor * 100
            for r in range(1, 7):
                room_numbers.append(base + r)

        self.rooms: Dict[int, RoomState] = {}
        for idx, num in enumerate(room_numbers):
            self.rooms[num] = RoomState(
                number=num,
                status="Needs Cleaning" if idx % 3 != 0 else "Clean",
                cleaner=self.cleaners[idx % len(self.cleaners)],
                note="Client is present" if num == 104 else "",
            )

        # references to row widgets so we can refresh them
        self._row_widgets: Dict[int, Dict[str, ctk.CTkBaseClass]] = {}

        # floor / room view flag (visual only for now)
        self.floor_view: bool = True

        # ---------- BUILD UI ----------
        self._build_layout()
        self.protocol("WM_DELETE_WINDOW", self.on_window_close)

    # ---------- LAYOUT ----------

    def _build_layout(self):
        # Top bar
        top_bar = ctk.CTkFrame(self, fg_color="#D4D4D4", height=60)
        top_bar.pack(side="top", fill="x")

        ctk.CTkLabel(
            top_bar,
            text="Housekeeping Overview",
            font=ctk.CTkFont(size=18, weight="bold"),
            anchor="w",
        ).pack(side="left", padx=20, pady=10)

        ctk.CTkButton(
            top_bar,
            text="Exit",
            width=80,
            fg_color="#333333",
            hover_color="#111111",
            command=self.on_window_close,
        ).pack(side="right", padx=16, pady=10)

        # Main tabs
        main = ctk.CTkTabview(self, fg_color=COLOR_BG, width=1360, height=720)
        main.pack(expand=True, fill="both", padx=10, pady=10)

        self.overview_tab = main.add("Overview")
        self.management_tab = main.add("Management")

        self._build_overview_tab()
        self._build_management_tab()

        # initial data fill
        self._refresh_room_rows()
        self._refresh_management_summary()

    # ---------- OVERVIEW TAB ----------

    def _build_overview_tab(self):

        # day header – real date from PC
        day_frame = ctk.CTkFrame(self.overview_tab, fg_color=COLOR_HEADER_BAR, corner_radius=50)
        day_frame.pack(fill="x", padx=60, pady=(4, 10))

        current_day = datetime.now().strftime("%A %d %B %Y")
        ctk.CTkLabel(
            day_frame,
            text=current_day,
            font=ctk.CTkFont(size=16, weight="bold"),
        ).pack(padx=10, pady=6)

        # big card
        card = ctk.CTkFrame(self.overview_tab, fg_color=COLOR_MAIN_CARD, corner_radius=30)
        card.pack(fill="both", expand=True, padx=40, pady=(6, 6))

        # --- floor/room toggle pill (small yellow circle with arrow) ---
        toggle_frame = ctk.CTkFrame(card, fg_color=COLOR_MAIN_CARD)
        toggle_frame.pack(anchor="w", padx=40, pady=(16, 0))

        self.toggle_btn = ctk.CTkButton(
            toggle_frame,
            text="↕",
            width=36,
            height=36,
            corner_radius=18,
            fg_color=COLOR_ROOMS_COLUMN,
            hover_color="#FBBF24",
            text_color="black",
            command=self._toggle_floor_view,
        )
        self.toggle_btn.pack(side="left", padx=(0, 10))

        self.toggle_label = ctk.CTkLabel(
            toggle_frame,
            text="Floor View",
            font=ctk.CTkFont(size=13, weight="bold"),
        )
        self.toggle_label.pack(side="left")

        # headers row inside card
        header_bar = ctk.CTkFrame(card, fg_color=COLOR_HEADER_BAR, corner_radius=40)
        header_bar.pack(fill="x", padx=40, pady=(10, 10))

        # EMPTY space for rooms column so that "Status" aligns correctly
        ctk.CTkLabel(
            header_bar,
            text="",
            width=80,
        ).pack(side="left", padx=(15, 5), pady=8)

        ctk.CTkLabel(
            header_bar,
            text="Status",
            width=150,
            font=ctk.CTkFont(size=15, weight="bold"),
        ).pack(side="left", padx=5, pady=8)

        ctk.CTkLabel(
            header_bar,
            text="Cleaning Staff in Charge",
            width=350,
            font=ctk.CTkFont(size=15, weight="bold"),
        ).pack(side="left", padx=5, pady=8)

        ctk.CTkLabel(
            header_bar,
            text="Notes by Receptionist",
            width=350,
            font=ctk.CTkFont(size=15, weight="bold"),
        ).pack(side="left", padx=5, pady=8)

        # scrollable list
        list_outer = ctk.CTkFrame(card, fg_color=COLOR_MAIN_CARD)
        list_outer.pack(fill="both", expand=True, padx=20, pady=(0, 10))

        self.rooms_scroll = ctk.CTkScrollableFrame(
            list_outer,
            fg_color=COLOR_MAIN_CARD,
        )
        self.rooms_scroll.pack(fill="both", expand=True, padx=10, pady=10)

    def _refresh_room_rows(self):
        # clear previous rows
        for child in self.rooms_scroll.winfo_children():
            child.destroy()
        self._row_widgets.clear()

        # one row per room
        for room_num in sorted(self.rooms.keys()):
            state = self.rooms[room_num]

            row = ctk.CTkFrame(self.rooms_scroll, fg_color=COLOR_MAIN_CARD, corner_radius=0)
            row.pack(fill="x", padx=0, pady=0)

            # yellow room number cell (looks like part of a big yellow column)
            room_lbl = ctk.CTkLabel(
                row,
                text=str(room_num),
                width=80,
                height=34,
                fg_color=COLOR_ROOMS_COLUMN,
                text_color="black",
                anchor="center",
                font=ctk.CTkFont(size=14, weight="bold"),
            )
            room_lbl.pack(side="left", padx=(40, 10), pady=1)

            # status button
            status_btn = ctk.CTkButton(
                row,
                text=state.status,
                width=140,
                height=32,
                corner_radius=20,
                command=lambda n=room_num: self._cycle_status(n),
            )
            status_btn.pack(side="left", padx=(0, 10), pady=3)

            # cleaner dropdown
            cleaner_var = ctk.StringVar(value=state.cleaner or self.cleaners[0])
            cleaner_menu = ctk.CTkOptionMenu(
                row,
                values=self.cleaners,
                variable=cleaner_var,
                width=250,
                command=lambda _v, n=room_num, v=cleaner_var: self._set_cleaner(n, v.get()),
            )
            cleaner_menu.pack(side="left", padx=(0, 10), pady=3)

            # note entry
            note_entry = ctk.CTkEntry(
                row,
                width=380,
                placeholder_text="Note…",
            )
            note_entry.insert(0, state.note)
            note_entry.pack(side="left", padx=(0, 10), pady=3)

            def on_note_focus_out(event, n=room_num, entry=note_entry):
                self.rooms[n].note = entry.get().strip()

            note_entry.bind("<FocusOut>", on_note_focus_out)

            # store refs & apply status color
            self._row_widgets[room_num] = {
                "status_btn": status_btn,
                "cleaner_var": cleaner_var,
                "note_entry": note_entry,
            }
            self._apply_status_style(room_num)

    # ---------- MANAGEMENT TAB ----------

    def _build_management_tab(self):
        wrapper = ctk.CTkFrame(self.management_tab, fg_color=COLOR_BG)
        wrapper.pack(fill="both", expand=True, padx=40, pady=40)

        ctk.CTkLabel(
            wrapper,
            text="Cleaning Management",
            font=ctk.CTkFont(size=20, weight="bold"),
        ).pack(anchor="w", pady=(0, 10))

        ctk.CTkLabel(
            wrapper,
            text="Summary of assigned rooms per cleaning staff (demo / prototype).",
            font=ctk.CTkFont(size=13),
        ).pack(anchor="w", pady=(0, 20))

        self.summary_frame = ctk.CTkFrame(wrapper, fg_color="#F3F4F6", corner_radius=20)
        self.summary_frame.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(
            wrapper,
            text="You can change staff and statuses from the Overview tab.",
            font=ctk.CTkFont(size=12, slant="italic"),
            text_color="#4B5563",
        ).pack(anchor="w", pady=(10, 0))

    def _refresh_management_summary(self):
        for child in self.summary_frame.winfo_children():
            child.destroy()

        counts: Dict[str, Dict[str, int]] = {
            c: {"Clean": 0, "Needs Cleaning": 0, "Occupied": 0} for c in self.cleaners
        }

        for r in self.rooms.values():
            cleaner = r.cleaner or self.cleaners[0]
            if cleaner not in counts:
                counts[cleaner] = {"Clean": 0, "Needs Cleaning": 0, "Occupied": 0}
            if r.status in counts[cleaner]:
                counts[cleaner][r.status] += 1

        # header
        header = ctk.CTkFrame(self.summary_frame, fg_color="#E5E7EB", corner_radius=10)
        header.pack(fill="x", padx=12, pady=(12, 4))

        def h_label(txt, w):
            ctk.CTkLabel(
                header,
                text=txt,
                width=w,
                font=ctk.CTkFont(size=14, weight="bold"),
            ).pack(side="left", padx=4, pady=4)

        h_label("Cleaner", 220)
        h_label("Clean", 80)
        h_label("Needs Cleaning", 130)
        h_label("Occupied", 100)
        h_label("Total Rooms", 110)

        # rows
        for cleaner in self.cleaners:
            row_counts = counts.get(cleaner, {"Clean": 0, "Needs Cleaning": 0, "Occupied": 0})
            total = row_counts["Clean"] + row_counts["Needs Cleaning"] + row_counts["Occupied"]

            row = ctk.CTkFrame(self.summary_frame, fg_color="white", corner_radius=10)
            row.pack(fill="x", padx=12, pady=3)

            def lbl(text, w):
                ctk.CTkLabel(row, text=text, width=w).pack(side="left", padx=4, pady=4)

            lbl(cleaner, 220)
            lbl(str(row_counts["Clean"]), 80)
            lbl(str(row_counts["Needs Cleaning"]), 130)
            lbl(str(row_counts["Occupied"]), 100)
            lbl(str(total), 110)

    # ---------- STATUS / CLEANER HANDLERS ----------

    def _cycle_status(self, room_num: int):
        state = self.rooms[room_num]
        idx = STATUS_ORDER.index(state.status) if state.status in STATUS_ORDER else 0
        idx = (idx + 1) % len(STATUS_ORDER)
        state.status = STATUS_ORDER[idx]
        self._apply_status_style(room_num)
        self._refresh_management_summary()

    def _set_cleaner(self, room_num: int, cleaner: str):
        self.rooms[room_num].cleaner = cleaner
        self._refresh_management_summary()

    def _apply_status_style(self, room_num: int):
        state = self.rooms[room_num]
        cfg = STATUS_CONFIG.get(state.status, STATUS_CONFIG["Needs Cleaning"])
        btn = self._row_widgets[room_num]["status_btn"]
        btn.configure(
            text=state.status,
            fg_color=cfg["bg"],
            hover_color=cfg["bg"],
            text_color=cfg["fg"],
        )

    # ---------- FLOOR VIEW TOGGLE (visual only) ----------

    def _toggle_floor_view(self):
        self.floor_view = not self.floor_view
        self.toggle_label.configure(text="Floor View" if self.floor_view else "Room View")

    # ---------- MISC ----------

    def on_window_close(self):
        self.destroy()
        if self.parent is not None:
            try:
                self.parent.deiconify()
            except Exception:
                pass


# Optional standalone test
if __name__ == "__main__":
    ctk.set_appearance_mode("light")
    app = ctk.CTk()
    app.title("InnKeeper Demo Launcher")
    app.geometry("400x200")

    def open_cleaning():
        CleaningWindow(parent=app)

    ctk.CTkButton(app, text="Open Cleaning Window", command=open_cleaning).pack(pady=40)
    app.mainloop()
