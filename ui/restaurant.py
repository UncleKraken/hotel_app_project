# ui/restaurant.py

import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import date

import customtkinter as ctk
from tkinter import messagebox
from PIL import Image

from backend import finance


# ---------- PATHS / ICONS ----------

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ICON_DIR = os.path.join(BASE_DIR, "assets", "icons")
COLOR_BG = "#E6E7EA"
COLOR_WAITER_PANEL = "#DCDDE0"
COLOR_TABLE_AREA = "#28D3E3"

COLOR_STATUS = {
    "free": None,            # no color / default
    "reserved": "#3B82F6",   # blue
    "serving": "#16A34A",    # green
    "maintenance": "#EF4444" # red
}


@dataclass
class TableState:
    number: int
    status: str = "free"              # free / reserved / serving / maintenance
    waiter: Optional[str] = None
    guests: int = 0
    items: List[Dict[str, Any]] = field(default_factory=list)
    note: str = ""


class RestaurantWindow(ctk.CTkToplevel):
    """Waiter / Bar & Restaurant UI."""

    def __init__(self, parent=None, user: Optional[Dict] = None):
        super().__init__()

        # Make this window modal over login
        self.parent = parent
        if parent is not None:
            self.transient(parent)
            self.grab_set()
        self.focus()

        self.user = user or {"username": "waiter"}

        self.title("InnKeeper • Restaurant (waiter)")
        self.geometry("1400x820")
        self.minsize(1100, 650)
        ctk.set_appearance_mode("light")

        # icon cache
        self._images: Dict[str, ctk.CTkImage] = {}
        self._load_icons()

        # waiter list (later from DB)
        self.waiter_names: List[str] = ["Waiter 1", "Waiter 2", "Waiter 3"]
        self.current_waiter: Optional[str] = None

        # tables
        self.table_count = 15
        self.tables: Dict[int, TableState] = {
            i: TableState(number=i) for i in range(1, self.table_count + 1)
        }
        self.table_buttons: Dict[int, ctk.CTkButton] = {}
        self.selected_table: Optional[int] = None

        # sample MENU data
        self.menu_entries: List[Dict[str, Any]] = [
            {"area": "Bar", "group": "Cold Drinks", "name": "Coca Cola 0.33L", "price": 2.50},
            {"area": "Bar", "group": "Cold Drinks", "name": "Sprite 0.33L", "price": 2.50},
            {"area": "Bar", "group": "Cold Drinks", "name": "Water 0.5L", "price": 1.00},
            {"area": "Bar", "group": "Hot Drinks", "name": "Espresso", "price": 1.50},
            {"area": "Bar", "group": "Hot Drinks", "name": "Cappuccino", "price": 2.00},

            {"area": "Restaurant", "group": "Salads", "name": "Greek Salad", "price": 5.50},
            {"area": "Restaurant", "group": "Salads", "name": "Caesar Salad", "price": 6.50},
            {"area": "Restaurant", "group": "First dishes", "name": "Spaghetti Bolognese", "price": 8.00},
            {"area": "Restaurant", "group": "First dishes", "name": "Chicken Alfredo", "price": 8.50},
            {"area": "Restaurant", "group": "Desserts", "name": "Chocolate Cake", "price": 4.00},
            {"area": "Restaurant", "group": "Desserts", "name": "Ice Cream (2 scoops)", "price": 3.50},
        ]

        # bubble-related widgets
        self.bubble_container: Optional[ctk.CTkFrame] = None
        self.bubble: Optional[ctk.CTkFrame] = None
        self.no_table_label: Optional[ctk.CTkLabel] = None

        self.search_entry: Optional[ctk.CTkEntry] = None
        self.table_title_label: Optional[ctk.CTkLabel] = None
        self.status_var: Optional[ctk.StringVar] = None
        self.status_menu: Optional[ctk.CTkOptionMenu] = None
        self.guests_entry: Optional[ctk.CTkEntry] = None
        self.items_frame_inner: Optional[ctk.CTkScrollableFrame] = None
        self.note_text: Optional[ctk.CTkTextbox] = None
        self.total_entry: Optional[ctk.CTkEntry] = None

        self._build_layout()

    # ---------- ICONS ----------

    def _load_icons(self):
        def load(name: str, filename: str, size):
            path = os.path.join(ICON_DIR, filename)
            if not os.path.exists(path):
                print(f"[WAITER ICON] Missing: {path}")
                return
            try:
                img = Image.open(path).resize(size, Image.LANCZOS)
                self._images[name] = ctk.CTkImage(
                    light_image=img, dark_image=img, size=size
                )
                print(f"[WAITER ICON] Loaded: {path}")
            except Exception as e:
                print(f"[WAITER ICON] Error loading {path}: {e}")

        load("table", "table.png", (100, 100))
        # Load receipt icon but DO NOT attach to button (avoid Tk image bug)
        load("receipt", "print_receipt.png", (22, 22))

    # ---------- LAYOUT ----------

    def _build_layout(self):
        self.configure(fg_color=COLOR_BG)

        # LEFT PANEL (waiters)
        left = ctk.CTkFrame(self, fg_color=COLOR_WAITER_PANEL, corner_radius=0, width=220)
        left.pack(side="left", fill="y")

        ctk.CTkLabel(
            left,
            text="Waiters",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(pady=(20, 10))

        self.waiter_buttons: Dict[str, ctk.CTkButton] = {}
        for name in self.waiter_names:
            btn = ctk.CTkButton(
                left,
                text=name,
                width=160,
                height=50,
                fg_color="#FF4B4B",
                hover_color="#E53935",
                corner_radius=16,
                command=lambda n=name: self._select_waiter(n),
            )
            btn.pack(pady=8)
            self.waiter_buttons[name] = btn

        # Bottom left: settings / logout
        bottom_left = ctk.CTkFrame(left, fg_color=COLOR_WAITER_PANEL)
        bottom_left.pack(side="bottom", pady=20)

        ctk.CTkButton(
            bottom_left,
            text="Settings",
            width=160,
            height=45,
            fg_color="#FF4B4B",
            hover_color="#E53935",
            corner_radius=16,
            command=self._open_settings,
        ).pack(pady=(0, 8))

        ctk.CTkButton(
            bottom_left,
            text="Logout",
            width=160,
            height=45,
            fg_color="#333333",
            hover_color="#111111",
            corner_radius=16,
            command=self._logout,
        ).pack()

        # CENTER (tables) + RIGHT (bubble)
        center = ctk.CTkFrame(self, fg_color=COLOR_BG, corner_radius=0)
        center.pack(side="left", fill="both", expand=True)

        board = ctk.CTkFrame(center, fg_color=COLOR_TABLE_AREA, corner_radius=0)
        board.pack(side="left", fill="both", expand=True, padx=(6, 0), pady=6)

        self.bubble_container = ctk.CTkFrame(center, fg_color=COLOR_BG, corner_radius=0, width=460)
        self.bubble_container.pack(side="right", fill="y", padx=(0, 6), pady=6)

        self.no_table_label = ctk.CTkLabel(
            self.bubble_container,
            text="Select a table to see details",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#666666",
        )
        self.no_table_label.pack(expand=True)

        # Create bubble UI (but not shown until table click)
        self._build_bubble_ui()
        self.bubble.pack_propagate(False)

        # Tables grid 3 x 5
        rows, cols = 3, 5
        for r in range(rows):
            board.rowconfigure(r, weight=1)
        for c in range(cols):
            board.columnconfigure(c, weight=1)

        for n in range(1, self.table_count + 1):
            r = (n - 1) // cols
            c = (n - 1) % cols
            btn = ctk.CTkButton(
                board,
                text=str(n),
                width=150,
                height=130,
                corner_radius=40,
                fg_color="#F3F4F6",
                hover_color="#E5E7EB",
                border_width=2,
                border_color="#D1D5DB",
                image=self._images.get("table"),
                compound="top",
                font=ctk.CTkFont(size=16, weight="bold"),
                command=lambda num=n: self._on_table_click(num),
            )
            btn.grid(row=r, column=c, padx=20, pady=20, sticky="nsew")
            self.table_buttons[n] = btn

        # Auto-select waiter if username resembles their name
        username = (self.user.get("username") or "").lower()
        for w in self.waiter_names:
            if w.lower().replace(" ", "") in username.replace(" ", ""):
                self._select_waiter(w)
                break

    # ---------- BUBBLE UI ----------

    def _build_bubble_ui(self):
        self.bubble = ctk.CTkFrame(self.bubble_container, fg_color="white", corner_radius=20)

        # Header: search + MENU
        header = ctk.CTkFrame(self.bubble, fg_color="white")
        header.pack(fill="x", padx=12, pady=(10, 4))

        self.search_entry = ctk.CTkEntry(
            header,
            placeholder_text="Search menu item…",
            width=220,
        )
        self.search_entry.pack(side="left", padx=(0, 8))
        self.search_entry.bind("<Return>", lambda e: self._open_menu_popup())

        ctk.CTkButton(
            header,
            text="MENU",
            width=80,
            height=30,
            fg_color="#FFC93C",
            hover_color="#E0A800",
            text_color="black",
            corner_radius=16,
            command=self._open_menu_popup,
        ).pack(side="left")

        # Table title
        self.table_title_label = ctk.CTkLabel(
            self.bubble,
            text="No table selected",
            font=ctk.CTkFont(size=15, weight="bold"),
            anchor="w",
            text_color="#111827",
        )
        self.table_title_label.pack(fill="x", padx=14, pady=(4, 2))

        # Status + guests row
        top_row = ctk.CTkFrame(self.bubble, fg_color="white")
        top_row.pack(fill="x", padx=14, pady=(2, 6))

        ctk.CTkLabel(top_row, text="Status:", width=70, anchor="w").pack(side="left")
        self.status_var = ctk.StringVar(value="free")
        self.status_menu = ctk.CTkOptionMenu(
            top_row,
            values=["free", "reserved", "serving", "maintenance"],
            variable=self.status_var,
            width=110,
            command=lambda _: self._update_selected_status(),
        )
        self.status_menu.pack(side="left", padx=(0, 12))

        ctk.CTkLabel(top_row, text="Guests:", width=60, anchor="w").pack(side="left")
        self.guests_entry = ctk.CTkEntry(top_row, width=60)
        self.guests_entry.pack(side="left")

        # Orders area
        ctk.CTkLabel(
            self.bubble,
            text="Orders:",
            anchor="w",
        ).pack(fill="x", padx=14, pady=(6, 2))

        items_outer = ctk.CTkFrame(self.bubble, fg_color="#F3F4F6", corner_radius=12)
        items_outer.pack(fill="both", expand=True, padx=14, pady=(0, 4))

        self.items_frame_inner = ctk.CTkScrollableFrame(items_outer, fg_color="#F3F4F6")
        self.items_frame_inner.pack(fill="both", expand=True, padx=6, pady=6)

        # Total row
        bottom_info = ctk.CTkFrame(self.bubble, fg_color="white")
        bottom_info.pack(fill="x", padx=14, pady=(4, 4))

        ctk.CTkLabel(bottom_info, text="Total:", width=60, anchor="w").pack(side="left")
        self.total_entry = ctk.CTkEntry(bottom_info, width=90)
        self.total_entry.pack(side="left", padx=(0, 4))
        ctk.CTkLabel(bottom_info, text="€", width=10, anchor="w").pack(side="left")

        # Note
        ctk.CTkLabel(self.bubble, text="Note:", anchor="w").pack(fill="x", padx=14, pady=(2, 0))
        self.note_text = ctk.CTkTextbox(self.bubble, height=70)
        self.note_text.pack(fill="x", padx=14, pady=(0, 4))

        # Bottom buttons
        bottom = ctk.CTkFrame(self.bubble, fg_color="white")
        bottom.pack(fill="x", padx=14, pady=(4, 10))

        ctk.CTkButton(
            bottom,
            text="Save",
            width=120,
            fg_color="#3B82F6",
            hover_color="#2563EB",
            command=self._save_table_state,
        ).pack(side="left", padx=(0, 6))

        # IMPORTANT: no image here to avoid Tk "pyimage1" bug
        ctk.CTkButton(
            bottom,
            text="Print & Free",
            width=140,
            fg_color="#10B981",
            hover_color="#059669",
            command=self._print_and_free,
        ).pack(side="left", padx=(6, 0))

    def _show_bubble(self):
        if self.no_table_label and self.no_table_label.winfo_ismapped():
            self.no_table_label.pack_forget()
        if self.bubble and not self.bubble.winfo_ismapped():
            self.bubble.pack(fill="both", expand=True, padx=6, pady=6)

    # ---------- WAITER / TABLE SELECT ----------

    def _select_waiter(self, name: str):
        self.current_waiter = name
        for w, btn in self.waiter_buttons.items():
            btn.configure(fg_color="#FF6B6B" if w == name else "#FF4B4B")
        if self.selected_table is not None:
            self._update_bubble_title()

    def _on_table_click(self, num: int):
        if self.current_waiter is None:
            messagebox.showinfo("Select waiter", "Please select your waiter name first.")
            return

        tbl = self.tables[num]

        # If table already owned by another waiter, block
        if tbl.waiter is not None and tbl.waiter != self.current_waiter:
            messagebox.showwarning(
                "Table in use",
                f"Table {num} is currently handled by {tbl.waiter}.",
            )
            return

        # First time a free table is taken → ask initial info
        if tbl.status == "free" and tbl.waiter is None:
            info = self._ask_initial_table_info(num)
            if not info:
                return
            tbl.guests = info["guests"]
            tbl.status = info["status"]
            tbl.waiter = self.current_waiter

        # Normal open
        self.selected_table = num
        if tbl.waiter is None:
            tbl.waiter = self.current_waiter

        self._show_bubble()
        self._load_table_into_bubble()
        self._refresh_all_table_colors()

    # ---------- INITIAL TABLE INFO ----------

    def _ask_initial_table_info(self, table_number: int) -> Optional[Dict[str, Any]]:
        """Dialog asking for guests + initial status when taking a free table."""
        win = ctk.CTkToplevel(self)
        win.title(f"Table {table_number} – setup")
        win.resizable(False, False)
        win.grab_set()

        self.update_idletasks()
        W, H = 280, 180
        x = self.winfo_rootx() + (self.winfo_width() - W) // 2
        y = self.winfo_rooty() + (self.winfo_height() - H) // 2
        win.geometry(f"{W}x{H}+{max(x, 0)}+{max(y, 0)}")

        frame = ctk.CTkFrame(win)
        frame.pack(expand=True, fill="both", padx=12, pady=12)

        ctk.CTkLabel(
            frame,
            text=f"Table {table_number}",
            font=ctk.CTkFont(size=15, weight="bold"),
        ).pack(pady=(4, 8))

        row1 = ctk.CTkFrame(frame)
        row1.pack(pady=4, fill="x")
        ctk.CTkLabel(row1, text="Guests:", width=80, anchor="e").pack(side="left", padx=(0, 6))
        guests_entry = ctk.CTkEntry(row1, width=80)
        guests_entry.insert(0, "2")
        guests_entry.pack(side="left")

        row2 = ctk.CTkFrame(frame)
        row2.pack(pady=4, fill="x")
        ctk.CTkLabel(row2, text="Status:", width=80, anchor="e").pack(side="left", padx=(0, 6))
        status_var = ctk.StringVar(value="serving")
        ctk.CTkOptionMenu(
            row2,
            values=["reserved", "serving", "maintenance"],
            variable=status_var,
            width=120,
        ).pack(side="left")

        result: Dict[str, Any] = {"ok": False}

        def ok():
            try:
                g = int(guests_entry.get().strip() or "0")
                g = max(0, g)
            except ValueError:
                messagebox.showerror("Invalid", "Guests must be a number.")
                return
            result["ok"] = True
            result["guests"] = g
            result["status"] = status_var.get()
            win.destroy()

        ctk.CTkButton(frame, text="OK", width=80, command=ok).pack(pady=8)

        self.wait_window(win)
        return result if result.get("ok") else None

    # ---------- BUBBLE <-> TABLE STATE ----------

    def _load_table_into_bubble(self):
        if self.selected_table is None:
            return
        tbl = self.tables[self.selected_table]

        self._update_bubble_title()

        self.status_var.set(tbl.status)

        self.guests_entry.delete(0, "end")
        if tbl.guests:
            self.guests_entry.insert(0, str(tbl.guests))

        self._render_items_list()

        total = sum(i["qty"] * i["price"] for i in tbl.items)
        self.total_entry.delete(0, "end")
        self.total_entry.insert(0, f"{total:.2f}")

        self.note_text.delete("1.0", "end")
        if tbl.note:
            self.note_text.insert("1.0", tbl.note)

    def _update_bubble_title(self):
        if self.selected_table is None:
            self.table_title_label.configure(text="No table selected")
            return
        tbl = self.tables[self.selected_table]
        waiter_txt = f" • {tbl.waiter}" if tbl.waiter else ""
        self.table_title_label.configure(text=f"Table {tbl.number}{waiter_txt}")

    def _update_selected_status(self):
        if self.selected_table is None:
            return
        tbl = self.tables[self.selected_table]
        tbl.status = self.status_var.get()
        self._refresh_all_table_colors()

    # ---------- ITEMS RENDER ----------

    def _render_items_list(self):
        for child in self.items_frame_inner.winfo_children():
            child.destroy()

        if self.selected_table is None:
            return
        tbl = self.tables[self.selected_table]

        for idx, item in enumerate(tbl.items):
            row = ctk.CTkFrame(self.items_frame_inner, fg_color="#E5E7EB", corner_radius=8)
            row.pack(fill="x", pady=3, padx=2)

            ctk.CTkLabel(
                row,
                text=item["name"],
                anchor="w",
            ).pack(side="left", padx=(6, 4), expand=True)

            qty_frame = ctk.CTkFrame(row, fg_color="#E5E7EB")
            qty_frame.pack(side="left", padx=4)

            def make_change(delta: int, index: int = idx):
                return lambda: self._change_item_qty(index, delta)

            ctk.CTkButton(
                qty_frame,
                text="-",
                width=26,
                height=26,
                fg_color="#9CA3AF",
                hover_color="#6B7280",
                command=make_change(-1),
            ).pack(side="left", padx=(0, 2))

            ctk.CTkLabel(
                qty_frame,
                text=str(item["qty"]),
                width=20,
                anchor="center",
            ).pack(side="left")

            ctk.CTkButton(
                qty_frame,
                text="+",
                width=26,
                height=26,
                fg_color="#3B82F6",
                hover_color="#2563EB",
                command=make_change(1),
            ).pack(side="left", padx=(2, 0))

            line_total = item["qty"] * item["price"]
            ctk.CTkLabel(
                row,
                text=f"{item['price']:.2f}€ | {line_total:.2f}€",
                width=120,
                anchor="e",
            ).pack(side="left", padx=6)

            ctk.CTkButton(
                row,
                text="✕",
                width=26,
                height=26,
                fg_color="#DC2626",
                hover_color="#B91C1C",
                command=lambda i=idx: self._delete_item(i),
            ).pack(side="right", padx=4)

    def _change_item_qty(self, index: int, delta: int):
        if self.selected_table is None:
            return
        tbl = self.tables[self.selected_table]
        if index < 0 or index >= len(tbl.items):
            return
        item = tbl.items[index]
        new_qty = item["qty"] + delta
        if new_qty <= 0:
            tbl.items.pop(index)
        else:
            item["qty"] = new_qty
        self._load_table_into_bubble()

    def _delete_item(self, index: int):
        if self.selected_table is None:
            return
        tbl = self.tables[self.selected_table]
        if 0 <= index < len(tbl.items):
            tbl.items.pop(index)
        self._load_table_into_bubble()

    # ---------- SAVE / PRINT ----------

    def _save_table_state(self):
        if self.selected_table is None:
            return
        tbl = self.tables[self.selected_table]

        try:
            guests = int(self.guests_entry.get().strip() or "0")
        except ValueError:
            guests = 0
        tbl.guests = max(0, guests)

        tbl.status = self.status_var.get()
        tbl.note = self.note_text.get("1.0", "end").strip()

        total = sum(i["qty"] * i["price"] for i in tbl.items)
        self.total_entry.delete(0, "end")
        self.total_entry.insert(0, f"{total:.2f}")

        messagebox.showinfo("Saved", f"Table {tbl.number} saved.")
        self._refresh_all_table_colors()

    def _ask_payment_method(self) -> Optional[str]:
        """Small dialog asking Cash / Card before printing bill."""
        win = ctk.CTkToplevel(self)
        win.title("Payment method")
        win.resizable(False, False)
        win.grab_set()

        # center on parent
        self.update_idletasks()
        px = self.winfo_rootx()
        py = self.winfo_rooty()
        pw = self.winfo_width()
        ph = self.winfo_height()
        W, H = 260, 150
        x = px + (pw - W) // 2
        y = py + (ph - H) // 2
        win.geometry(f"{W}x{H}+{max(x, 0)}+{max(y, 0)}")

        frame = ctk.CTkFrame(win)
        frame.pack(expand=True, fill="both", padx=12, pady=12)

        ctk.CTkLabel(
            frame,
            text="Choose payment method:",
            font=ctk.CTkFont(size=14, weight="bold"),
        ).pack(pady=(4, 8))

        method_var = ctk.StringVar(value="Cash")
        menu = ctk.CTkOptionMenu(
            frame,
            values=["Cash", "Card"],
            variable=method_var,
            width=140,
        )
        menu.pack(pady=(0, 10))

        result = {"ok": False}

        def confirm():
            result["ok"] = True
            win.destroy()

        def cancel():
            win.destroy()

        btn_row = ctk.CTkFrame(frame)
        btn_row.pack(pady=6)

        ctk.CTkButton(btn_row, text="OK", width=80, command=confirm).pack(side="left", padx=4)
        ctk.CTkButton(
            btn_row,
            text="Cancel",
            width=80,
            fg_color="#9CA3AF",
            hover_color="#6B7280",
            command=cancel,
        ).pack(side="left", padx=4)

        self.wait_window(win)
        return method_var.get() if result["ok"] else None

    def _print_and_free(self):
        if self.selected_table is None:
            return
        tbl = self.tables[self.selected_table]

        # calculate total
        total = sum(i["qty"] * i["price"] for i in tbl.items)

        # ask payment method
        method = self._ask_payment_method()
        if not method:
            return  # user cancelled

        # build demo receipt
        lines = [f"Bill for Table {tbl.number} ({tbl.waiter or 'no waiter'})"]
        lines.append(f"Guests: {tbl.guests}")
        lines.append("")
        for it in tbl.items:
            lines.append(f"{it['qty']} x {it['name']} – {it['qty'] * it['price']:.2f} €")
        lines.append("")
        lines.append(f"TOTAL: {total:.2f} €")
        lines.append(f"Method: {method}")
        if tbl.note:
            lines.append("")
            lines.append(f"Note: {tbl.note}")

        messagebox.showinfo("Print (demo)", "\n".join(lines))

        # ---- LOG INTO FINANCE (single row per bill) ----
        try:
            finance.add_finance_log(
                source="Restaurant",
                category="Food",  # you can refine this later
                description=f"Table {tbl.number} bill",
                amount=total,
                method=method,
                pending=False,
                log_date=date.today(),
            )
        except Exception as e:
            print("[FINANCE ERROR]", e)

        # free table
        tbl.status = "free"
        tbl.waiter = None
        tbl.guests = 0
        tbl.items.clear()
        tbl.note = ""
        self.selected_table = None

        # reset UI
        if self.bubble and self.bubble.winfo_ismapped():
            self.bubble.pack_forget()
        if self.no_table_label and not self.no_table_label.winfo_ismapped():
            self.no_table_label.pack(expand=True)

        self._refresh_all_table_colors()

    # ---------- MENU POPUP ----------

    def _open_menu_popup(self):
        """Opens popup showing Bar / Restaurant menu; filtered by search text."""
        search = (self.search_entry.get().strip() or "").lower()

        win = ctk.CTkToplevel(self)
        win.title("Menu")
        win.geometry("500x420")
        win.resizable(False, False)
        win.grab_set()

        # center
        self.update_idletasks()
        pw = self.winfo_width()
        ph = self.winfo_height()
        px = self.winfo_rootx()
        py = self.winfo_rooty()
        W, H = 500, 420
        x = px + (pw - W) // 2
        y = py + (ph - H) // 2
        win.geometry(f"{W}x{H}+{max(x, 0)}+{max(y, 0)}")

        main = ctk.CTkFrame(win)
        main.pack(expand=True, fill="both", padx=10, pady=10)

        ctk.CTkLabel(
            main,
            text="Select item to add to table",
            font=ctk.CTkFont(size=15, weight="bold"),
        ).pack(pady=(4, 8))

        tabs = ctk.CTkTabview(main, width=460, height=340)
        tabs.pack(expand=True, fill="both", padx=4, pady=4)

        bar_tab = tabs.add("Bar")
        rest_tab = tabs.add("Restaurant")

        def fill_tab(parent_tab, area_name):
            sf = ctk.CTkScrollableFrame(parent_tab)
            sf.pack(fill="both", expand=True, padx=4, pady=4)

            groups: Dict[str, ctk.CTkFrame] = {}

            for item in self.menu_entries:
                if item["area"] != area_name:
                    continue
                if search and search not in item["name"].lower():
                    continue

                group = item["group"]
                if group not in groups:
                    group_frame = ctk.CTkFrame(sf, fg_color="#E5E7EB", corner_radius=10)
                    group_frame.pack(fill="x", pady=4, padx=2)

                    ctk.CTkLabel(
                        group_frame,
                        text=group,
                        font=ctk.CTkFont(size=13, weight="bold"),
                        anchor="w",
                    ).pack(fill="x", padx=8, pady=(4, 2))

                    inner = ctk.CTkFrame(group_frame, fg_color="#E5E7EB")
                    inner.pack(fill="x", padx=6, pady=(0, 4))
                    groups[group] = inner

                inner = groups[group]

                btn = ctk.CTkButton(
                    inner,
                    text=f"{item['name']} – {item['price']:.2f}€",
                    anchor="w",
                    width=380,
                    height=32,
                    fg_color="#FFFFFF",
                    hover_color="#D1D5DB",
                    text_color="black",
                    command=lambda it=item: self._add_item_from_menu(it, win),
                )
                btn.pack(fill="x", pady=2, padx=4)

        fill_tab(bar_tab, "Bar")
        fill_tab(rest_tab, "Restaurant")

    def _add_item_from_menu(self, menu_item: Dict[str, Any], popup):
        if self.selected_table is None:
            popup.destroy()
            return
        tbl = self.tables[self.selected_table]
        tbl.items.append(
            {"name": menu_item["name"], "qty": 1, "price": menu_item["price"]}
        )
        popup.destroy()
        self._load_table_into_bubble()

    # ---------- HELPERS ----------

    def _refresh_all_table_colors(self):
        for num, btn in self.table_buttons.items():
            tbl = self.tables[num]
            col = COLOR_STATUS.get(tbl.status)
            if col:
                btn.configure(fg_color=col, hover_color=col)
            else:
                btn.configure(fg_color="#F3F4F6", hover_color="#E5E7EB")

    def _open_settings(self):
        messagebox.showinfo(
            "Settings",
            "Restaurant settings (tables count, waiters, menu) will be implemented later."
        )

    def _logout(self):
        self.destroy()
        if self.parent is not None:
            self.parent.deiconify()

    def on_window_close(self):
        self._logout()
