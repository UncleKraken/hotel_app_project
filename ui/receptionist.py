# ui/receptionist.py


import calendar
from dataclasses import dataclass
from datetime import date, timedelta
from typing import List, Dict, Optional

import customtkinter as ctk
from tkinter import messagebox, TclError
from PIL import Image

from backend import rooms as rooms_backend
from ui.clients import ClientsWindow

# ----------------- COLORS -----------------
COLOR_BG = "#E6E7EA"
COLOR_TIMELINE_BG = "#D0D1D5"
COLOR_DAYS_BAR = "#21D4E3"
COLOR_ROOM_COL = "#FFD95E"

COLOR_RESERVED = "#3366FF"
COLOR_PRESENT = "#1EBE57"
COLOR_CLEANING = "#A6744A"
COLOR_FINISHED = "#B7BDC8"      # after cleaned – finished stay (history)
COLOR_MAINTENANCE = "#F03737"
COLOR_AVAILABLE = "#EDEFF2"


@dataclass
class Reservation:
    id: int
    room_id: int
    guest_name: str
    start: date
    end: date       # exclusive
    adults: int
    children: int
    phone: str
    email: str
    notes: str
    status: str     # reserved / present / cleaning / finished / maintenance


class ReceptionistWindow(ctk.CTkToplevel):
    """Main receptionist timeline window (child of LoginWindow)."""

    def __init__(self, parent=None, user: Optional[Dict] = None):
        super().__init__(parent)

        self.parent = parent
        self.user = user or {"username": "Unknown"}

        self.title(f"InnKeeper • Receptionist ({self.user['username']})")
        self.geometry("1400x820")
        self.minsize(1100, 650)

        today = date.today()
        self.year = today.year
        self.month = today.month

        self.day_width = 36
        self.row_height = 34
        self.room_col_width = 130
        self.header_h = 38
        self.day_label_h = 26
        self.grid_top = self.header_h + self.day_label_h

        self.show_room_numbers = True
        self.zoom_after_id = None
        self._last_width = None
        self._click_suppressed = False

        self.rooms: List[Dict] = rooms_backend.get_all_rooms()
        self.reservations: List[Reservation] = []
        self.next_res_id = 1

        self.tooltip_label: Optional[ctk.CTkLabel] = None
        self.canvas: Optional[ctk.CTkCanvas] = None
        self.v_scroll = None
        self.h_scroll = None

        self._build_layout()
        self._redraw_canvas()

    # ---------- UTILS ----------

    def _center_toplevel(self, win: ctk.CTkToplevel):
        self.update_idletasks()
        win.update_idletasks()
        w = win.winfo_reqwidth()
        h = win.winfo_reqheight()
        x = self.winfo_rootx() + max(0, (self.winfo_width() - w) // 2)
        y = self.winfo_rooty() + max(0, (self.winfo_height() - h) // 2 - 20)
        win.geometry(f"{w}x{h}+{x}+{y}")

    # ---------- LAYOUT ----------

    def _build_layout(self):
        self.configure(fg_color=COLOR_BG)

        # -------------------- TOP TOOLBAR (HOME ICONS) --------------------
        toolbar = ctk.CTkFrame(self, height=70, corner_radius=0, fg_color="#DDDEE2")
        toolbar.pack(side="top", fill="x")

        self.tooltip_label = ctk.CTkLabel(
            self,
            text="",
            fg_color="#2C2C2C",
            text_color="white",
            corner_radius=6,
            padx=8,
            pady=2,
        )

        # Icons row aligned from LEFT to RIGHT
        icons_frame = ctk.CTkFrame(toolbar, fg_color="#DDDEE2")
        icons_frame.pack(side="left", padx=12, pady=(6, 4))

        def make_icon_button(text: str, tooltip: str, cmd):
            btn = ctk.CTkButton(
                icons_frame,
                text=text,
                width=90,
                height=50,
                fg_color="#2B2B2B",
                hover_color="#4A4A4A",
                corner_radius=16,
                command=cmd,
                font=ctk.CTkFont(size=14, weight="bold"),
            )
            btn.pack(side="left", padx=8)

            def enter(e):
                self.tooltip_label.configure(text=tooltip)
                self.tooltip_label.place(
                    x=e.widget.winfo_rootx() - self.winfo_rootx(),
                    y=e.widget.winfo_rooty() - self.winfo_rooty() + 55,
                )

            def leave(e):
                self.tooltip_label.place_forget()

            btn.bind("<Enter>", enter)
            btn.bind("<Leave>", leave)

        # mapping (text is like your icons: clients / maintenance / reports / toolbox / logout)
        make_icon_button("🪪", "Client register", self._open_clients)
        make_icon_button("🔧", "Maintenance", self._open_maintenance)
        make_icon_button("📝", "Reception reports", self._open_reports)
        make_icon_button("🧰", "Reception toolbox / settings", self._open_toolbox)
        make_icon_button("⏻", "Logout", self._logout)

        # -------------------- MONTH BAR (CENTERED) --------------------
        month_bar = ctk.CTkFrame(self, height=55, corner_radius=0, fg_color="#DDDEE2")
        month_bar.pack(side="top", fill="x")

        month_container = ctk.CTkFrame(month_bar, fg_color="#DDDEE2")
        month_container.pack(expand=True)

        prev_btn = ctk.CTkButton(
            month_container,
            text="◀",
            width=45,
            height=35,
            fg_color="#3A84C4",
            hover_color="#2A6DA8",
            command=self._prev_month,
        )
        prev_btn.pack(side="left", padx=6, pady=8)

        self.month_btn = ctk.CTkButton(
            month_container,
            text="",
            width=320,
            height=35,
            fg_color=COLOR_DAYS_BAR,
            hover_color="#0FB5C6",
            corner_radius=25,
            command=self._open_jump_to,
        )
        self.month_btn.pack(side="left", padx=10, pady=8)

        next_btn = ctk.CTkButton(
            month_container,
            text="▶",
            width=45,
            height=35,
            fg_color="#3A84C4",
            hover_color="#2A6DA8",
            command=self._next_month,
        )
        next_btn.pack(side="left", padx=6, pady=8)

        # -------------------- ZOOM BAR --------------------
        control_bar = ctk.CTkFrame(self, height=40, corner_radius=0, fg_color="#DDDEE2")
        control_bar.pack(side="top", fill="x")

        ctk.CTkLabel(control_bar, text="Zoom days:").pack(side="left", padx=10)

        self.zoom_slider = ctk.CTkSlider(
            control_bar,
            from_=24,
            to=64,
            number_of_steps=40,
            width=180,
            command=self._on_zoom_change,
        )
        self.zoom_slider.set(self.day_width)
        self.zoom_slider.pack(side="left", padx=8)

        # -------------------- MAIN CANVAS --------------------
        main = ctk.CTkFrame(self, corner_radius=0, fg_color=COLOR_BG)
        main.pack(side="top", fill="both", expand=True, padx=8, pady=(4, 6))

        self.canvas = ctk.CTkCanvas(
            main,
            bg=COLOR_TIMELINE_BG,
            highlightthickness=0,
        )
        self.canvas.grid(row=0, column=0, sticky="nsew")

        self.v_scroll = ctk.CTkScrollbar(main, orientation="vertical", command=self.canvas.yview)
        self.v_scroll.grid(row=0, column=1, sticky="ns")

        self.h_scroll = ctk.CTkScrollbar(main, orientation="horizontal", command=self.canvas.xview)
        self.h_scroll.grid(row=1, column=0, sticky="ew")

        self.canvas.configure(xscrollcommand=self.h_scroll.set, yscrollcommand=self.v_scroll.set)

        main.rowconfigure(0, weight=1)
        main.columnconfigure(0, weight=1)

        self.canvas.bind("<Button-1>", self._on_canvas_click)
        self.bind("<Configure>", self._on_window_resize)

    # ---------- NAV ----------

    def _update_month_label(self):
        self.month_btn.configure(text=f"{calendar.month_name[self.month]} {self.year}")

    def _prev_month(self):
        self.month -= 1
        if self.month < 1:
            self.month = 12
            self.year -= 1
        self._redraw_canvas()

    def _next_month(self):
        self.month += 1
        if self.month > 12:
            self.month = 1
            self.year += 1
        self._redraw_canvas()

    # ---------- JUMP TO DATE ----------

    def _open_jump_to(self):
        win = ctk.CTkToplevel(self)
        win.title("Jump to date")
        win.grab_set()

        ctk.CTkLabel(win, text="Day").pack(pady=(10, 2))
        days = [str(d) for d in range(1, 32)]
        dvar = ctk.StringVar(value="1")
        ctk.CTkOptionMenu(win, values=days, variable=dvar, width=80).pack(pady=4)

        ctk.CTkLabel(win, text="Month").pack(pady=(8, 2))
        months = [calendar.month_name[m] for m in range(1, 13)]
        mvar = ctk.StringVar(value=calendar.month_name[self.month])
        ctk.CTkOptionMenu(win, values=months, variable=mvar, width=150).pack(pady=4)

        ctk.CTkLabel(win, text="Year").pack(pady=(8, 2))
        yvar = ctk.StringVar(value=str(self.year))
        yentry = ctk.CTkEntry(win, textvariable=yvar, width=120)
        yentry.pack(pady=4)

        def go():
            try:
                day = int(dvar.get())
                year = int(yvar.get())
                month = months.index(mvar.get()) + 1
                _ = date(year, month, day)
                self.year = year
                self.month = month
                win.destroy()
                self._redraw_canvas()
            except Exception:
                messagebox.showerror("Invalid", "Invalid date. Check Day / Month / Year.")

        ctk.CTkButton(win, text="Go", width=120, command=go).pack(pady=12)
        self._center_toplevel(win)

    # ---------- ZOOM / RESIZE ----------

    def _on_zoom_change(self, val):
        self.day_width = int(float(val))
        if self.zoom_after_id:
            try:
                self.after_cancel(self.zoom_after_id)
            except Exception:
                pass
        self.zoom_after_id = self.after(120, self._redraw_canvas)

    def _on_window_resize(self, event):
        if event.widget is not self:
            return
        if self._last_width and abs(self._last_width - event.width) < 20:
            return
        self._last_width = event.width
        self._redraw_canvas()

    # ---------- DRAW GRID + RESERVATIONS ----------

    def _redraw_canvas(self):
        if not self.canvas:
            return

        self._update_month_label()
        self.canvas.delete("all")

        days_in_month = calendar.monthrange(self.year, self.month)[1]
        month_start = date(self.year, self.month, 1)

        visible_w = max(self.winfo_width() - 40, 900)
        total_days_width = days_in_month * self.day_width
        total_width = max(self.room_col_width + total_days_width + 40, visible_w)
        total_height = self.grid_top + len(self.rooms) * self.row_height + 60

        # background
        self.canvas.create_rectangle(
            0, 0, total_width, total_height, fill=COLOR_TIMELINE_BG, outline=""
        )

        # DAYS title bar
        self.canvas.create_rectangle(
            self.room_col_width,
            8,
            total_width - 10,
            self.header_h,
            fill=COLOR_DAYS_BAR,
            outline="",
        )
        self.canvas.create_text(
            (self.room_col_width + total_width - 10) // 2,
            self.header_h // 2,
            text="Days",
            font=("Arial", 12, "bold"),
            fill="black",
        )

        # day grid
        for d in range(days_in_month):
            x = self.room_col_width + d * self.day_width
            self.canvas.create_line(
                x, self.grid_top, x, total_height, fill="#B0B3BA", width=1
            )
            self.canvas.create_text(
                x + self.day_width / 2,
                self.header_h + self.day_label_h / 2,
                text=str(d + 1),
                font=("Arial", 10, "bold"),
                fill="black",
            )

        # horizontal line under labels
        self.canvas.create_line(
            self.room_col_width,
            self.grid_top,
            total_width,
            self.grid_top,
            fill="#8F939B",
        )

        # room column background
        self.canvas.create_rectangle(
            0,
            self.grid_top,
            self.room_col_width,
            total_height,
            fill=COLOR_ROOM_COL,
            outline="",
        )

        # big ⇅ toggle centered between room col and days bar
        def toggle_label(event=None):
            self.show_room_numbers = not self.show_room_numbers
            self._redraw_canvas()

        arrow_bg = self.canvas.create_oval(
            self.room_col_width / 2 - 16,
            self.grid_top - 26,
            self.room_col_width / 2 + 16,
            self.grid_top - 2,
            fill="#FFC842",
            outline="#D6A932",
        )
        arrow_text = self.canvas.create_text(
            self.room_col_width / 2,
            self.grid_top - 14,
            text="⇅",
            font=("Arial", 18, "bold"),
        )
        self.canvas.tag_bind(arrow_bg, "<Button-1>", toggle_label)
        self.canvas.tag_bind(arrow_text, "<Button-1>", toggle_label)

        # room labels
        for idx, room in enumerate(self.rooms):
            y_top = self.grid_top + idx * self.row_height
            y_bottom = y_top + self.row_height

            label = room["number"] if self.show_room_numbers else room["type"]
            self.canvas.create_text(
                12,
                (y_top + y_bottom) / 2,
                anchor="w",
                text=label,
                font=("Arial", 10, "bold"),
                fill="black",
            )

            self.canvas.create_line(
                0, y_bottom, total_width, y_bottom, fill="#C2C4CC", width=1
            )

        # reservations
        month_end = month_start + timedelta(days=days_in_month)
        for res in self.reservations:
            if res.end <= month_start or res.start >= month_end:
                continue

            start = max(res.start, month_start)
            end = min(res.end, month_end)
            start_offset = (start - month_start).days
            end_offset = (end - month_start).days
            span = max(1, end_offset - start_offset)

            try:
                idx = next(i for i, r in enumerate(self.rooms) if r["id"] == res.room_id)
            except StopIteration:
                continue

            y_top = self.grid_top + idx * self.row_height + 5
            y_bottom = y_top + self.row_height - 10
            x1 = self.room_col_width + start_offset * self.day_width + 2
            x2 = x1 + span * self.day_width - 4

            color = self._status_to_color(res.status)

            rect_id = self.canvas.create_rectangle(
                x1, y_top, x2, y_bottom, fill=color, outline=color
            )

            label = res.guest_name or "Reservation"
            if len(label) > 17:
                label = label[:16] + "…"

            text_id = self.canvas.create_text(
                (x1 + x2) / 2,
                (y_top + y_bottom) / 2,
                text=label,
                font=("Arial", 10, "bold"),
                fill="white",
            )

            def detail(event, rid=res.id):
                self._click_suppressed = True
                self.after(50, lambda: setattr(self, "_click_suppressed", False))
                self._open_reservation_detail(rid)

            self.canvas.tag_bind(rect_id, "<Button-1>", detail)
            self.canvas.tag_bind(text_id, "<Button-1>", detail)

        self.canvas.configure(scrollregion=(0, 0, total_width, total_height))

    # ---------- STATUS COLOR ----------

    def _status_to_color(self, status: str) -> str:
        s = (status or "").lower()
        if s == "present":
            return COLOR_PRESENT
        if s == "cleaning":
            return COLOR_CLEANING
        if s == "finished":
            return COLOR_FINISHED
        if s == "maintenance":
            return COLOR_MAINTENANCE
        if s == "reserved":
            return COLOR_RESERVED
        return COLOR_AVAILABLE

    # ---------- CLICK HANDLING ----------

    def _on_canvas_click(self, event):
        if self._click_suppressed:
            return

        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)

        days_in_month = calendar.monthrange(self.year, self.month)[1]
        month_start = date(self.year, self.month, 1)

        if x < self.room_col_width or y < self.grid_top:
            return

        day_index = int((x - self.room_col_width) // self.day_width)
        row_index = int((y - self.grid_top) // self.row_height)

        if day_index < 0 or day_index >= days_in_month:
            return
        if row_index < 0 or row_index >= len(self.rooms):
            return

        room = self.rooms[row_index]
        start_date = month_start + timedelta(days=day_index)

        self._open_new_reservation_popup(room, start_date)

    # ---------- NEW / EDIT RESERVATION POPUP ----------

    def _open_new_reservation_popup(self, room: Dict, start_date: date, existing: Reservation = None):
        is_edit = existing is not None

        win = ctk.CTkToplevel(self)
        title_txt = "Edit Reservation" if is_edit else "New Reservation"
        win.title(f"{title_txt} • Room {room['number']}")
        win.grab_set()

        ctk.CTkLabel(
            win,
            text=f"Room {room['number']} ({room['type']})",
            font=ctk.CTkFont(size=16, weight="bold"),
        ).pack(pady=(10, 4))

        body = ctk.CTkFrame(win)
        body.pack(fill="both", expand=True, padx=12, pady=8)

        # Start date
        row1 = ctk.CTkFrame(body)
        row1.pack(fill="x", pady=4)
        ctk.CTkLabel(row1, text="Start date (YYYY-MM-DD)", width=160, anchor="e").pack(
            side="left", padx=4
        )
        e_start = ctk.CTkEntry(row1, width=140)
        e_start.insert(0, (existing.start if is_edit else start_date).isoformat())
        e_start.pack(side="left", padx=4)

        # Nights
        row2 = ctk.CTkFrame(body)
        row2.pack(fill="x", pady=4)
        ctk.CTkLabel(row2, text="Nights", width=160, anchor="e").pack(
            side="left", padx=4
        )
        e_nights = ctk.CTkEntry(row2, width=80)
        if is_edit:
            nights = max(1, (existing.end - existing.start).days)
            e_nights.insert(0, str(nights))
        else:
            e_nights.insert(0, "1")
        e_nights.pack(side="left", padx=4)

        # Guest name
        row3 = ctk.CTkFrame(body)
        row3.pack(fill="x", pady=4)
        ctk.CTkLabel(row3, text="Guest Name", width=160, anchor="e").pack(
            side="left", padx=4
        )
        e_guest = ctk.CTkEntry(row3, width=200, placeholder_text="Name Surname")
        if is_edit:
            e_guest.insert(0, existing.guest_name)
        e_guest.pack(side="left", padx=4)

        # Adults / Children
        row4 = ctk.CTkFrame(body)
        row4.pack(fill="x", pady=4)
        ctk.CTkLabel(row4, text="Adults", width=80, anchor="e").pack(side="left", padx=(4, 2))
        e_adults = ctk.CTkEntry(row4, width=60)
        e_adults.insert(0, str(existing.adults if is_edit else 2))
        e_adults.pack(side="left", padx=2)

        ctk.CTkLabel(row4, text="Children", width=80, anchor="e").pack(side="left", padx=(12, 2))
        e_children = ctk.CTkEntry(row4, width=60)
        e_children.insert(0, str(existing.children if is_edit else 0))
        e_children.pack(side="left", padx=2)

        # Phone / Email
        row5 = ctk.CTkFrame(body)
        row5.pack(fill="x", pady=4)
        ctk.CTkLabel(row5, text="Phone", width=80, anchor="e").pack(side="left", padx=(4, 2))
        e_phone = ctk.CTkEntry(row5, width=120, placeholder_text="+355...")
        if is_edit:
            e_phone.insert(0, existing.phone)
        e_phone.pack(side="left", padx=2)

        ctk.CTkLabel(row5, text="Email", width=60, anchor="e").pack(side="left", padx=(12, 2))
        e_email = ctk.CTkEntry(row5, width=160, placeholder_text="name@email.com")
        if is_edit:
            e_email.insert(0, existing.email)
        e_email.pack(side="left", padx=2)

        # Notes
        row6 = ctk.CTkFrame(body)
        row6.pack(fill="both", expand=True, pady=4)
        ctk.CTkLabel(row6, text="Notes", width=80, anchor="ne").pack(
            side="left", padx=4, pady=4
        )
        t_notes = ctk.CTkTextbox(row6, width=260, height=120)
        if is_edit:
            t_notes.insert("1.0", existing.notes)
        t_notes.pack(side="left", padx=4, pady=4)

        btns = ctk.CTkFrame(win)
        btns.pack(pady=10)

        def save():
            try:
                start = date.fromisoformat(e_start.get().strip())
                nights_val = int(e_nights.get().strip() or "1")
                nights_val = max(1, nights_val)
                end = start + timedelta(days=nights_val)
            except Exception:
                messagebox.showerror("Invalid", "Please enter a valid date and nights.")
                return

            name = e_guest.get().strip()
            if not name:
                messagebox.showwarning("Missing", "Please enter guest name.")
                return

            try:
                adults = int(e_adults.get().strip() or "0")
                children = int(e_children.get().strip() or "0")
            except Exception:
                adults, children = 0, 0

            phone = e_phone.get().strip()
            email = e_email.get().strip()
            notes = t_notes.get("1.0", "end").strip()

            if is_edit:
                existing.start = start
                existing.end = end
                existing.guest_name = name
                existing.adults = adults
                existing.children = children
                existing.phone = phone
                existing.email = email
                existing.notes = notes
            else:
                res = Reservation(
                    id=self.next_res_id,
                    room_id=room["id"],
                    guest_name=name,
                    start=start,
                    end=end,
                    adults=adults,
                    children=children,
                    phone=phone,
                    email=email,
                    notes=notes,
                    status="reserved",
                )
                self.next_res_id += 1
                self.reservations.append(res)

            win.destroy()
            self._redraw_canvas()

        ctk.CTkButton(btns, text="Save", width=160, command=save).pack(side="left", padx=6)
        ctk.CTkButton(
            btns,
            text="Cancel",
            width=120,
            fg_color="#888888",
            hover_color="#666666",
            command=win.destroy,
        ).pack(side="left", padx=6)

        self._center_toplevel(win)

    # ---------- FIND RESERVATION ----------

    def _find_reservation(self, res_id: int) -> Optional[Reservation]:
        for r in self.reservations:
            if r.id == res_id:
                return r
        return None

    # ---------- RESERVATION DETAIL ----------

    def _open_reservation_detail(self, res_id: int):
        res = self._find_reservation(res_id)
        if not res:
            return

        win = ctk.CTkToplevel(self)
        win.title(f"Reservation #{res.id}")
        win.grab_set()

        ctk.CTkLabel(
            win,
            text=f"{res.guest_name}",
            font=ctk.CTkFont(size=16, weight="bold"),
        ).pack(pady=(10, 4))

        info = ctk.CTkFrame(win)
        info.pack(fill="x", padx=12, pady=4)

        def add_row(label, value):
            row = ctk.CTkFrame(info)
            row.pack(fill="x", pady=2)
            ctk.CTkLabel(row, text=f"{label}:", width=120, anchor="e").pack(side="left", padx=4)
            ctk.CTkLabel(row, text=value, anchor="w").pack(side="left", padx=4)

        room = next(r for r in self.rooms if r["id"] == res.room_id)
        add_row("Room", f"{room['number']} ({room['type']})")
        add_row("Start", res.start.isoformat())
        add_row("End", res.end.isoformat())
        add_row("Status", res.status.capitalize())
        add_row("Adults", str(res.adults))
        add_row("Children", str(res.children))
        add_row("Phone", res.phone)
        add_row("Email", res.email)

        notes_frame = ctk.CTkFrame(win)
        notes_frame.pack(fill="both", expand=True, padx=12, pady=4)
        ctk.CTkLabel(notes_frame, text="Notes").pack(anchor="w", padx=4)
        txt = ctk.CTkTextbox(notes_frame, height=120)
        txt.pack(fill="both", expand=True, padx=4, pady=4)
        txt.insert("1.0", res.notes)
        txt.configure(state="disabled")

        btns = ctk.CTkFrame(win)
        btns.pack(pady=(6, 12))

        def do_edit():
            win.destroy()
            room_info = next(r for r in self.rooms if r["id"] == res.room_id)
            self._open_new_reservation_popup(room_info, res.start, existing=res)

        def do_check_in():
            res.status = "present"
            self._redraw_canvas()
            win.destroy()

        def do_cancel():
            if not messagebox.askyesno(
                "Cancel reservation",
                "Are you sure you want to cancel this reservation?",
            ):
                return
            self.reservations = [r for r in self.reservations if r.id != res.id]
            self._redraw_canvas()
            win.destroy()

        def do_check_out():
            res.status = "cleaning"
            self._redraw_canvas()
            win.destroy()

        def do_mark_cleaned():
            res.status = "finished"
            self._redraw_canvas()
            win.destroy()

        # Buttons depend on status
        if res.status == "reserved":
            ctk.CTkButton(
                btns,
                text="Edit",
                width=100,
                fg_color="#4A90E2",
                hover_color="#3575BF",
                command=do_edit,
            ).pack(side="left", padx=6)

            ctk.CTkButton(
                btns,
                text="Check In",
                width=100,
                fg_color=COLOR_PRESENT,
                hover_color="#179846",
                command=do_check_in,
            ).pack(side="left", padx=6)

            ctk.CTkButton(
                btns,
                text="Cancel Reservation",
                width=150,
                fg_color=COLOR_MAINTENANCE,
                hover_color="#C02424",
                command=do_cancel,
            ).pack(side="left", padx=6)

        elif res.status == "present":
            ctk.CTkButton(
                btns,
                text="Edit",
                width=120,
                fg_color="#4A90E2",
                hover_color="#3575BF",
                command=do_edit,
            ).pack(side="left", padx=6)

            ctk.CTkButton(
                btns,
                text="Check Out",
                width=120,
                fg_color=COLOR_CLEANING,
                hover_color="#845231",
                command=do_check_out,
            ).pack(side="left", padx=6)

        elif res.status == "cleaning":
            ctk.CTkButton(
                btns,
                text="Mark Cleaned",
                width=140,
                fg_color=COLOR_FINISHED,
                hover_color="#9AA2AD",
                command=do_mark_cleaned,
            ).pack(side="left", padx=6)

        # finished / others – just close
        ctk.CTkButton(
            btns,
            text="Close",
            width=100,
            fg_color="#888888",
            hover_color="#666666",
            command=win.destroy,
        ).pack(side="left", padx=6)

        self._center_toplevel(win)

    # ---------- TOOLBAR ACTIONS ----------

    def _logout(self):
        if self.parent is not None:
            self.destroy()
            self.parent.deiconify()
        else:
            self.destroy()

    # ---------- TOOLBAR ACTIONS ----------

    def _logout(self):
        if self.parent is not None:
            self.destroy()
            self.parent.deiconify()
        else:
            self.destroy()

    def _open_toolbox(self):
        try:
            from ui.toolbox_ui import ToolboxWindow
            ToolboxWindow(self)
        except Exception as e:
            messagebox.showerror("Error", f"Could not open toolbox:\n{e}")

    def _open_reports(self):
        try:
            from ui.reports_ui import ReportsWindow
            ReportsWindow(self)
        except Exception as e:
            messagebox.showerror("Error", f"Could not open reports window:\n{e}")

    def _open_maintenance(self):
        try:
            from ui.maintenance_ui import MaintenanceWindow
            MaintenanceWindow(self)
        except Exception as e:
            messagebox.showerror("Error", f"Could not open maintenance window:\n{e}")

    def _open_clients(self):
        try:
            from ui.clients_ui import ClientsWindow
            ClientsWindow(self)
        except Exception as e:
            messagebox.showerror("Error", f"Could not open clients window:\n{e}")

    def on_window_close(self):
        self._logout()

    from ui.clients import ClientsWindow

    def _open_clients(self):
        ClientsWindow(self)

    def on_window_close(self):
        self._logout()
