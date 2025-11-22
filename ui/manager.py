# ui/manager.py

import customtkinter as ctk
from tkinter import messagebox

from ui.receptionist import ReceptionistWindow
from ui.restaurant import RestaurantWindow
from ui.cleaning import CleaningWindow
from ui.finance import FinanceWindow


class ManagerWindow(ctk.CTkToplevel):
    """
    Manager / Admin UI

    - Sidebar navigation with manager sections
    - Dashboard shows stats + buttons to open department UIs
    - Logout returns to LoginWindow
    """

    def __init__(self, parent=None, user=None):
        super().__init__()

        self.parent = parent          # LoginWindow
        self.user = user or {"username": "manager"}

        # Make modal over login
        if self.parent is not None:
            self.transient(self.parent)
            self.grab_set()

        self.title("InnKeeper • Manager")
        self.geometry("1300x780")
        self.minsize(1100, 650)

        # default CTK theme
        ctk.set_appearance_mode("light")

        # current theme + current page
        self.theme_var = ctk.StringVar(value="Light")
        self.current_page = "dashboard"

        # main containers (will be created in _build_layout)
        self.sidebar: ctk.CTkFrame | None = None
        self.content: ctk.CTkFrame | None = None

        # build layout
        self._build_layout()

        # when manager window is open, hide login
        if self.parent is not None:
            try:
                self.parent.withdraw()
            except Exception:
                pass

        self.protocol("WM_DELETE_WINDOW", self.on_window_close)

    # ---------- LAYOUT ROOT ----------

    def _build_layout(self):
        # main 2-column layout
        self.sidebar = ctk.CTkFrame(self, fg_color="#111827", corner_radius=0, width=220)
        self.sidebar.pack(side="left", fill="y")

        self.content = ctk.CTkFrame(self, fg_color="#F3F4F6")
        self.content.pack(side="right", fill="both", expand=True)

        self._build_sidebar()
        self._build_dashboard()  # default page

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

        # Sidebar sections → manager pages (NOT department UIs)
        self.btn_dashboard = nav_btn("🏠  Dashboard", self._build_dashboard)
        self.btn_rooms = nav_btn("🛏️  Rooms Manager", self._build_rooms_manager_panel)
        self.btn_restaurant = nav_btn("🍽️  Restaurant Manager", self._build_restaurant_manager_panel)
        self.btn_cleaning = nav_btn("🧹  Cleaning Manager", self._build_cleaning_manager_panel)
        self.btn_finance = nav_btn("💰  Finance Dashboard", self._build_finance_manager_panel)
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

    def _refresh_current_page(self):
        """Rebuild the current page (used after theme change)."""
        if self.current_page == "dashboard":
            self._build_dashboard()
        elif self.current_page == "rooms":
            self._build_rooms_manager_panel()
        elif self.current_page == "restaurant":
            self._build_restaurant_manager_panel()
        elif self.current_page == "cleaning":
            self._build_cleaning_manager_panel()
        elif self.current_page == "finance":
            self._build_finance_manager_panel()
        elif self.current_page == "staff":
            self._build_staff_panel()
        elif self.current_page == "settings":
            self._build_settings_panel()

    # ---------- DASHBOARD ----------

    def _build_dashboard(self):
        self.current_page = "dashboard"
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

        # Bottom area with department access buttons
        bottom = ctk.CTkFrame(wrapper, fg_color="white", corner_radius=16)
        bottom.pack(fill="both", expand=True, pady=20, padx=2)

        ctk.CTkLabel(
            bottom,
            text="Open Department UIs",
            font=ctk.CTkFont(size=15, weight="bold"),
            anchor="w",
        ).pack(anchor="w", padx=16, pady=(16, 8))

        grid = ctk.CTkFrame(bottom, fg_color="white")
        grid.pack(padx=16, pady=(0, 16), fill="x")

        def big_ui_btn(parent, text, command):
            btn = ctk.CTkButton(
                parent,
                text=text,
                height=60,
                fg_color="#3B82F6",
                hover_color="#2563EB",
                text_color="white",
                font=ctk.CTkFont(size=14, weight="bold"),
                corner_radius=12,
                command=command,
            )
            return btn

        # 2x2 layout
        btn1 = big_ui_btn(grid, "Reception UI", self.open_reception_ui)
        btn2 = big_ui_btn(grid, "Bar & Restaurant UI", self.open_restaurant_ui)
        btn3 = big_ui_btn(grid, "Cleaning Service UI", self.open_cleaning_ui)
        btn4 = big_ui_btn(grid, "Finance UI", self.open_finance_ui)

        btn1.grid(row=0, column=0, sticky="nsew", padx=6, pady=6)
        btn2.grid(row=0, column=1, sticky="nsew", padx=6, pady=6)
        btn3.grid(row=1, column=0, sticky="nsew", padx=6, pady=6)
        btn4.grid(row=1, column=1, sticky="nsew", padx=6, pady=6)

        grid.columnconfigure(0, weight=1)
        grid.columnconfigure(1, weight=1)
        grid.rowconfigure(0, weight=1)
        grid.rowconfigure(1, weight=1)

    # ---------- ROOMS MANAGER PANEL ----------

    def _build_rooms_manager_panel(self):
        self.current_page = "rooms"
        self._clear_content()

        wrapper = ctk.CTkFrame(self.content, fg_color="#F3F4F6")
        wrapper.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(
            wrapper,
            text="Rooms Manager",
            font=ctk.CTkFont(size=22, weight="bold"),
            anchor="w",
        ).pack(anchor="w", pady=(0, 10))

        ctk.CTkLabel(
            wrapper,
            text="Here you will manage room numbers, typology and prices (demo table).",
            font=ctk.CTkFont(size=13),
            text_color="#4B5563",
        ).pack(anchor="w", pady=(0, 20))

        table = ctk.CTkFrame(wrapper, fg_color="white", corner_radius=16)
        table.pack(fill="x")

        header = ctk.CTkFrame(table, fg_color="#E5E7EB", corner_radius=8)
        header.pack(fill="x", padx=10, pady=10)

        def h(txt, w):
            ctk.CTkLabel(header, text=txt, width=w,
                         font=ctk.CTkFont(size=13, weight="bold")).pack(
                side="left", padx=4, pady=4
            )

        h("Room No.", 100)
        h("Typology", 140)
        h("Price / night", 120)
        h("Status", 100)

        # demo rows
        demo_data = [
            ("101", "Single", "45 €", "Active"),
            ("102", "Double", "65 €", "Active"),
            ("201", "Suite", "120 €", "Inactive"),
        ]
        for rno, typ, price, st in demo_data:
            row = ctk.CTkFrame(table, fg_color="white", corner_radius=8)
            row.pack(fill="x", padx=10, pady=(0, 6))

            def cell(txt, w):
                ctk.CTkLabel(row, text=txt, width=w).pack(side="left", padx=4, pady=4)

            cell(rno, 100)
            cell(typ, 140)
            cell(price, 120)
            cell(st, 100)

    # ---------- RESTAURANT MANAGER PANEL ----------

    def _build_restaurant_manager_panel(self):
        self.current_page = "restaurant"
        self._clear_content()

        wrapper = ctk.CTkFrame(self.content, fg_color="#F3F4F6")
        wrapper.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(
            wrapper,
            text="Restaurant Manager",
            font=ctk.CTkFont(size=22, weight="bold"),
            anchor="w",
        ).pack(anchor="w", pady=(0, 10))

        ctk.CTkLabel(
            wrapper,
            text="Manage menu items and prices (demo table).",
            font=ctk.CTkFont(size=13),
            text_color="#4B5563",
        ).pack(anchor="w", pady=(0, 20))

        table = ctk.CTkFrame(wrapper, fg_color="white", corner_radius=16)
        table.pack(fill="x")

        header = ctk.CTkFrame(table, fg_color="#E5E7EB", corner_radius=8)
        header.pack(fill="x", padx=10, pady=10)

        def h(txt, w):
            ctk.CTkLabel(header, text=txt, width=w,
                         font=ctk.CTkFont(size=13, weight="bold")).pack(
                side="left", padx=4, pady=4
            )

        h("Item", 220)
        h("Category", 140)
        h("Price", 80)

        demo_items = [
            ("Espresso", "Hot Drink", "1.50 €"),
            ("Coca Cola 0.33L", "Cold Drink", "2.50 €"),
            ("Greek Salad", "Salad", "5.50 €"),
        ]
        for name, cat, price in demo_items:
            row = ctk.CTkFrame(table, fg_color="white", corner_radius=8)
            row.pack(fill="x", padx=10, pady=(0, 6))

            def cell(txt, w):
                ctk.CTkLabel(row, text=txt, width=w, anchor="w").pack(
                    side="left", padx=4, pady=4
                )

            cell(name, 220)
            cell(cat, 140)
            cell(price, 80)

    # ---------- CLEANING MANAGER PANEL ----------

    def _build_cleaning_manager_panel(self):
        self.current_page = "cleaning"
        self._clear_content()

        wrapper = ctk.CTkFrame(self.content, fg_color="#F3F4F6")
        wrapper.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(
            wrapper,
            text="Cleaning Manager",
            font=ctk.CTkFont(size=22, weight="bold"),
            anchor="w",
        ).pack(anchor="w", pady=(0, 10))

        ctk.CTkLabel(
            wrapper,
            text="Overview of cleaning staff and assignments (demo).",
            font=ctk.CTkFont(size=13),
            text_color="#4B5563",
        ).pack(anchor="w", pady=(0, 20))

        table = ctk.CTkFrame(wrapper, fg_color="white", corner_radius=16)
        table.pack(fill="x")

        header = ctk.CTkFrame(table, fg_color="#E5E7EB", corner_radius=8)
        header.pack(fill="x", padx=10, pady=10)

        def h(txt, w):
            ctk.CTkLabel(header, text=txt, width=w,
                         font=ctk.CTkFont(size=13, weight="bold")).pack(
                side="left", padx=4, pady=4
            )

        h("Cleaner", 200)
        h("Assigned Rooms", 200)

        demo_rows = [
            ("Cleaning Lady 1", "101, 102, 201"),
            ("Cleaning Lady 2", "103, 104, 202"),
            ("Cleaning Lady 3", "105, 106, 203"),
        ]
        for name, rooms in demo_rows:
            row = ctk.CTkFrame(table, fg_color="white", corner_radius=8)
            row.pack(fill="x", padx=10, pady=(0, 6))

            def cell(txt, w):
                ctk.CTkLabel(row, text=txt, width=w, anchor="w").pack(
                    side="left", padx=4, pady=4
                )

            cell(name, 200)
            cell(rooms, 200)

    # ---------- FINANCE MANAGER PANEL ----------

    def _build_finance_manager_panel(self):
        self.current_page = "finance"
        self._clear_content()

        wrapper = ctk.CTkFrame(self.content, fg_color="#F3F4F6")
        wrapper.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(
            wrapper,
            text="Finance Dashboard",
            font=ctk.CTkFont(size=22, weight="bold"),
            anchor="w",
        ).pack(anchor="w", pady=(0, 10))

        ctk.CTkLabel(
            wrapper,
            text="High-level financial overview (demo placeholders).",
            font=ctk.CTkFont(size=13),
            text_color="#4B5563",
        ).pack(anchor="w", pady=(0, 20))

        cards = ctk.CTkFrame(wrapper, fg_color="#F3F4F6")
        cards.pack(fill="x")

        def card(parent, title, val):
            f = ctk.CTkFrame(parent, fg_color="white", corner_radius=16)
            f.pack(side="left", fill="x", expand=True, padx=6)
            ctk.CTkLabel(f, text=title,
                         font=ctk.CTkFont(size=14, weight="bold")).pack(
                anchor="w", padx=12, pady=(10, 4)
            )
            ctk.CTkLabel(f, text=val,
                         font=ctk.CTkFont(size=18, weight="bold")).pack(
                anchor="w", padx=12, pady=(0, 10)
            )

        card(cards, "Today Revenue", "560 €")
        card(cards, "Month Revenue", "12 340 €")
        card(cards, "Pending Payments", "4")

    # ---------- STAFF & USERS (placeholder for now) ----------

    def _build_staff_panel(self):
        self.current_page = "staff"
        self._clear_content()

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
            text="(Demo) Here you will be able to add/remove users, set roles and privileges.",
            font=ctk.CTkFont(size=13),
            text_color="#4B5563",
        ).pack(anchor="w", pady=(0, 20))

        # Simple table placeholder
        table = ctk.CTkFrame(wrapper, fg_color="white", corner_radius=16)
        table.pack(fill="x")

        header = ctk.CTkFrame(table, fg_color="#E5E7EB", corner_radius=8)
        header.pack(fill="x", padx=10, pady=10)

        def h(txt, w):
            ctk.CTkLabel(header, text=txt, width=w,
                         font=ctk.CTkFont(size=13, weight="bold")).pack(
                side="left", padx=4, pady=4
            )

        h("Username", 160)
        h("Full name", 200)
        h("Role", 140)
        h("Status", 100)

        # demo row
        row = ctk.CTkFrame(table, fg_color="white", corner_radius=8)
        row.pack(fill="x", padx=10, pady=(0, 10))

        def cell(txt, w):
            ctk.CTkLabel(row, text=txt, width=w).pack(side="left", padx=4, pady=4)

        cell("manager", 160)
        cell("Main Manager", 200)
        cell("Manager", 140)
        cell("Active", 100)

    # ---------- SETTINGS PANEL (with theme + hotel name) ----------

    def _build_settings_panel(self):
        self.current_page = "settings"
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
                self.sidebar.configure(fg_color="#111827")
                self.content.configure(fg_color="#F3F4F6")
            elif mode == "Dark":
                ctk.set_appearance_mode("dark")
                self.sidebar.configure(fg_color="#020617")
                self.content.configure(fg_color="#020617")
            else:
                ctk.set_appearance_mode("system")
                self.sidebar.configure(fg_color="#111827")
                self.content.configure(fg_color="#F3F4F6")

            # rebuild current page so background/colors refresh nicely
            self._refresh_current_page()

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

    # ---------- OPEN OTHER UIs (real department windows) ----------

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
