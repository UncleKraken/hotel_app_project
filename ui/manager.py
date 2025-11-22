# ui/manager.py

import os
import sqlite3

import customtkinter as ctk
from tkinter import messagebox

from ui.receptionist import ReceptionistWindow
from ui.restaurant import RestaurantWindow
from ui.cleaning import CleaningWindow
from ui.finance import FinanceWindow

from backend import restaurant_admin  # already created earlier

# ---------- DB PATH ----------

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "database", "hotel.db")


def get_conn():
    """Return a SQLite connection with Row factory."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


class ManagerWindow(ctk.CTkToplevel):
    """
    Manager / Admin UI

    - Sidebar navigation
    - Manager panels: Rooms, Restaurant, Cleaning, Staff/Users, Settings
    - Can open other UIs as child windows (Reception / Restaurant / Cleaning / Finance)
    - Logout returns to LoginWindow
    """

    def __init__(self, parent=None, user=None):
        super().__init__()

        self.parent = parent          # this will be LoginWindow
        self.user = user or {"username": "manager"}

        # Make modal over login
        if self.parent is not None:
            self.transient(self.parent)
            self.grab_set()

        self.title("InnKeeper • Manager")
        self.geometry("1300x780")
        self.minsize(1100, 650)
        ctk.set_appearance_mode("light")

        # current theme state
        self.theme_var = ctk.StringVar(value="Light")

        # manager panel row caches
        self._menu_rows = {}
        self._table_rows = {}
        self._rooms_rows = {}
        self._cleaning_rows = {}
        self._user_rows = {}

        # helper caches for cleaning panel
        self._clean_rooms_choices = []   # list of (room_id, label)
        self._clean_cleaner_choices = [] # list of (user_id, label)

        # build layout
        self._build_layout()

        # hide login while manager window is open
        if self.parent is not None:
            try:
                self.parent.withdraw()
            except Exception:
                pass

        self.protocol("WM_DELETE_WINDOW", self.on_window_close)

    # ---------- LAYOUT ----------

    def _build_layout(self):
        # main 2-column layout
        self.sidebar = ctk.CTkFrame(self, fg_color="#111827", corner_radius=0, width=220)
        self.sidebar.pack(side="left", fill="y")

        self.content = ctk.CTkFrame(self, fg_color="#F3F4F6")
        self.content.pack(side="right", fill="both", expand=True)

        self._build_sidebar()
        self._build_dashboard()  # default content

    def _build_sidebar(self):
        # App title
        title = ctk.CTkLabel(
            self.sidebar,
            text="InnKeeper\nManager",
            font=ctk.CTkFont(size=20, weight="bold"),
            justify="left",
            text_color="white",
        )
        title.pack(padx=20, pady=(20, 30), anchor="w")

        # helper to create nav buttons
        def nav_btn(text, command):
            b = ctk.CTkButton(
                self.sidebar,
                text=text,
                width=180,
                height=40,
                fg_color="#1F2937",
                hover_color="#374151",
                text_color="white",
                anchor="w",
                command=command,
            )
            b.pack(padx=20, pady=4)
            return b

        self.btn_dashboard = nav_btn("🏠  Dashboard", self._build_dashboard)
        # NOW: Rooms Manager opens manager panel, not Reception UI directly
        self.btn_rooms = nav_btn("🛏️  Rooms Manager", self._build_rooms_panel)
        # Restaurant Manager (DB editor)
        self.btn_restaurant = nav_btn("🍽️  Restaurant Manager", self._build_restaurant_panel)
        # Cleaning Manager (DB editor)
        self.btn_cleaning = nav_btn("🧹  Cleaning Manager", self._build_cleaning_panel)
        # Finance still opens FinanceWindow UI
        self.btn_finance = nav_btn("💰  Finance Dashboard", self.open_finance_ui)
        # Staff & Users (CRUD)
        self.btn_staff = nav_btn("👥  Staff & Users", self._build_staff_panel)
        self.btn_settings = nav_btn("⚙️  Settings", self._build_settings_panel)

        # spacer
        ctk.CTkLabel(self.sidebar, text="", fg_color="transparent").pack(expand=True, fill="y")

        # Logout button
        ctk.CTkButton(
            self.sidebar,
            text="🚪  Logout",
            width=180,
            height=40,
            fg_color="#DC2626",
            hover_color="#B91C1C",
            text_color="white",
            command=self._logout,
        ).pack(padx=20, pady=20)

    # ---------- CONTENT HELPERS ----------

    def _clear_content(self):
        for child in self.content.winfo_children():
            child.destroy()

    # ---------- DASHBOARD ----------

    def _build_dashboard(self):
        self._clear_content()

        wrapper = ctk.CTkFrame(self.content, fg_color="#F3F4F6")
        wrapper.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(
            wrapper,
            text="Manager Dashboard",
            font=ctk.CTkFont(size=22, weight="bold"),
            anchor="w",
        ).pack(anchor="w", pady=(0, 10))

        ctk.CTkLabel(
            wrapper,
            text="Quick overview of the hotel (demo placeholders for now).",
            font=ctk.CTkFont(size=13),
            text_color="#4B5563",
        ).pack(anchor="w", pady=(0, 20))

        # Simple 3 cards row (dummy data for presentation)
        cards = ctk.CTkFrame(wrapper, fg_color="#F3F4F6")
        cards.pack(fill="x")

        def stat_card(parent, title, value, note):
            card = ctk.CTkFrame(parent, fg_color="white", corner_radius=16)
            card.pack(side="left", fill="x", expand=True, padx=6)
            ctk.CTkLabel(
                card,
                text=title,
                font=ctk.CTkFont(size=14, weight="bold"),
                anchor="w",
            ).pack(anchor="w", padx=12, pady=(10, 2))
            ctk.CTkLabel(
                card,
                text=value,
                font=ctk.CTkFont(size=20, weight="bold"),
            ).pack(anchor="w", padx=12, pady=(0, 2))
            ctk.CTkLabel(
                card,
                text=note,
                font=ctk.CTkFont(size=11),
                text_color="#6B7280",
            ).pack(anchor="w", padx=12, pady=(0, 10))

        stat_card(cards, "Occupied Rooms", "18", "Live data can be wired from DB")
        stat_card(cards, "Restaurant Orders Today", "42", "Pulled from finance / restaurant")
        stat_card(cards, "Pending Cleanings", "7", "From cleaning module")

        # Quick launch for department UIs
        launch = ctk.CTkFrame(wrapper, fg_color="white", corner_radius=16)
        launch.pack(fill="x", pady=20)

        ctk.CTkLabel(
            launch,
            text="Open Department UIs",
            font=ctk.CTkFont(size=14, weight="bold"),
        ).pack(anchor="w", padx=16, pady=(10, 4))

        btn_row = ctk.CTkFrame(launch, fg_color="white")
        btn_row.pack(anchor="w", padx=16, pady=(0, 12))

        ctk.CTkButton(
            btn_row,
            text="Reception UI",
            width=140,
            fg_color="#3B82F6",
            hover_color="#2563EB",
            command=self.open_reception_ui,
        ).pack(side="left", padx=6)

        ctk.CTkButton(
            btn_row,
            text="Restaurant UI",
            width=140,
            fg_color="#10B981",
            hover_color="#059669",
            command=self.open_restaurant_ui,
        ).pack(side="left", padx=6)

        ctk.CTkButton(
            btn_row,
            text="Cleaning UI",
            width=140,
            fg_color="#F59E0B",
            hover_color="#D97706",
            command=self.open_cleaning_ui,
        ).pack(side="left", padx=6)

        ctk.CTkButton(
            btn_row,
            text="Finance UI",
            width=140,
            fg_color="#6366F1",
            hover_color="#4F46E5",
            command=self.open_finance_ui,
        ).pack(side="left", padx=6)

        # Bottom info
        bottom = ctk.CTkFrame(wrapper, fg_color="white", corner_radius=16)
        bottom.pack(fill="both", expand=True, pady=10)

        ctk.CTkLabel(
            bottom,
            text=(
                "Tip: Use the left menu to manage rooms, menu items, tables, "
                "cleaning tasks and staff. All changes are saved to the database."
            ),
            font=ctk.CTkFont(size=13),
            text_color="#111827",
        ).pack(anchor="w", padx=16, pady=16)

    # =======================================================================
    # ROOMS MANAGER (F)
    # =======================================================================

    def _build_rooms_panel(self):
        self._clear_content()
        self._rooms_rows.clear()

        wrapper = ctk.CTkFrame(self.content, fg_color="#F3F4F6")
        wrapper.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(
            wrapper,
            text="Rooms Manager",
            font=ctk.CTkFont(size=22, weight="bold"),
            anchor="w",
        ).pack(anchor="w", pady=(0, 8))

        ctk.CTkLabel(
            wrapper,
            text=(
                "Here the manager can add / edit / delete rooms. "
                "Changes are stored in the rooms table and are visible "
                "in the Receptionist UI."
            ),
            font=ctk.CTkFont(size=13),
            text_color="#4B5563",
            justify="left",
        ).pack(anchor="w", pady=(0, 14))

        ctk.CTkButton(
            wrapper,
            text="Open Reception UI",
            width=160,
            fg_color="#3B82F6",
            hover_color="#2563EB",
            command=self.open_reception_ui,
        ).pack(anchor="w", pady=(0, 16))

        top = ctk.CTkFrame(wrapper, fg_color="#F3F4F6")
        top.pack(fill="x", padx=10, pady=(0, 4))

        ctk.CTkButton(
            top,
            text="+ Add room",
            width=140,
            fg_color="#10B981",
            hover_color="#059669",
            command=self._open_add_room_dialog,
        ).pack(side="left", padx=(0, 10), pady=4)

        self.rooms_list_frame = ctk.CTkScrollableFrame(wrapper, fg_color="#F3F4F6")
        self.rooms_list_frame.pack(fill="both", expand=True, padx=10, pady=10)

        self._reload_rooms()

    def _reload_rooms(self):
        for child in self.rooms_list_frame.winfo_children():
            child.destroy()
        self._rooms_rows.clear()

        try:
            with get_conn() as conn:
                cur = conn.execute(
                    """
                    SELECT room_id, room_number, type, floor, price, status
                    FROM rooms
                    ORDER BY floor, room_number
                    """
                )
                rows = cur.fetchall()
        except Exception as e:
            messagebox.showerror("DB error", f"Failed to load rooms:\n{e}")
            return

        if not rows:
            ctk.CTkLabel(
                self.rooms_list_frame,
                text="No rooms yet. Use '+ Add room' to create one.",
                text_color="#6B7280",
            ).pack(pady=10)
            return

        header = ctk.CTkFrame(self.rooms_list_frame, fg_color="#E5E7EB", corner_radius=8)
        header.pack(fill="x", padx=4, pady=(0, 4))

        def h(txt, w):
            ctk.CTkLabel(
                header, text=txt, width=w, font=ctk.CTkFont(size=13, weight="bold")
            ).pack(side="left", padx=4, pady=4)

        h("ID", 40)
        h("Room #", 80)
        h("Type", 140)
        h("Floor", 60)
        h("Price (€)", 80)
        h("Status", 120)

        for r in rows:
            self._add_room_row(r)

    def _add_room_row(self, r):
        row = ctk.CTkFrame(self.rooms_list_frame, fg_color="white", corner_radius=8)
        row.pack(fill="x", padx=4, pady=2)

        room_id = r["room_id"]

        ctk.CTkLabel(row, text=str(room_id), width=40).pack(side="left", padx=4, pady=4)

        num_entry = ctk.CTkEntry(row, width=80)
        num_entry.insert(0, r["room_number"])
        num_entry.pack(side="left", padx=4, pady=4)

        type_entry = ctk.CTkEntry(row, width=140)
        type_entry.insert(0, r["type"])
        type_entry.pack(side="left", padx=4, pady=4)

        floor_entry = ctk.CTkEntry(row, width=60)
        floor_entry.insert(0, str(r["floor"]))
        floor_entry.pack(side="left", padx=4, pady=4)

        price_entry = ctk.CTkEntry(row, width=80)
        price_entry.insert(0, str(r["price"] or 0))
        price_entry.pack(side="left", padx=4, pady=4)

        status_var = ctk.StringVar(value=r["status"] or "available")
        status_menu = ctk.CTkOptionMenu(
            row,
            values=["available", "occupied", "needs_cleaning", "maintenance", "out_of_order"],
            variable=status_var,
            width=120,
        )
        status_menu.pack(side="left", padx=4, pady=4)

        btn_save = ctk.CTkButton(
            row,
            text="Save",
            width=70,
            fg_color="#3B82F6",
            hover_color="#2563EB",
            command=lambda rid=room_id: self._save_room_row(rid),
        )
        btn_save.pack(side="left", padx=4, pady=4)

        btn_del = ctk.CTkButton(
            row,
            text="Delete",
            width=70,
            fg_color="#DC2626",
            hover_color="#B91C1C",
            command=lambda rid=room_id: self._delete_room_row(rid),
        )
        btn_del.pack(side="left", padx=4, pady=4)

        self._rooms_rows[room_id] = {
            "row": row,
            "room_number": num_entry,
            "type": type_entry,
            "floor": floor_entry,
            "price": price_entry,
            "status_var": status_var,
        }

    def _save_room_row(self, room_id: int):
        fields = self._rooms_rows.get(room_id)
        if not fields:
            return

        number = fields["room_number"].get().strip()
        rtype = fields["type"].get().strip() or "Standard"
        status = fields["status_var"].get()

        try:
            floor = int(fields["floor"].get().strip() or "0")
        except ValueError:
            messagebox.showerror("Invalid value", "Floor must be an integer.")
            return

        try:
            price = float(fields["price"].get().strip() or "0")
        except ValueError:
            messagebox.showerror("Invalid value", "Price must be a number.")
            return

        if not number:
            messagebox.showerror("Missing", "Room number cannot be empty.")
            return

        try:
            with get_conn() as conn:
                conn.execute(
                    """
                    UPDATE rooms
                    SET room_number=?, type=?, floor=?, price=?, status=?
                    WHERE room_id=?
                    """,
                    (number, rtype, floor, price, status, room_id),
                )
        except Exception as e:
            messagebox.showerror("DB error", f"Failed to save room:\n{e}")
            return

        messagebox.showinfo("Saved", "Room updated.")
        self._reload_rooms()

    def _delete_room_row(self, room_id: int):
        if not messagebox.askyesno(
            "Delete room", "Delete this room from the system?\n(Reservations may break in real app.)"
        ):
            return
        try:
            with get_conn() as conn:
                conn.execute("DELETE FROM rooms WHERE room_id=?", (room_id,))
        except Exception as e:
            messagebox.showerror("DB error", f"Failed to delete room:\n{e}")
            return
        self._reload_rooms()

    def _open_add_room_dialog(self):
        win = ctk.CTkToplevel(self)
        win.title("Add room")
        win.geometry("420x260")
        win.grab_set()

        frame = ctk.CTkFrame(win)
        frame.pack(expand=True, fill="both", padx=10, pady=10)

        ctk.CTkLabel(
            frame, text="New room", font=ctk.CTkFont(size=16, weight="bold")
        ).pack(pady=(6, 10))

        # room number
        r1 = ctk.CTkFrame(frame, fg_color="white")
        r1.pack(fill="x", padx=8, pady=4)
        ctk.CTkLabel(r1, text="Room #:", width=90, anchor="e").pack(side="left", padx=(0, 6))
        num_entry = ctk.CTkEntry(r1)
        num_entry.pack(side="left", fill="x", expand=True)

        # type
        r2 = ctk.CTkFrame(frame, fg_color="white")
        r2.pack(fill="x", padx=8, pady=4)
        ctk.CTkLabel(r2, text="Type:", width=90, anchor="e").pack(side="left", padx=(0, 6))
        type_entry = ctk.CTkEntry(r2)
        type_entry.insert(0, "Double")
        type_entry.pack(side="left", fill="x", expand=True)

        # floor
        r3 = ctk.CTkFrame(frame, fg_color="white")
        r3.pack(fill="x", padx=8, pady=4)
        ctk.CTkLabel(r3, text="Floor:", width=90, anchor="e").pack(side="left", padx=(0, 6))
        floor_entry = ctk.CTkEntry(r3)
        floor_entry.insert(0, "1")
        floor_entry.pack(side="left", fill="x", expand=True)

        # price
        r4 = ctk.CTkFrame(frame, fg_color="white")
        r4.pack(fill="x", padx=8, pady=4)
        ctk.CTkLabel(r4, text="Price (€):", width=90, anchor="e").pack(side="left", padx=(0, 6))
        price_entry = ctk.CTkEntry(r4)
        price_entry.insert(0, "50")
        price_entry.pack(side="left", fill="x", expand=True)

        # status
        r5 = ctk.CTkFrame(frame, fg_color="white")
        r5.pack(fill="x", padx=8, pady=4)
        ctk.CTkLabel(r5, text="Status:", width=90, anchor="e").pack(side="left", padx=(0, 6))
        status_var = ctk.StringVar(value="available")
        status_menu = ctk.CTkOptionMenu(
            r5,
            values=["available", "occupied", "needs_cleaning", "maintenance", "out_of_order"],
            variable=status_var,
            width=140,
        )
        status_menu.pack(side="left")

        def save_new():
            number = num_entry.get().strip()
            rtype = type_entry.get().strip() or "Standard"
            try:
                floor = int(floor_entry.get().strip() or "0")
            except ValueError:
                messagebox.showerror("Invalid", "Floor must be an integer.")
                return
            try:
                price = float(price_entry.get().strip() or "0")
            except ValueError:
                messagebox.showerror("Invalid", "Price must be a number.")
                return
            status = status_var.get()
            if not number:
                messagebox.showerror("Missing", "Room number cannot be empty.")
                return

            try:
                with get_conn() as conn:
                    conn.execute(
                        """
                        INSERT INTO rooms (room_number, type, status, price, floor)
                        VALUES (?, ?, ?, ?, ?)
                        """,
                        (number, rtype, status, price, floor),
                    )
            except Exception as e:
                messagebox.showerror("DB error", f"Failed to insert room:\n{e}")
                return

            win.destroy()
            self._reload_rooms()

        ctk.CTkButton(
            frame,
            text="Save",
            width=100,
            fg_color="#10B981",
            hover_color="#059669",
            command=save_new,
        ).pack(pady=10)

    # =======================================================================
    # RESTAURANT MANAGER (A – already mostly done)
    # =======================================================================

    def _build_restaurant_panel(self):
        self._clear_content()
        self._menu_rows.clear()
        self._table_rows.clear()

        wrapper = ctk.CTkFrame(self.content, fg_color="#F3F4F6")
        wrapper.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(
            wrapper,
            text="Restaurant Manager",
            font=ctk.CTkFont(size=22, weight="bold"),
            anchor="w",
        ).pack(anchor="w", pady=(0, 8))

        ctk.CTkLabel(
            wrapper,
            text=(
                "Here the manager can edit the restaurant menu, prices and tables.\n"
                "Changes are saved directly into the database and will be visible in the "
                "Restaurant (waiter) UI."
            ),
            font=ctk.CTkFont(size=13),
            text_color="#4B5563",
            justify="left",
        ).pack(anchor="w", pady=(0, 14))

        # Button to open the actual waiter UI
        ctk.CTkButton(
            wrapper,
            text="Open Restaurant UI",
            width=160,
            fg_color="#3B82F6",
            hover_color="#2563EB",
            command=self.open_restaurant_ui,
        ).pack(anchor="w", pady=(0, 16))

        tabs = ctk.CTkTabview(wrapper)
        tabs.pack(fill="both", expand=True, pady=(10, 0))

        menu_tab = tabs.add("Menu items")
        tables_tab = tabs.add("Tables")

        # ---- MENU TAB ----
        menu_top = ctk.CTkFrame(menu_tab, fg_color="#F3F4F6")
        menu_top.pack(fill="x", padx=10, pady=(10, 0))

        ctk.CTkButton(
            menu_top,
            text="+ Add menu item",
            width=150,
            fg_color="#10B981",
            hover_color="#059669",
            command=self._open_add_menu_dialog,
        ).pack(side="left", padx=(0, 10), pady=4)

        self.menu_list_frame = ctk.CTkScrollableFrame(menu_tab, fg_color="#F3F4F6")
        self.menu_list_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # ---- TABLES TAB ----
        tables_top = ctk.CTkFrame(tables_tab, fg_color="#F3F4F6")
        tables_top.pack(fill="x", padx=10, pady=(10, 0))

        ctk.CTkButton(
            tables_top,
            text="+ Add table",
            width=150,
            fg_color="#10B981",
            hover_color="#059669",
            command=self._open_add_table_dialog,
        ).pack(side="left", padx=(0, 10), pady=4)

        self.tables_list_frame = ctk.CTkScrollableFrame(tables_tab, fg_color="#F3F4F6")
        self.tables_list_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # load data from DB (via backend.restaurant_admin)
        self._reload_menu_items()
        self._reload_tables()

    # ----- MENU HELPERS -----

    def _reload_menu_items(self):
        for child in self.menu_list_frame.winfo_children():
            child.destroy()
        self._menu_rows.clear()

        try:
            items = restaurant_admin.get_menu_items()
        except Exception as e:
            messagebox.showerror("DB error", f"Failed to load menu items:\n{e}")
            return

        if not items:
            ctk.CTkLabel(
                self.menu_list_frame,
                text="No menu items yet. Use '+ Add menu item' to create one.",
                text_color="#6B7280",
            ).pack(pady=10)
            return

        # header row
        header = ctk.CTkFrame(self.menu_list_frame, fg_color="#E5E7EB", corner_radius=8)
        header.pack(fill="x", padx=4, pady=(0, 4))

        def h(txt, w):
            ctk.CTkLabel(
                header, text=txt, width=w, font=ctk.CTkFont(size=13, weight="bold")
            ).pack(side="left", padx=4, pady=4)

        h("ID", 40)
        h("Category", 140)
        h("Name", 300)
        h("Price (€)", 100)

        # data rows
        for item in items:
            self._add_menu_row(item)

    def _add_menu_row(self, item):
        row = ctk.CTkFrame(self.menu_list_frame, fg_color="white", corner_radius=8)
        row.pack(fill="x", padx=4, pady=2)

        item_id = item["item_id"]

        ctk.CTkLabel(row, text=str(item_id), width=40).pack(side="left", padx=4, pady=4)

        cat_entry = ctk.CTkEntry(row, width=140)
        cat_entry.insert(0, item.get("category", ""))
        cat_entry.pack(side="left", padx=4, pady=4)

        name_entry = ctk.CTkEntry(row, width=300)
        name_entry.insert(0, item.get("name", ""))
        name_entry.pack(side="left", padx=4, pady=4)

        price_entry = ctk.CTkEntry(row, width=80)
        price_entry.insert(0, str(item.get("price", 0)))
        price_entry.pack(side="left", padx=4, pady=4)

        btn_save = ctk.CTkButton(
            row,
            text="Save",
            width=70,
            fg_color="#3B82F6",
            hover_color="#2563EB",
            command=lambda iid=item_id: self._save_menu_row(iid),
        )
        btn_save.pack(side="left", padx=4, pady=4)

        btn_del = ctk.CTkButton(
            row,
            text="Delete",
            width=70,
            fg_color="#DC2626",
            hover_color="#B91C1C",
            command=lambda iid=item_id: self._delete_menu_row(iid),
        )
        btn_del.pack(side="left", padx=4, pady=4)

        self._menu_rows[item_id] = {
            "row": row,
            "category": cat_entry,
            "name": name_entry,
            "price": price_entry,
        }

    def _save_menu_row(self, item_id: int):
        fields = self._menu_rows.get(item_id)
        if not fields:
            return

        cat = fields["category"].get().strip()
        name = fields["name"].get().strip()
        try:
            price = float(fields["price"].get().strip() or "0")
        except ValueError:
            messagebox.showerror("Invalid value", "Price must be a number.")
            return

        try:
            restaurant_admin.update_menu_item(item_id, cat, name, price)
        except Exception as e:
            messagebox.showerror("DB error", f"Failed to save menu item:\n{e}")
            return

        messagebox.showinfo("Saved", "Menu item updated.")
        self._reload_menu_items()

    def _delete_menu_row(self, item_id: int):
        if not messagebox.askyesno("Delete", "Delete this menu item?"):
            return
        try:
            restaurant_admin.delete_menu_item(item_id)
        except Exception as e:
            messagebox.showerror("DB error", f"Failed to delete menu item:\n{e}")
            return
        self._reload_menu_items()

    def _open_add_menu_dialog(self):
        win = ctk.CTkToplevel(self)
        win.title("Add menu item")
        win.geometry("380x220")
        win.grab_set()

        frame = ctk.CTkFrame(win)
        frame.pack(expand=True, fill="both", padx=10, pady=10)

        ctk.CTkLabel(frame, text="New menu item", font=ctk.CTkFont(size=16, weight="bold")).pack(
            pady=(6, 10)
        )

        row1 = ctk.CTkFrame(frame, fg_color="white")
        row1.pack(fill="x", padx=8, pady=4)
        ctk.CTkLabel(row1, text="Category:", width=80, anchor="e").pack(
            side="left", padx=(0, 6)
        )
        cat_entry = ctk.CTkEntry(row1)
        cat_entry.pack(side="left", fill="x", expand=True)

        row2 = ctk.CTkFrame(frame, fg_color="white")
        row2.pack(fill="x", padx=8, pady=4)
        ctk.CTkLabel(row2, text="Name:", width=80, anchor="e").pack(side="left", padx=(0, 6))
        name_entry = ctk.CTkEntry(row2)
        name_entry.pack(side="left", fill="x", expand=True)

        row3 = ctk.CTkFrame(frame, fg_color="white")
        row3.pack(fill="x", padx=8, pady=4)
        ctk.CTkLabel(row3, text="Price (€):", width=80, anchor="e").pack(
            side="left", padx=(0, 6)
        )
        price_entry = ctk.CTkEntry(row3)
        price_entry.pack(side="left", fill="x", expand=True)

        def save_new():
            cat = cat_entry.get().strip()
            name = name_entry.get().strip()
            if not name:
                messagebox.showerror("Missing", "Please enter a name.")
                return
            try:
                price = float(price_entry.get().strip() or "0")
            except ValueError:
                messagebox.showerror("Invalid", "Price must be a number.")
                return

            try:
                restaurant_admin.insert_menu_item(cat, name, price)
            except Exception as e:
                messagebox.showerror("DB error", f"Failed to insert menu item:\n{e}")
                return

            win.destroy()
            self._reload_menu_items()

        ctk.CTkButton(
            frame,
            text="Save",
            width=100,
            fg_color="#10B981",
            hover_color="#059669",
            command=save_new,
        ).pack(pady=10)

    # ----- TABLE HELPERS -----

    def _reload_tables(self):
        for child in self.tables_list_frame.winfo_children():
            child.destroy()
        self._table_rows.clear()

        try:
            tables = restaurant_admin.get_tables()
        except Exception as e:
            messagebox.showerror("DB error", f"Failed to load tables:\n{e}")
            return

        if not tables:
            ctk.CTkLabel(
                self.tables_list_frame,
                text="No tables yet. Use '+ Add table' to create one.",
                text_color="#6B7280",
            ).pack(pady=10)
            return

        header = ctk.CTkFrame(self.tables_list_frame, fg_color="#E5E7EB", corner_radius=8)
        header.pack(fill="x", padx=4, pady=(0, 4))

        def h(txt, w):
            ctk.CTkLabel(
                header, text=txt, width=w, font=ctk.CTkFont(size=13, weight="bold")
            ).pack(side="left", padx=4, pady=4)

        h("ID", 40)
        h("Table #", 80)
        h("Status", 140)
        h("Seats", 70)

        for tbl in tables:
            self._add_table_row(tbl)

    def _add_table_row(self, tbl):
        row = ctk.CTkFrame(self.tables_list_frame, fg_color="white", corner_radius=8)
        row.pack(fill="x", padx=4, pady=2)

        table_id = tbl["table_id"]

        ctk.CTkLabel(row, text=str(table_id), width=40).pack(side="left", padx=4, pady=4)

        num_entry = ctk.CTkEntry(row, width=80)
        num_entry.insert(0, str(tbl.get("table_number", "")))
        num_entry.pack(side="left", padx=4, pady=4)

        status_var = ctk.StringVar(value=tbl.get("status", "available"))
        status_menu = ctk.CTkOptionMenu(
            row,
            values=["available", "reserved", "occupied", "maintenance"],
            variable=status_var,
            width=140,
        )
        status_menu.pack(side="left", padx=4, pady=4)

        seats_entry = ctk.CTkEntry(row, width=70)
        seats_entry.insert(0, str(tbl.get("seats", 0)))
        seats_entry.pack(side="left", padx=4, pady=4)

        btn_save = ctk.CTkButton(
            row,
            text="Save",
            width=70,
            fg_color="#3B82F6",
            hover_color="#2563EB",
            command=lambda tid=table_id: self._save_table_row(tid),
        )
        btn_save.pack(side="left", padx=4, pady=4)

        btn_del = ctk.CTkButton(
            row,
            text="Delete",
            width=70,
            fg_color="#DC2626",
            hover_color="#B91C1C",
            command=lambda tid=table_id: self._delete_table_row(tid),
        )
        btn_del.pack(side="left", padx=4, pady=4)

        self._table_rows[table_id] = {
            "row": row,
            "number": num_entry,
            "status_var": status_var,
            "seats": seats_entry,
        }

    def _save_table_row(self, table_id: int):
        fields = self._table_rows.get(table_id)
        if not fields:
            return

        try:
            number = int(fields["number"].get().strip())
        except ValueError:
            messagebox.showerror("Invalid value", "Table number must be an integer.")
            return

        try:
            seats = int(fields["seats"].get().strip() or "0")
        except ValueError:
            messagebox.showerror("Invalid value", "Seats must be an integer.")
            return

        status = fields["status_var"].get()

        try:
            restaurant_admin.update_table(table_id, number, status, seats)
        except Exception as e:
            messagebox.showerror("DB error", f"Failed to save table:\n{e}")
            return

        messagebox.showinfo("Saved", "Table updated.")
        self._reload_tables()

    def _delete_table_row(self, table_id: int):
        if not messagebox.askyesno("Delete", "Delete this table?"):
            return
        try:
            restaurant_admin.delete_table(table_id)
        except Exception as e:
            messagebox.showerror("DB error", f"Failed to delete table:\n{e}")
            return
        self._reload_tables()

    def _open_add_table_dialog(self):
        win = ctk.CTkToplevel(self)
        win.title("Add table")
        win.geometry("320x220")
        win.grab_set()

        frame = ctk.CTkFrame(win)
        frame.pack(expand=True, fill="both", padx=10, pady=10)

        ctk.CTkLabel(frame, text="New table", font=ctk.CTkFont(size=16, weight="bold")).pack(
            pady=(6, 10)
        )

        row1 = ctk.CTkFrame(frame, fg_color="white")
        row1.pack(fill="x", padx=8, pady=4)
        ctk.CTkLabel(row1, text="Table #:", width=80, anchor="e").pack(
            side="left", padx=(0, 6)
        )
        num_entry = ctk.CTkEntry(row1)
        num_entry.pack(side="left", fill="x", expand=True)

        row2 = ctk.CTkFrame(frame, fg_color="white")
        row2.pack(fill="x", padx=8, pady=4)
        ctk.CTkLabel(row2, text="Status:", width=80, anchor="e").pack(
            side="left", padx=(0, 6)
        )
        status_var = ctk.StringVar(value="available")
        status_menu = ctk.CTkOptionMenu(
            row2,
            values=["available", "reserved", "occupied", "maintenance"],
            variable=status_var,
            width=140,
        )
        status_menu.pack(side="left")

        row3 = ctk.CTkFrame(frame, fg_color="white")
        row3.pack(fill="x", padx=8, pady=4)
        ctk.CTkLabel(row3, text="Seats:", width=80, anchor="e").pack(
            side="left", padx=(0, 6)
        )
        seats_entry = ctk.CTkEntry(row3)
        seats_entry.pack(side="left", fill="x", expand=True)

        def save_new():
            try:
                number = int(num_entry.get().strip())
            except ValueError:
                messagebox.showerror("Invalid", "Table number must be an integer.")
                return

            try:
                seats = int(seats_entry.get().strip() or "0")
            except ValueError:
                messagebox.showerror("Invalid", "Seats must be an integer.")
                return

            status = status_var.get()

            try:
                restaurant_admin.insert_table(number, status, seats)
            except Exception as e:
                messagebox.showerror("DB error", f"Failed to insert table:\n{e}")
                return

            win.destroy()
            self._reload_tables()

        ctk.CTkButton(
            frame,
            text="Save",
            width=100,
            fg_color="#10B981",
            hover_color="#059669",
            command=save_new,
        ).pack(pady=10)

    # =======================================================================
    # CLEANING MANAGER (E)
    # =======================================================================

    def _build_cleaning_panel(self):
        self._clear_content()
        self._cleaning_rows.clear()

        wrapper = ctk.CTkFrame(self.content, fg_color="#F3F4F6")
        wrapper.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(
            wrapper,
            text="Cleaning Manager",
            font=ctk.CTkFont(size=22, weight="bold"),
            anchor="w",
        ).pack(anchor="w", pady=(0, 8))

        ctk.CTkLabel(
            wrapper,
            text=(
                "Here the manager can see and manage cleaning tasks.\n"
                "Assign rooms to cleaners, update status and notes. "
                "Data is stored in cleaning_tasks table."
            ),
            font=ctk.CTkFont(size=13),
            text_color="#4B5563",
            justify="left",
        ).pack(anchor="w", pady=(0, 14))

        ctk.CTkButton(
            wrapper,
            text="Open Cleaning UI",
            width=160,
            fg_color="#F59E0B",
            hover_color="#D97706",
            command=self.open_cleaning_ui,
        ).pack(anchor="w", pady=(0, 16))

        top = ctk.CTkFrame(wrapper, fg_color="#F3F4F6")
        top.pack(fill="x", padx=10, pady=(0, 4))

        ctk.CTkButton(
            top,
            text="+ Add cleaning task",
            width=190,
            fg_color="#10B981",
            hover_color="#059669",
            command=self._open_add_cleaning_dialog,
        ).pack(side="left", padx=(0, 10), pady=4)

        self.cleaning_list_frame = ctk.CTkScrollableFrame(wrapper, fg_color="#F3F4F6")
        self.cleaning_list_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # build choices for rooms & cleaners
        self._load_cleaning_choices()
        self._reload_cleaning_tasks()

    def _load_cleaning_choices(self):
        # rooms
        self._clean_rooms_choices = []
        self._clean_cleaner_choices = []

        try:
            with get_conn() as conn:
                cur = conn.execute(
                    "SELECT room_id, room_number, floor FROM rooms ORDER BY floor, room_number"
                )
                for r in cur.fetchall():
                    label = f"{r['room_number']} (floor {r['floor']})"
                    self._clean_rooms_choices.append((r["room_id"], label))

                cur2 = conn.execute(
                    """
                    SELECT user_id, username, COALESCE(full_name, '') AS full_name
                    FROM users
                    WHERE LOWER(role) LIKE 'clean%' OR LOWER(role) LIKE '%clean%'
                    ORDER BY username
                    """
                )
                for u in cur2.fetchall():
                    name = u["full_name"] or u["username"]
                    label = f"{name} (id {u['user_id']})"
                    self._clean_cleaner_choices.append((u["user_id"], label))
        except Exception:
            # it's fine if there are no cleaners/rooms yet
            pass

    def _reload_cleaning_tasks(self):
        for child in self.cleaning_list_frame.winfo_children():
            child.destroy()
        self._cleaning_rows.clear()

        try:
            with get_conn() as conn:
                cur = conn.execute(
                    """
                    SELECT t.task_id,
                           t.room_id,
                           r.room_number,
                           t.assigned_to,
                           u.full_name AS assigned_name,
                           t.notes,
                           t.status,
                           t.created_at,
                           t.completed_at
                    FROM cleaning_tasks t
                    LEFT JOIN rooms r ON t.room_id = r.room_id
                    LEFT JOIN users u ON t.assigned_to = u.user_id
                    ORDER BY t.created_at DESC
                    """
                )
                rows = cur.fetchall()
        except Exception as e:
            messagebox.showerror("DB error", f"Failed to load cleaning tasks:\n{e}")
            return

        if not rows:
            ctk.CTkLabel(
                self.cleaning_list_frame,
                text="No cleaning tasks yet. Use '+ Add cleaning task' to create one.",
                text_color="#6B7280",
            ).pack(pady=10)
            return

        header = ctk.CTkFrame(self.cleaning_list_frame, fg_color="#E5E7EB", corner_radius=8)
        header.pack(fill="x", padx=4, pady=(0, 4))

        def h(txt, w):
            ctk.CTkLabel(
                header, text=txt, width=w, font=ctk.CTkFont(size=13, weight="bold")
            ).pack(side="left", padx=4, pady=4)

        h("ID", 40)
        h("Room", 130)
        h("Cleaner", 180)
        h("Status", 120)
        h("Notes", 280)

        for t in rows:
            self._add_cleaning_row(t)

    def _add_cleaning_row(self, t):
        row = ctk.CTkFrame(self.cleaning_list_frame, fg_color="white", corner_radius=8)
        row.pack(fill="x", padx=4, pady=2)

        task_id = t["task_id"]

        ctk.CTkLabel(row, text=str(task_id), width=40).pack(side="left", padx=4, pady=4)

        # room selector
        room_var = ctk.StringVar()
        room_options = [label for (_id, label) in self._clean_rooms_choices]
        if t["room_id"]:
            label = next(
                (lbl for (_id, lbl) in self._clean_rooms_choices if _id == t["room_id"]),
                "Unknown room",
            )
        else:
            label = "Select room"
        room_var.set(label if room_options else "No rooms")

        room_menu = ctk.CTkOptionMenu(
            row,
            values=room_options or ["No rooms"],
            variable=room_var,
            width=130,
        )
        room_menu.pack(side="left", padx=4, pady=4)

        # cleaner selector
        cleaner_var = ctk.StringVar()
        cleaner_options = [label for (_id, label) in self._clean_cleaner_choices]
        if t["assigned_to"]:
            label = next(
                (lbl for (_id, lbl) in self._clean_cleaner_choices if _id == t["assigned_to"]),
                "Unknown cleaner",
            )
        else:
            label = "Unassigned"
        cleaner_var.set(label if cleaner_options else "No cleaners")

        cleaner_menu = ctk.CTkOptionMenu(
            row,
            values=cleaner_options or ["No cleaners"],
            variable=cleaner_var,
            width=180,
        )
        cleaner_menu.pack(side="left", padx=4, pady=4)

        status_var = ctk.StringVar(value=t["status"] or "pending")
        status_menu = ctk.CTkOptionMenu(
            row,
            values=["pending", "in_progress", "done", "cancelled"],
            variable=status_var,
            width=120,
        )
        status_menu.pack(side="left", padx=4, pady=4)

        notes_entry = ctk.CTkEntry(row, width=280)
        notes_entry.insert(0, t["notes"] or "")
        notes_entry.pack(side="left", padx=4, pady=4)

        btn_save = ctk.CTkButton(
            row,
            text="Save",
            width=70,
            fg_color="#3B82F6",
            hover_color="#2563EB",
            command=lambda tid=task_id: self._save_cleaning_row(tid),
        )
        btn_save.pack(side="left", padx=4, pady=4)

        btn_del = ctk.CTkButton(
            row,
            text="Delete",
            width=70,
            fg_color="#DC2626",
            hover_color="#B91C1C",
            command=lambda tid=task_id: self._delete_cleaning_row(tid),
        )
        btn_del.pack(side="left", padx=4, pady=4)

        self._cleaning_rows[task_id] = {
            "row": row,
            "room_var": room_var,
            "cleaner_var": cleaner_var,
            "status_var": status_var,
            "notes_entry": notes_entry,
        }

    def _resolve_room_id_from_label(self, label: str) -> Optional[int]:
        for rid, lbl in self._clean_rooms_choices:
            if lbl == label:
                return rid
        return None

    def _resolve_cleaner_id_from_label(self, label: str) -> Optional[int]:
        for uid, lbl in self._clean_cleaner_choices:
            if lbl == label:
                return uid
        return None

    def _save_cleaning_row(self, task_id: int):
        fields = self._cleaning_rows.get(task_id)
        if not fields:
            return

        room_label = fields["room_var"].get()
        cleaner_label = fields["cleaner_var"].get()
        status = fields["status_var"].get()
        notes = fields["notes_entry"].get().strip()

        room_id = self._resolve_room_id_from_label(room_label)
        cleaner_id = self._resolve_cleaner_id_from_label(cleaner_label)

        try:
            with get_conn() as conn:
                conn.execute(
                    """
                    UPDATE cleaning_tasks
                    SET room_id=?, assigned_to=?, status=?, notes=?
                    WHERE task_id=?
                    """,
                    (room_id, cleaner_id, status, notes, task_id),
                )
        except Exception as e:
            messagebox.showerror("DB error", f"Failed to save cleaning task:\n{e}")
            return

        messagebox.showinfo("Saved", "Cleaning task updated.")
        self._reload_cleaning_tasks()

    def _delete_cleaning_row(self, task_id: int):
        if not messagebox.askyesno("Delete", "Delete this cleaning task?"):
            return
        try:
            with get_conn() as conn:
                conn.execute("DELETE FROM cleaning_tasks WHERE task_id=?", (task_id,))
        except Exception as e:
            messagebox.showerror("DB error", f"Failed to delete cleaning task:\n{e}")
            return
        self._reload_cleaning_tasks()

    def _open_add_cleaning_dialog(self):
        win = ctk.CTkToplevel(self)
        win.title("Add cleaning task")
        win.geometry("420x260")
        win.grab_set()

        frame = ctk.CTkFrame(win)
        frame.pack(expand=True, fill="both", padx=10, pady=10)

        ctk.CTkLabel(
            frame, text="New cleaning task", font=ctk.CTkFont(size=16, weight="bold")
        ).pack(pady=(6, 10))

        # room
        r1 = ctk.CTkFrame(frame, fg_color="white")
        r1.pack(fill="x", padx=8, pady=4)
        ctk.CTkLabel(r1, text="Room:", width=90, anchor="e").pack(side="left", padx=(0, 6))

        room_var = ctk.StringVar()
        room_options = [label for (_id, label) in self._clean_rooms_choices] or ["No rooms"]
        if room_options:
            room_var.set(room_options[0])
        room_menu = ctk.CTkOptionMenu(
            r1,
            values=room_options,
            variable=room_var,
            width=200,
        )
        room_menu.pack(side="left")

        # cleaner
        r2 = ctk.CTkFrame(frame, fg_color="white")
        r2.pack(fill="x", padx=8, pady=4)
        ctk.CTkLabel(r2, text="Cleaner:", width=90, anchor="e").pack(side="left", padx=(0, 6))

        cleaner_var = ctk.StringVar()
        cleaner_options = [label for (_id, label) in self._clean_cleaner_choices] or ["Unassigned"]
        cleaner_var.set(cleaner_options[0])
        cleaner_menu = ctk.CTkOptionMenu(
            r2,
            values=cleaner_options,
            variable=cleaner_var,
            width=200,
        )
        cleaner_menu.pack(side="left")

        # status
        r3 = ctk.CTkFrame(frame, fg_color="white")
        r3.pack(fill="x", padx=8, pady=4)
        ctk.CTkLabel(r3, text="Status:", width=90, anchor="e").pack(side="left", padx=(0, 6))
        status_var = ctk.StringVar(value="pending")
        status_menu = ctk.CTkOptionMenu(
            r3,
            values=["pending", "in_progress", "done", "cancelled"],
            variable=status_var,
            width=140,
        )
        status_menu.pack(side="left")

        # notes
        r4 = ctk.CTkFrame(frame, fg_color="white")
        r4.pack(fill="x", padx=8, pady=4)
        ctk.CTkLabel(r4, text="Notes:", width=90, anchor="e").pack(side="left", padx=(0, 6))
        notes_entry = ctk.CTkEntry(r4)
        notes_entry.pack(side="left", fill="x", expand=True)

        def save_new():
            room_label = room_var.get()
            cleaner_label = cleaner_var.get()
            status = status_var.get()
            notes = notes_entry.get().strip()

            room_id = self._resolve_room_id_from_label(room_label)
            cleaner_id = self._resolve_cleaner_id_from_label(cleaner_label)

            try:
                with get_conn() as conn:
                    conn.execute(
                        """
                        INSERT INTO cleaning_tasks (room_id, assigned_to, notes, status, created_at)
                        VALUES (?, ?, ?, ?, datetime('now'))
                        """,
                        (room_id, cleaner_id, notes, status),
                    )
            except Exception as e:
                messagebox.showerror("DB error", f"Failed to insert cleaning task:\n{e}")
                return

            win.destroy()
            self._reload_cleaning_tasks()

        ctk.CTkButton(
            frame,
            text="Save",
            width=100,
            fg_color="#10B981",
            hover_color="#059669",
            command=save_new,
        ).pack(pady=10)

    # =======================================================================
    # STAFF & USERS (A + B – CRUD on users table)
    # =======================================================================

    def _build_staff_panel(self):
        self._clear_content()
        self._user_rows.clear()

        wrapper = ctk.CTkFrame(self.content, fg_color="#F3F4F6")
        wrapper.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(
            wrapper,
            text="Staff & Users",
            font=ctk.CTkFont(size=22, weight="bold"),
            anchor="w",
        ).pack(anchor="w", pady=(0, 10))

        ctk.CTkLabel(
            wrapper,
            text="Manage login accounts, roles and reset passwords.",
            font=ctk.CTkFont(size=13),
            text_color="#4B5563",
        ).pack(anchor="w", pady=(0, 14))

        top = ctk.CTkFrame(wrapper, fg_color="#F3F4F6")
        top.pack(fill="x", padx=10, pady=(0, 4))

        ctk.CTkButton(
            top,
            text="+ Add user",
            width=140,
            fg_color="#10B981",
            hover_color="#059669",
            command=self._open_add_user_dialog,
        ).pack(side="left", padx=(0, 10), pady=4)

        self.users_list_frame = ctk.CTkScrollableFrame(wrapper, fg_color="#F3F4F6")
        self.users_list_frame.pack(fill="both", expand=True, padx=10, pady=10)

        self._reload_users()

    def _reload_users(self):
        for child in self.users_list_frame.winfo_children():
            child.destroy()
        self._user_rows.clear()

        try:
            with get_conn() as conn:
                cur = conn.execute(
                    """
                    SELECT user_id, username, password, full_name, role
                    FROM users
                    ORDER BY username
                    """
                )
                rows = cur.fetchall()
        except Exception as e:
            messagebox.showerror("DB error", f"Failed to load users:\n{e}")
            return

        header = ctk.CTkFrame(self.users_list_frame, fg_color="#E5E7EB", corner_radius=8)
        header.pack(fill="x", padx=4, pady=(0, 4))

        def h(txt, w):
            ctk.CTkLabel(
                header, text=txt, width=w, font=ctk.CTkFont(size=13, weight="bold")
            ).pack(side="left", padx=4, pady=4)

        h("ID", 40)
        h("Username", 140)
        h("Full name", 200)
        h("Role", 160)

        if not rows:
            ctk.CTkLabel(
                self.users_list_frame,
                text="No users yet. Use '+ Add user' to create one.",
                text_color="#6B7280",
            ).pack(pady=10)
            return

        for u in rows:
            self._add_user_row(u)

    def _add_user_row(self, u):
        row = ctk.CTkFrame(self.users_list_frame, fg_color="white", corner_radius=8)
        row.pack(fill="x", padx=4, pady=2)

        user_id = u["user_id"]

        ctk.CTkLabel(row, text=str(user_id), width=40).pack(side="left", padx=4, pady=4)

        ctk.CTkLabel(row, text=u["username"], width=140, anchor="w").pack(
            side="left", padx=4, pady=4
        )

        full_entry = ctk.CTkEntry(row, width=200)
        full_entry.insert(0, u["full_name"] or "")
        full_entry.pack(side="left", padx=4, pady=4)

        roles = [
            "Receptionist",
            "Bar & Restaurant",
            "Waiter",
            "Restaurant",
            "Bar",
            "Cleaning",
            "Finance",
            "Manager",
        ]
        role_var = ctk.StringVar(value=u["role"] or "Receptionist")
        role_menu = ctk.CTkOptionMenu(
            row,
            values=roles,
            variable=role_var,
            width=160,
        )
        role_menu.pack(side="left", padx=4, pady=4)

        btn_reset = ctk.CTkButton(
            row,
            text="Reset PW",
            width=80,
            fg_color="#F59E0B",
            hover_color="#D97706",
            command=lambda uid=user_id: self._reset_user_password(uid),
        )
        btn_reset.pack(side="left", padx=4, pady=4)

        btn_save = ctk.CTkButton(
            row,
            text="Save",
            width=70,
            fg_color="#3B82F6",
            hover_color="#2563EB",
            command=lambda uid=user_id: self._save_user_row(uid),
        )
        btn_save.pack(side="left", padx=4, pady=4)

        btn_del = ctk.CTkButton(
            row,
            text="Delete",
            width=70,
            fg_color="#DC2626",
            hover_color="#B91C1C",
            command=lambda uid=user_id: self._delete_user_row(uid),
        )
        btn_del.pack(side="left", padx=4, pady=4)

        self._user_rows[user_id] = {
            "row": row,
            "full_name": full_entry,
            "role_var": role_var,
        }

    def _save_user_row(self, user_id: int):
        fields = self._user_rows.get(user_id)
        if not fields:
            return

        full_name = fields["full_name"].get().strip()
        role = fields["role_var"].get()

        try:
            with get_conn() as conn:
                conn.execute(
                    "UPDATE users SET full_name=?, role=? WHERE user_id=?",
                    (full_name, role, user_id),
                )
        except Exception as e:
            messagebox.showerror("DB error", f"Failed to save user:\n{e}")
            return

        messagebox.showinfo("Saved", "User updated.")
        self._reload_users()

    def _delete_user_row(self, user_id: int):
        if not messagebox.askyesno("Delete", "Delete this user account?"):
            return

        try:
            with get_conn() as conn:
                conn.execute("DELETE FROM users WHERE user_id=?", (user_id,))
        except Exception as e:
            messagebox.showerror("DB error", f"Failed to delete user:\n{e}")
            return

        self._reload_users()

    def _reset_user_password(self, user_id: int):
        if not messagebox.askyesno(
            "Reset password",
            "Reset this user's password to '1234' ?",
        ):
            return
        try:
            with get_conn() as conn:
                conn.execute(
                    "UPDATE users SET password=? WHERE user_id=?",
                    ("1234", user_id),
                )
        except Exception as e:
            messagebox.showerror("DB error", f"Failed to reset password:\n{e}")
            return

        messagebox.showinfo("Password reset", "Password reset to '1234'.")

    def _open_add_user_dialog(self):
        win = ctk.CTkToplevel(self)
        win.title("Add user")
        win.geometry("420x260")
        win.grab_set()

        frame = ctk.CTkFrame(win)
        frame.pack(expand=True, fill="both", padx=10, pady=10)

        ctk.CTkLabel(
            frame, text="New user account", font=ctk.CTkFont(size=16, weight="bold")
        ).pack(pady=(6, 10))

        r1 = ctk.CTkFrame(frame, fg_color="white")
        r1.pack(fill="x", padx=8, pady=4)
        ctk.CTkLabel(r1, text="Username:", width=90, anchor="e").pack(
            side="left", padx=(0, 6)
        )
        user_entry = ctk.CTkEntry(r1)
        user_entry.pack(side="left", fill="x", expand=True)

        r2 = ctk.CTkFrame(frame, fg_color="white")
        r2.pack(fill="x", padx=8, pady=4)
        ctk.CTkLabel(r2, text="Password:", width=90, anchor="e").pack(
            side="left", padx=(0, 6)
        )
        pass_entry = ctk.CTkEntry(r2, show="●")
        pass_entry.insert(0, "1234")
        pass_entry.pack(side="left", fill="x", expand=True)

        r3 = ctk.CTkFrame(frame, fg_color="white")
        r3.pack(fill="x", padx=8, pady=4)
        ctk.CTkLabel(r3, text="Full name:", width=90, anchor="e").pack(
            side="left", padx=(0, 6)
        )
        full_entry = ctk.CTkEntry(r3)
        full_entry.pack(side="left", fill="x", expand=True)

        r4 = ctk.CTkFrame(frame, fg_color="white")
        r4.pack(fill="x", padx=8, pady=4)
        ctk.CTkLabel(r4, text="Role:", width=90, anchor="e").pack(side="left", padx=(0, 6))

        roles = [
            "Receptionist",
            "Bar & Restaurant",
            "Waiter",
            "Restaurant",
            "Bar",
            "Cleaning",
            "Finance",
            "Manager",
        ]
        role_var = ctk.StringVar(value="Receptionist")
        role_menu = ctk.CTkOptionMenu(
            r4,
            values=roles,
            variable=role_var,
            width=160,
        )
        role_menu.pack(side="left")

        def save_new():
            username = user_entry.get().strip()
            password = pass_entry.get().strip()
            full_name = full_entry.get().strip()
            role = role_var.get()

            if not username or not password:
                messagebox.showerror("Missing", "Username and password are required.")
                return

            try:
                with get_conn() as conn:
                    conn.execute(
                        """
                        INSERT INTO users (username, password, full_name, role)
                        VALUES (?, ?, ?, ?)
                        """,
                        (username, password, full_name, role),
                    )
            except sqlite3.IntegrityError:
                messagebox.showerror("Error", "Username already exists.")
                return
            except Exception as e:
                messagebox.showerror("DB error", f"Failed to add user:\n{e}")
                return

            win.destroy()
            self._reload_users()

        ctk.CTkButton(
            frame,
            text="Save",
            width=100,
            fg_color="#10B981",
            hover_color="#059669",
            command=save_new,
        ).pack(pady=10)

    # =======================================================================
    # SETTINGS PANEL (THEME + HOTEL NAME)
    # =======================================================================

    def _build_settings_panel(self):
        self._clear_content()

        wrapper = ctk.CTkFrame(self.content, fg_color="#F3F4F6")
        wrapper.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(
            wrapper,
            text="Settings",
            font=ctk.CTkFont(size=22, weight="bold"),
            anchor="w",
        ).pack(anchor="w", pady=(0, 10))

        ctk.CTkLabel(
            wrapper,
            text="General application settings (demo version).",
            font=ctk.CTkFont(size=13),
            text_color="#4B5563",
        ).pack(anchor="w", pady=(0, 20))

        # Theme selector
        theme_frame = ctk.CTkFrame(wrapper, fg_color="white", corner_radius=16)
        theme_frame.pack(fill="x", pady=(0, 16))

        ctk.CTkLabel(
            theme_frame,
            text="Theme",
            font=ctk.CTkFont(size=14, weight="bold"),
        ).pack(anchor="w", padx=16, pady=(10, 4))

        theme_row = ctk.CTkFrame(theme_frame, fg_color="white")
        theme_row.pack(anchor="w", padx=16, pady=(0, 10))

        def set_theme(mode: str):
            self.theme_var.set(mode)
            if mode == "Light":
                ctk.set_appearance_mode("light")
            elif mode == "Dark":
                ctk.set_appearance_mode("dark")
            else:
                ctk.set_appearance_mode("system")

        ctk.CTkRadioButton(
            theme_row,
            text="Light",
            value="Light",
            variable=self.theme_var,
            command=lambda: set_theme("Light"),
        ).pack(side="left", padx=(0, 10))

        ctk.CTkRadioButton(
            theme_row,
            text="Dark",
            value="Dark",
            variable=self.theme_var,
            command=lambda: set_theme("Dark"),
        ).pack(side="left", padx=10)

        ctk.CTkRadioButton(
            theme_row,
            text="System",
            value="System",
            variable=self.theme_var,
            command=lambda: set_theme("System"),
        ).pack(side="left", padx=10)

        # Hotel info
        hotel_frame = ctk.CTkFrame(wrapper, fg_color="white", corner_radius=16)
        hotel_frame.pack(fill="x", pady=(0, 16))

        ctk.CTkLabel(
            hotel_frame,
            text="Hotel Information",
            font=ctk.CTkFont(size=14, weight="bold"),
        ).pack(anchor="w", padx=16, pady=(10, 4))

        row = ctk.CTkFrame(hotel_frame, fg_color="white")
        row.pack(fill="x", padx=16, pady=(0, 10))

        ctk.CTkLabel(row, text="Hotel name:", width=100, anchor="e").pack(
            side="left", padx=(0, 8)
        )
        self.hotel_name_entry = ctk.CTkEntry(row, placeholder_text="My Hotel Name")
        self.hotel_name_entry.pack(side="left", fill="x", expand=True)

        # save button (demo)
        ctk.CTkButton(
            hotel_frame,
            text="Save Settings",
            width=140,
            fg_color="#3B82F6",
            hover_color="#2563EB",
            command=self._save_settings_demo,
        ).pack(anchor="e", padx=16, pady=(0, 12))

    def _save_settings_demo(self):
        name = self.hotel_name_entry.get().strip() if hasattr(self, "hotel_name_entry") else ""
        messagebox.showinfo("Settings", f"Settings saved (demo).\nHotel name: {name or 'Not set'}")

    # =======================================================================
    # OPEN OTHER UIs
    # =======================================================================

    def open_reception_ui(self):
        # open ReceptionistWindow with Manager as parent
        win = ReceptionistWindow(parent=self, user={"username": "manager"})
        win.protocol("WM_DELETE_WINDOW", win.on_window_close)

    def open_restaurant_ui(self):
        win = RestaurantWindow(parent=self, user={"username": "manager"})
        win.protocol("WM_DELETE_WINDOW", win.on_window_close)

    def open_cleaning_ui(self):
        win = CleaningWindow(parent=self, user={"username": "manager"})
        # CleaningWindow already handles on_window_close internally

    def open_finance_ui(self):
        win = FinanceWindow(parent=self, user={"username": "manager"})
        win.protocol("WM_DELETE_WINDOW", win.on_window_close)

    # ---------- LOGOUT / CLOSE ----------

    def _logout(self):
        """Logout from manager back to login window."""
        self.destroy()
        if self.parent is not None:
            try:
                self.parent.deiconify()
            except Exception:
                pass

    def on_window_close(self):
        # Same as logout when X is pressed
        self._logout()
