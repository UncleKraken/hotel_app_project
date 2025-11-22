# ui/maintenance_ui.py

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Dict

import customtkinter as ctk
from tkinter import ttk, messagebox

from backend import rooms as rooms_backend


@dataclass
class MaintenanceRequest:
    id: int
    room_id: int
    room_number: str
    title: str
    priority: str   # Low / Normal / High
    status: str     # Pending / In progress / Completed
    description: str
    created_at: str


class MaintenanceWindow(ctk.CTkToplevel):
    """Floating, centered maintenance panel (Option A)."""

    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent

        self.title("Maintenance requests")
        self.geometry("780x420")
        self.resizable(False, False)

        # data
        self.rooms: List[Dict] = rooms_backend.get_all_rooms()
        self.requests: List[MaintenanceRequest] = []
        self.next_id = 1

        self._build_ui()
        self._center_on_parent()
        self.grab_set()   # stay on top of receptionist
        self.focus()

    # ---------- helpers ----------

    def _center_on_parent(self):
        self.update_idletasks()
        if self.parent is not None:
            px = self.parent.winfo_rootx()
            py = self.parent.winfo_rooty()
            pw = self.parent.winfo_width()
            ph = self.parent.winfo_height()
        else:
            px = py = 0
            pw = self.winfo_screenwidth()
            ph = self.winfo_screenheight()

        w = self.winfo_reqwidth()
        h = self.winfo_reqheight()
        x = px + (pw - w) // 2
        y = py + (ph - h) // 2
        self.geometry(f"+{max(0, x)}+{max(0, y)}")

    # ---------- UI ----------

    def _build_ui(self):
        main = ctk.CTkFrame(self, corner_radius=12)
        main.pack(expand=True, fill="both", padx=10, pady=10)

        title = ctk.CTkLabel(
            main,
            text="Maintenance Panel",
            font=ctk.CTkFont(size=18, weight="bold"),
        )
        title.pack(pady=(8, 4))

        # table frame
        table_frame = ctk.CTkFrame(main, corner_radius=10)
        table_frame.pack(fill="both", expand=True, padx=8, pady=8)

        self.tree = ttk.Treeview(
            table_frame,
            columns=("id", "room", "title", "priority", "status", "created"),
            show="headings",
            height=10,
        )
        self.tree.pack(side="left", fill="both", expand=True, padx=(6, 0), pady=6)

        # scrollbar
        vs = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        vs.pack(side="right", fill="y", pady=6)
        self.tree.configure(yscrollcommand=vs.set)

        # headings
        self.tree.heading("id", text="ID")
        self.tree.heading("room", text="Room")
        self.tree.heading("title", text="Title")
        self.tree.heading("priority", text="Priority")
        self.tree.heading("status", text="Status")
        self.tree.heading("created", text="Created")

        self.tree.column("id", width=40, anchor="center")
        self.tree.column("room", width=70, anchor="center")
        self.tree.column("title", width=220, anchor="w")
        self.tree.column("priority", width=80, anchor="center")
        self.tree.column("status", width=100, anchor="center")
        self.tree.column("created", width=150, anchor="center")

        # row colors
        style = ttk.Style(self)
        style.configure("Treeview", rowheight=26)

        self.tree.tag_configure("Pending", background="#FFE79A")
        self.tree.tag_configure("In progress", background="#FFC27A")
        self.tree.tag_configure("Completed", background="#C1E9B5")

        # buttons
        btns = ctk.CTkFrame(main)
        btns.pack(fill="x", pady=(4, 2))

        ctk.CTkButton(
            btns, text="Add request", width=140, command=self._open_add_dialog
        ).pack(side="left", padx=6, pady=4)

        ctk.CTkButton(
            btns,
            text="Mark in progress",
            width=140,
            fg_color="#FFA94D",
            hover_color="#E08624",
            command=lambda: self._change_status("In progress"),
        ).pack(side="left", padx=6, pady=4)

        ctk.CTkButton(
            btns,
            text="Mark completed",
            width=140,
            fg_color="#37B24D",
            hover_color="#2B8A3E",
            command=lambda: self._change_status("Completed"),
        ).pack(side="left", padx=6, pady=4)

        ctk.CTkButton(
            btns,
            text="Close",
            width=100,
            fg_color="#888888",
            hover_color="#666666",
            command=self.destroy,
        ).pack(side="right", padx=6, pady=4)

        self._refresh_table()

    # ---------- data + table ----------

    def _refresh_table(self):
        # clear
        for iid in self.tree.get_children():
            self.tree.delete(iid)

        # refill
        for req in self.requests:
            self.tree.insert(
                "",
                "end",
                values=(
                    req.id,
                    req.room_number,
                    req.title,
                    req.priority,
                    req.status,
                    req.created_at,
                ),
                tags=(req.status,),
            )

    def _get_selected_request(self) -> Optional[MaintenanceRequest]:
        sel = self.tree.selection()
        if not sel:
            return None
        iid = sel[0]
        values = self.tree.item(iid, "values")
        if not values:
            return None
        rid = int(values[0])
        for r in self.requests:
            if r.id == rid:
                return r
        return None

    # ---------- actions ----------

    def _open_add_dialog(self):
        win = ctk.CTkToplevel(self)
        win.title("New maintenance request")
        win.geometry("420x360")
        win.grab_set()

        self._center_child(win)

        ctk.CTkLabel(
            win,
            text="Create maintenance request",
            font=ctk.CTkFont(size=15, weight="bold"),
        ).pack(pady=(10, 4))

        body = ctk.CTkFrame(win)
        body.pack(fill="both", expand=True, padx=10, pady=8)

        # room selector
        row_room = ctk.CTkFrame(body)
        row_room.pack(fill="x", pady=4)
        ctk.CTkLabel(row_room, text="Room:", width=90, anchor="e").pack(
            side="left", padx=4
        )

        room_names = [f"{r['number']} – {r['type']}" for r in self.rooms]
        self._room_var = ctk.StringVar(value=room_names[0] if room_names else "")
        room_menu = ctk.CTkOptionMenu(
            row_room, values=room_names, variable=self._room_var, width=220
        )
        room_menu.pack(side="left", padx=4)

        # title
        row_title = ctk.CTkFrame(body)
        row_title.pack(fill="x", pady=4)
        ctk.CTkLabel(row_title, text="Title:", width=90, anchor="e").pack(
            side="left", padx=4
        )
        e_title = ctk.CTkEntry(row_title, width=230, placeholder_text="Ex: AC not working")
        e_title.pack(side="left", padx=4)

        # priority
        row_prio = ctk.CTkFrame(body)
        row_prio.pack(fill="x", pady=4)
        ctk.CTkLabel(row_prio, text="Priority:", width=90, anchor="e").pack(
            side="left", padx=4
        )
        prio_var = ctk.StringVar(value="Normal")
        prio_menu = ctk.CTkOptionMenu(
            row_prio,
            values=["Low", "Normal", "High"],
            variable=prio_var,
            width=120,
        )
        prio_menu.pack(side="left", padx=4)

        # description
        row_desc = ctk.CTkFrame(body)
        row_desc.pack(fill="both", expand=True, pady=4)
        ctk.CTkLabel(row_desc, text="Description:", width=90, anchor="ne").pack(
            side="left", padx=4, pady=4
        )
        t_desc = ctk.CTkTextbox(row_desc, width=230, height=140)
        t_desc.pack(side="left", padx=4, pady=4)

        btns = ctk.CTkFrame(win)
        btns.pack(pady=8)

        def save():
            title_text = e_title.get().strip()
            if not title_text:
                messagebox.showwarning("Missing", "Please add a short title.")
                return

            if not self.rooms:
                messagebox.showerror("No rooms", "No rooms found in database.")
                return

            room_label = self._room_var.get()
            # find selected room
            room = None
            for r in self.rooms:
                label = f"{r['number']} – {r['type']}"
                if label == room_label:
                    room = r
                    break
            if room is None:
                room = self.rooms[0]

            req = MaintenanceRequest(
                id=self.next_id,
                room_id=room["id"],
                room_number=room["number"],
                title=title_text,
                priority=prio_var.get(),
                status="Pending",
                description=t_desc.get("1.0", "end").strip(),
                created_at=datetime.now().strftime("%Y-%m-%d %H:%M"),
            )
            self.next_id += 1
            self.requests.append(req)
            self._refresh_table()
            win.destroy()

        ctk.CTkButton(btns, text="Save", width=130, command=save).pack(
            side="left", padx=6
        )
        ctk.CTkButton(
            btns,
            text="Cancel",
            width=100,
            fg_color="#888888",
            hover_color="#666666",
            command=win.destroy,
        ).pack(side="left", padx=6)

    def _center_child(self, win):
        self.update_idletasks()
        win.update_idletasks()
        px = self.winfo_rootx()
        py = self.winfo_rooty()
        pw = self.winfo_width()
        ph = self.winfo_height()
        w = win.winfo_reqwidth()
        h = win.winfo_reqheight()
        x = px + (pw - w) // 2
        y = py + (ph - h) // 2
        win.geometry(f"+{max(0, x)}+{max(0, y)}")

    def _change_status(self, new_status: str):
        req = self._get_selected_request()
        if not req:
            messagebox.showinfo("No selection", "Please select a request first.")
            return

        req.status = new_status
        self._refresh_table()
