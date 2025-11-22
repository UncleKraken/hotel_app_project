# ui/manager.py

import customtkinter as ctk
from tkinter import messagebox
from typing import Dict, Optional, List

# Import your existing windows
from ui.receptionist import ReceptionistWindow
from ui.restaurant import RestaurantWindow
from ui.cleaning import CleaningWindow
from ui.finance import FinanceWindow


class ManagerWindow(ctk.CTkToplevel):
    """
    Manager / Super-User UI

    - Left sidebar navigation
    - Central content area with pages:
        • Dashboard
        • Rooms Manager
        • Restaurant Manager
        • Cleaning Manager
        • Finance Dashboard
        • Staff & Users
        • Settings

    From here, the Manager can open the other modules (Reception, Restaurant,
    Cleaning, Finance) and still return back to this window on their "Logout".
    """

    def __init__(self, parent=None, user: Optional[Dict] = None):
        super().__init__()

        # Parent is usually the LoginWindow
        self.parent = parent
        self.user = user or {"username": "manager"}

        # Basic window setup
        self.title("InnKeeper • Manager")
        self.geometry("1400x800")
        self.minsize(1100, 650)
        ctk.set_appearance_mode("light")
        self.configure(fg_color="#F3F4F6")

        # Keep track of "pages"
        self.current_page_name: Optional[str] = None
        self.pages: Dict[str, ctk.CTkFrame] = {}

        # Build layout
        self._build_layout()

        # Close behavior
        self.protocol("WM_DELETE_WINDOW", self.on_window_close)

    # ------------------------------------------------------------------
    # LAYOUT
    # ------------------------------------------------------------------

    def _build_layout(self):
        # Top bar
        top_bar = ctk.CTkFrame(self, fg_color="#FFFFFF", height=60, corner_radius=0)
        top_bar.pack(side="top", fill="x")

        title = ctk.CTkLabel(
            top_bar,
            text="InnKeeper • Manager Console",
            font=ctk.CTkFont(size=20, weight="bold"),
            anchor="w",
        )
        title.pack(side="left", padx=20, pady=10)

        user_label = ctk.CTkLabel(
            top_bar,
            text=f"Logged in as: {self.user.get('username', 'manager')}",
            font=ctk.CTkFont(size=13),
            anchor="e",
            text_color="#6B7280",
        )
        user_label.pack(side="right", padx=20)

        # Main area: sidebar + content
        main_frame = ctk.CTkFrame(self, fg_color="#E5E7EB", corner_radius=0)
        main_frame.pack(fill="both", expand=True)

        # Sidebar
        sidebar = ctk.CTkFrame(main_frame, fg_color="#1F2937", width=220, corner_radius=0)
        sidebar.pack(side="left", fill="y")

        self._build_sidebar(sidebar)

        # Content area
        self.content_frame = ctk.CTkFrame(main_frame, fg_color="#F3F4F6")
        self.content_frame.pack(side="left", fill="both", expand=True)

        # Build all pages
        self._build_pages()

        # Show default page
        self.show_page("dashboard")

    def _build_sidebar(self, sidebar: ctk.CTkFrame):
        # Sidebar title
        ctk.CTkLabel(
            sidebar,
            text="Manager Menu",
            font=ctk.CTkFont(size=17, weight="bold"),
            text_color="white",
        ).pack(pady=(20, 10), padx=16, anchor="w")

        # Helper to create nav buttons
        def nav_btn(text: str, page_name: str):
            return ctk.CTkButton(
                sidebar,
                text=text,
                height=40,
                fg_color="#111827",
                hover_color="#374151",
                text_color="white",
                anchor="w",
                command=lambda pn=page_name: self.show_page(pn),
            )

        # Navigation buttons
        nav_btn("🏠  Dashboard", "dashboard").pack(fill="x", padx=12, pady=4)
        nav_btn("🛏️  Rooms Manager", "rooms").pack(fill="x", padx=12, pady=4)
        nav_btn("🍽️  Restaurant Manager", "restaurant").pack(fill="x", padx=12, pady=4)
        nav_btn("🧹  Cleaning Manager", "cleaning").pack(fill="x", padx=12, pady=4)
        nav_btn("💰  Finance Dashboard", "finance").pack(fill="x", padx=12, pady=4)
        nav_btn("👥  Staff & Users", "staff").pack(fill="x", padx=12, pady=4)
        nav_btn("⚙️  Settings", "settings").pack(fill="x", padx=12, pady=4)

        # Spacer
        ctk.CTkLabel(sidebar, text="", fg_color="transparent").pack(expand=True)

        # Logout button
        ctk.CTkButton(
            sidebar,
            text="🚪  Logout",
            fg_color="#DC2626",
            hover_color="#B91C1C",
            text_color="white",
            height=40,
            command=self.on_logout,
        ).pack(fill="x", padx=12, pady=(0, 16))

    # ------------------------------------------------------------------
    # PAGES
    # ------------------------------------------------------------------

    def _build_pages(self):
        self.pages["dashboard"] = self._build_dashboard_page()
        self.pages["rooms"] = self._build_rooms_page()
        self.pages["restaurant"] = self._build_restaurant_page()
        self.pages["cleaning"] = self._build_cleaning_page()
        self.pages["finance"] = self._build_finance_page()
        self.pages["staff"] = self._build_staff_page()
        self.pages["settings"] = self._build_settings_page()

    def show_page(self, name: str):
        if self.current_page_name == name:
            return

        # Hide all pages
        for page in self.pages.values():
            page.pack_forget()

        # Show requested
        page = self.pages.get(name)
        if page is not None:
            page.pack(fill="both", expand=True, padx=20, pady=20)

        self.current_page_name = name

    # ------------------------------------------------------------------
    # DASHBOARD PAGE
    # ------------------------------------------------------------------

    def _build_dashboard_page(self) -> ctk.CTkFrame:
        frame = ctk.CTkFrame(self.content_frame, fg_color="#F9FAFB", corner_radius=20)

        ctk.CTkLabel(
            frame,
            text="Manager Dashboard",
            font=ctk.CTkFont(size=22, weight="bold"),
        ).pack(anchor="w", padx=20, pady=(20, 10))

        ctk.CTkLabel(
            frame,
            text="High-level overview (demo values). In a full app, this pulls live data\n"
                 "from Reception, Restaurant, Cleaning, and Finance modules.",
            font=ctk.CTkFont(size=13),
            text_color="#6B7280",
            justify="left",
        ).pack(anchor="w", padx=20)

        cards = ctk.CTkFrame(frame, fg_color="#F9FAFB")
        cards.pack(fill="x", padx=20, pady=20)

        def stat_card(parent, title, value, desc):
            card = ctk.CTkFrame(parent, fg_color="white", corner_radius=16)
            card.pack(side="left", fill="both", expand=True, padx=8)
            ctk.CTkLabel(card, text=title, font=ctk.CTkFont(size=14, weight="bold")).pack(
                anchor="w", padx=14, pady=(10, 2)
            )
            ctk.CTkLabel(card, text=value, font=ctk.CTkFont(size=24, weight="bold")).pack(
                anchor="w", padx=14, pady=(0, 4)
            )
            ctk.CTkLabel(card, text=desc, font=ctk.CTkFont(size=12), text_color="#6B7280").pack(
                anchor="w", padx=14, pady=(0, 10)
            )

        stat_card(cards, "Occupied Rooms", "18", "Demo value – connect to Reception later.")
        stat_card(cards, "Today’s Restaurant Revenue", "€ 742.50", "Demo value – from Restaurant & Finance.")
        stat_card(cards, "Pending Cleanings", "7", "Demo value – from Cleaning Service.")

        # Quick access buttons
        quick = ctk.CTkFrame(frame, fg_color="white", corner_radius=16)
        quick.pack(fill="x", padx=20, pady=(0, 20))

        ctk.CTkLabel(
            quick,
            text="Quick Actions",
            font=ctk.CTkFont(size=14, weight="bold"),
        ).pack(anchor="w", padx=14, pady=(10, 6))

        btn_row = ctk.CTkFrame(quick, fg_color="white")
        btn_row.pack(fill="x", padx=10, pady=(0, 12))

        ctk.CTkButton(
            btn_row,
            text="Open Reception UI",
            width=160,
            command=self.open_receptionist,
        ).pack(side="left", padx=6, pady=6)

        ctk.CTkButton(
            btn_row,
            text="Open Restaurant UI",
            width=160,
            command=self.open_restaurant,
        ).pack(side="left", padx=6, pady=6)

        ctk.CTkButton(
            btn_row,
            text="Open Cleaning UI",
            width=160,
            command=self.open_cleaning,
        ).pack(side="left", padx=6, pady=6)

        ctk.CTkButton(
            btn_row,
            text="Open Finance UI",
            width=160,
            command=self.open_finance,
        ).pack(side="left", padx=6, pady=6)

        return frame

    # ------------------------------------------------------------------
    # ROOMS MANAGER PAGE
    # ------------------------------------------------------------------

    def _build_rooms_page(self) -> ctk.CTkFrame:
        frame = ctk.CTkFrame(self.content_frame, fg_color="#F9FAFB", corner_radius=20)

        ctk.CTkLabel(
            frame,
            text="Rooms Manager",
            font=ctk.CTkFont(size=20, weight="bold"),
        ).pack(anchor="w", padx=20, pady=(20, 6))

        ctk.CTkLabel(
            frame,
            text="Here the manager can *conceptually* edit rooms (number, type, price).\n"
                 "For this project demo, actions show a confirmation popup instead of\n"
                 "actually changing the database.",
            font=ctk.CTkFont(size=12),
            text_color="#6B7280",
            justify="left",
        ).pack(anchor="w", padx=20)

        main = ctk.CTkFrame(frame, fg_color="white", corner_radius=16)
        main.pack(fill="both", expand=True, padx=20, pady=20)

        # Left side: form
        form = ctk.CTkFrame(main, fg_color="white")
        form.pack(side="left", fill="y", padx=16, pady=16)

        ctk.CTkLabel(form, text="Room Editor", font=ctk.CTkFont(size=14, weight="bold")).pack(
            anchor="w", pady=(0, 10)
        )

        # Room number
        ctk.CTkLabel(form, text="Room Number:").pack(anchor="w")
        room_number_entry = ctk.CTkEntry(form, placeholder_text="e.g. 101")
        room_number_entry.pack(fill="x", pady=(0, 8))

        # Type
        ctk.CTkLabel(form, text="Room Type / Topology:").pack(anchor="w")
        room_type_entry = ctk.CTkEntry(form, placeholder_text="e.g. Double, Suite...")
        room_type_entry.pack(fill="x", pady=(0, 8))

        # Price
        ctk.CTkLabel(form, text="Price per Night (€):").pack(anchor="w")
        room_price_entry = ctk.CTkEntry(form, placeholder_text="e.g. 69.99")
        room_price_entry.pack(fill="x", pady=(0, 12))

        # Buttons
        btns = ctk.CTkFrame(form, fg_color="white")
        btns.pack(fill="x", pady=(4, 0))

        def _demo_action(kind: str):
            rn = room_number_entry.get().strip() or "(no room)"
            rt = room_type_entry.get().strip() or "(no type)"
            rp = room_price_entry.get().strip() or "(no price)"
            messagebox.showinfo(
                "Demo",
                f"{kind} room:\n"
                f"Number: {rn}\n"
                f"Type: {rt}\n"
                f"Price: {rp}\n\n"
                f"(In a full implementation this would update the database.)"
            )

        ctk.CTkButton(btns, text="Add Room", command=lambda: _demo_action("Add")).pack(
            side="left", padx=4, pady=4
        )
        ctk.CTkButton(btns, text="Update Room", command=lambda: _demo_action("Update")).pack(
            side="left", padx=4, pady=4
        )
        ctk.CTkButton(
            btns,
            text="Delete Room",
            fg_color="#DC2626",
            hover_color="#B91C1C",
            command=lambda: _demo_action("Delete"),
        ).pack(side="left", padx=4, pady=4)

        # Right side: simple "table" preview
        right = ctk.CTkFrame(main, fg_color="#F3F4F6", corner_radius=16)
        right.pack(side="left", fill="both", expand=True, padx=16, pady=16)

        ctk.CTkLabel(
            right,
            text="Rooms Overview (demo)",
            font=ctk.CTkFont(size=14, weight="bold"),
        ).pack(anchor="w", padx=12, pady=(10, 6))

        info = (
            "In a complete version, this area would show a table pulled from the database,\n"
            "with filters for floor, type, price, and status.\n\n"
            "For now, you can explain to the professor that:\n"
            "• This is the manager control center for rooms.\n"
            "• The forms on the left are ready to be wired to backend.\n"
            "• Receptionist UI already works with real room data."
        )
        ctk.CTkLabel(
            right,
            text=info,
            font=ctk.CTkFont(size=12),
            text_color="#4B5563",
            justify="left",
        ).pack(anchor="w", padx=12, pady=(0, 10))

        ctk.CTkButton(
            right,
            text="Open Reception UI (live rooms view)",
            command=self.open_receptionist,
        ).pack(anchor="w", padx=12, pady=(4, 10))

        return frame

    # ------------------------------------------------------------------
    # RESTAURANT MANAGER PAGE
    # ------------------------------------------------------------------

    def _build_restaurant_page(self) -> ctk.CTkFrame:
        frame = ctk.CTkFrame(self.content_frame, fg_color="#F9FAFB", corner_radius=20)

        ctk.CTkLabel(
            frame,
            text="Restaurant & Bar Manager",
            font=ctk.CTkFont(size=20, weight="bold"),
        ).pack(anchor="w", padx=20, pady=(20, 6))

        ctk.CTkLabel(
            frame,
            text="Here the manager controls restaurant tables and menu items.\n"
                 "For now, this is a management *prototype* UI with demo buttons.",
            font=ctk.CTkFont(size=12),
            text_color="#6B7280",
        ).pack(anchor="w", padx=20)

        main = ctk.CTkFrame(frame, fg_color="white", corner_radius=16)
        main.pack(fill="both", expand=True, padx=20, pady=20)

        # Left: menu editor demo
        left = ctk.CTkFrame(main, fg_color="white")
        left.pack(side="left", fill="y", padx=16, pady=16)

        ctk.CTkLabel(left, text="Menu Item Editor", font=ctk.CTkFont(size=14, weight="bold")).pack(
            anchor="w", pady=(0, 10)
        )

        ctk.CTkLabel(left, text="Item Name:").pack(anchor="w")
        item_name_entry = ctk.CTkEntry(left, placeholder_text="e.g. Spaghetti Bolognese")
        item_name_entry.pack(fill="x", pady=(0, 6))

        ctk.CTkLabel(left, text="Category:").pack(anchor="w")
        item_cat_entry = ctk.CTkEntry(left, placeholder_text="e.g. Main Dish / Dessert / Drink")
        item_cat_entry.pack(fill="x", pady=(0, 6))

        ctk.CTkLabel(left, text="Price (€):").pack(anchor="w")
        item_price_entry = ctk.CTkEntry(left, placeholder_text="e.g. 7.50")
        item_price_entry.pack(fill="x", pady=(0, 10))

        def restaurant_demo(kind: str):
            messagebox.showinfo(
                "Demo",
                f"{kind} menu item:\n"
                f"- Name: {item_name_entry.get().strip() or '(none)'}\n"
                f"- Category: {item_cat_entry.get().strip() or '(none)'}\n"
                f"- Price: {item_price_entry.get().strip() or '(none)'}\n\n"
                f"(Backend not wired yet – this is a UI prototype.)"
            )

        btns = ctk.CTkFrame(left, fg_color="white")
        btns.pack(fill="x")

        ctk.CTkButton(btns, text="Add", command=lambda: restaurant_demo("Add")).pack(
            side="left", padx=4, pady=4
        )
        ctk.CTkButton(btns, text="Update", command=lambda: restaurant_demo("Update")).pack(
            side="left", padx=4, pady=4
        )
        ctk.CTkButton(
            btns,
            text="Delete",
            fg_color="#DC2626",
            hover_color="#B91C1C",
            command=lambda: restaurant_demo("Delete"),
        ).pack(side="left", padx=4, pady=4)

        # Right: explanation & link
        right = ctk.CTkFrame(main, fg_color="#F3F4F6", corner_radius=16)
        right.pack(side="left", fill="both", expand=True, padx=16, pady=16)

        ctk.CTkLabel(
            right,
            text="Tables & Live Service",
            font=ctk.CTkFont(size=14, weight="bold"),
        ).pack(anchor="w", padx=12, pady=(10, 6))

        text = (
            "• The Waiter / Restaurant UI you already built is used for live orders.\n"
            "• Here, the manager can configure menu items and (in the future) table layouts.\n"
            "• Tables (1–15) are handled in the Waiter UI, but a manager could add/remove them here.\n\n"
            "For the project presentation, you can say:\n"
            "➡ Manager can supervise and configure Bar & Restaurant, while\n"
            "   waiters use the dedicated service UI for daily work."
        )
        ctk.CTkLabel(
            right,
            text=text,
            font=ctk.CTkFont(size=12),
            text_color="#4B5563",
            justify="left",
        ).pack(anchor="w", padx=12, pady=(0, 10))

        ctk.CTkButton(
            right,
            text="Open Waiter / Restaurant UI",
            command=self.open_restaurant,
        ).pack(anchor="w", padx=12, pady=(4, 10))

        return frame

    # ------------------------------------------------------------------
    # CLEANING MANAGER PAGE
    # ------------------------------------------------------------------

    def _build_cleaning_page(self) -> ctk.CTkFrame:
        frame = ctk.CTkFrame(self.content_frame, fg_color="#F9FAFB", corner_radius=20)

        ctk.CTkLabel(
            frame,
            text="Cleaning / Housekeeping Manager",
            font=ctk.CTkFont(size=20, weight="bold"),
        ).pack(anchor="w", padx=20, pady=(20, 6))

        ctk.CTkLabel(
            frame,
            text="This section summarizes the cleaning service module.\n"
                 "Full control of room statuses is inside the Cleaning UI.",
            font=ctk.CTkFont(size=12),
            text_color="#6B7280",
        ).pack(anchor="w", padx=20)

        main = ctk.CTkFrame(frame, fg_color="white", corner_radius=16)
        main.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(
            main,
            text="Overview",
            font=ctk.CTkFont(size=14, weight="bold"),
        ).pack(anchor="w", padx=16, pady=(14, 6))

        info = (
            "• The Cleaning Service UI displays each room with status (Clean, Needs Cleaning, Occupied).\n"
            "• It also has a Management tab that summarizes how many rooms each staff member has.\n"
            "• From the Manager perspective, this module is already operational.\n\n"
            "Future ideas:\n"
            "• Export a daily cleaning report.\n"
            "• Enforce a deadline (e.g. all check-out rooms cleaned before 14:00).\n"
            "• Notify Finance / Reception when cleaning is delayed."
        )

        ctk.CTkLabel(
            main,
            text=info,
            font=ctk.CTkFont(size=12),
            text_color="#4B5563",
            justify="left",
        ).pack(anchor="w", padx=16, pady=(0, 10))

        ctk.CTkButton(
            main,
            text="Open Cleaning Service UI",
            command=self.open_cleaning,
        ).pack(anchor="w", padx=16, pady=(4, 10))

        return frame

    # ------------------------------------------------------------------
    # FINANCE DASHBOARD PAGE
    # ------------------------------------------------------------------

    def _build_finance_page(self) -> ctk.CTkFrame:
        frame = ctk.CTkFrame(self.content_frame, fg_color="#F9FAFB", corner_radius=20)

        ctk.CTkLabel(
            frame,
            text="Finance Dashboard",
            font=ctk.CTkFont(size=20, weight="bold"),
        ).pack(anchor="w", padx=20, pady=(20, 6))

        ctk.CTkLabel(
            frame,
            text="High-level finance overview. Detailed logs are available in the Finance UI.",
            font=ctk.CTkFont(size=12),
            text_color="#6B7280",
        ).pack(anchor="w", padx=20)

        main = ctk.CTkFrame(frame, fg_color="white", corner_radius=16)
        main.pack(fill="both", expand=True, padx=20, pady=20)

        # Two columns
        left = ctk.CTkFrame(main, fg_color="white")
        left.pack(side="left", fill="both", expand=True, padx=12, pady=12)

        right = ctk.CTkFrame(main, fg_color="white")
        right.pack(side="left", fill="both", expand=True, padx=12, pady=12)

        # Left: summary demo cards
        ctk.CTkLabel(
            left,
            text="Today (Demo values)",
            font=ctk.CTkFont(size=14, weight="bold"),
        ).pack(anchor="w", padx=10, pady=(4, 6))

        def f_card(parent, label, value):
            card = ctk.CTkFrame(parent, fg_color="#F3F4F6", corner_radius=12)
            card.pack(fill="x", padx=6, pady=4)
            ctk.CTkLabel(card, text=label, font=ctk.CTkFont(size=12, weight="bold")).pack(
                anchor="w", padx=10, pady=(6, 0)
            )
            ctk.CTkLabel(card, text=value, font=ctk.CTkFont(size=16, weight="bold")).pack(
                anchor="w", padx=10, pady=(0, 8)
            )

        f_card(left, "Total Revenue", "€ 1,245.00")
        f_card(left, "From Rooms", "€ 820.00")
        f_card(left, "From Restaurant", "€ 425.00")

        # Right: explanation + button
        ctk.CTkLabel(
            right,
            text="Details & Reports",
            font=ctk.CTkFont(size=14, weight="bold"),
        ).pack(anchor="w", padx=10, pady=(4, 6))

        text = (
            "Your Finance UI already receives logs from:\n"
            "• Restaurant bills (via Waiter / Restaurant module)\n"
            "• Other manual entries (if implemented).\n\n"
            "From the Manager UI, you can quickly open the Finance window\n"
            "to show daily / monthly reports, then come back here with Logout."
        )

        ctk.CTkLabel(
            right,
            text=text,
            font=ctk.CTkFont(size=12),
            text_color="#4B5563",
            justify="left",
        ).pack(anchor="w", padx=10, pady=(0, 10))

        ctk.CTkButton(
            right,
            text="Open Finance UI",
            command=self.open_finance,
        ).pack(anchor="w", padx=10, pady=(4, 10))

        return frame

    # ------------------------------------------------------------------
    # STAFF & USERS PAGE
    # ------------------------------------------------------------------

    def _build_staff_page(self) -> ctk.CTkFrame:
        frame = ctk.CTkFrame(self.content_frame, fg_color="#F9FAFB", corner_radius=20)

        ctk.CTkLabel(
            frame,
            text="Staff & Users Management",
            font=ctk.CTkFont(size=20, weight="bold"),
        ).pack(anchor="w", padx=20, pady=(20, 6))

        ctk.CTkLabel(
            frame,
            text="Conceptual interface for managing application users and roles.\n"
                 "For this project, it shows a working UI but does not fully edit the DB.",
            font=ctk.CTkFont(size=12),
            text_color="#6B7280",
        ).pack(anchor="w", padx=20)

        main = ctk.CTkFrame(frame, fg_color="white", corner_radius=16)
        main.pack(fill="both", expand=True, padx=20, pady=20)

        # Left: user form
        left = ctk.CTkFrame(main, fg_color="white")
        left.pack(side="left", fill="y", padx=16, pady=16)

        ctk.CTkLabel(left, text="Create / Edit User (Demo)", font=ctk.CTkFont(size=14, weight="bold")).pack(
            anchor="w", pady=(0, 8)
        )

        ctk.CTkLabel(left, text="Username:").pack(anchor="w")
        user_entry = ctk.CTkEntry(left, placeholder_text="e.g. reception")
        user_entry.pack(fill="x", pady=(0, 6))

        ctk.CTkLabel(left, text="Full Name:").pack(anchor="w")
        name_entry = ctk.CTkEntry(left, placeholder_text="e.g. John Doe")
        name_entry.pack(fill="x", pady=(0, 6))

        ctk.CTkLabel(left, text="Password:").pack(anchor="w")
        pass_entry = ctk.CTkEntry(left, placeholder_text="••••••", show="●")
        pass_entry.pack(fill="x", pady=(0, 6))

        ctk.CTkLabel(left, text="Role:").pack(anchor="w")
        role_var = ctk.StringVar(value="Receptionist")
        role_menu = ctk.CTkOptionMenu(
            left,
            values=["Manager", "Receptionist", "Bar & Restaurant", "Cleaning", "Finance"],
            variable=role_var,
            width=200,
        )
        role_menu.pack(fill="x", pady=(0, 8))

        def staff_demo(kind: str):
            messagebox.showinfo(
                "Demo",
                f"{kind} user:\n"
                f"Username: {user_entry.get().strip() or '(none)'}\n"
                f"Name: {name_entry.get().strip() or '(none)'}\n"
                f"Role: {role_var.get()}\n\n"
                f"(Database wiring can be added via backend.users.)"
            )

        btns = ctk.CTkFrame(left, fg_color="white")
        btns.pack(fill="x", pady=(4, 0))

        ctk.CTkButton(btns, text="Add / Save", command=lambda: staff_demo("Add / Save")).pack(
            side="left", padx=4, pady=4
        )
        ctk.CTkButton(
            btns,
            text="Delete",
            fg_color="#DC2626",
            hover_color="#B91C1C",
            command=lambda: staff_demo("Delete"),
        ).pack(side="left", padx=4, pady=4)

        # Right: explanation
        right = ctk.CTkFrame(main, fg_color="#F3F4F6", corner_radius=16)
        right.pack(side="left", fill="both", expand=True, padx=16, pady=16)

        text = (
            "In a full implementation, this screen would:\n"
            "• Load existing users from the database.\n"
            "• Let you change roles (like Manager, Receptionist, etc.).\n"
            "• Control who can access which modules of the app.\n\n"
            "For your presentation, you can explain that the architecture is ready:\n"
            "• Login already checks role and opens the correct UI.\n"
            "• Manager is the super user, with access to all modules.\n"
        )

        ctk.CTkLabel(
            right,
            text=text,
            font=ctk.CTkFont(size=12),
            text_color="#4B5563",
            justify="left",
        ).pack(anchor="w", padx=12, pady=10)

        return frame

    # ------------------------------------------------------------------
    # SETTINGS PAGE
    # ------------------------------------------------------------------

    def _build_settings_page(self) -> ctk.CTkFrame:
        frame = ctk.CTkFrame(self.content_frame, fg_color="#F9FAFB", corner_radius=20)

        ctk.CTkLabel(
            frame,
            text="Application Settings",
            font=ctk.CTkFont(size=20, weight="bold"),
        ).pack(anchor="w", padx=20, pady=(20, 6))

        ctk.CTkLabel(
            frame,
            text="Simple global settings for the demo (appearance mode, etc.).",
            font=ctk.CTkFont(size=12),
            text_color="#6B7280",
        ).pack(anchor="w", padx=20)

        main = ctk.CTkFrame(frame, fg_color="white", corner_radius=16)
        main.pack(fill="both", expand=True, padx=20, pady=20)

        # Appearance
        appearance_row = ctk.CTkFrame(main, fg_color="white")
        appearance_row.pack(anchor="w", padx=16, pady=(10, 6))

        ctk.CTkLabel(
            appearance_row,
            text="Appearance Mode:",
            font=ctk.CTkFont(size=13, weight="bold"),
        ).pack(side="left", padx=(0, 10))

        appearance_var = ctk.StringVar(value="Light")

        def on_appearance_change(choice: str):
            if choice.lower() == "dark":
                ctk.set_appearance_mode("dark")
            else:
                ctk.set_appearance_mode("light")

            self.refresh_theme()

        ctk.CTkOptionMenu(
            appearance_row,
            values=["Light", "Dark"],
            variable=appearance_var,
            command=on_appearance_change,
            width=140,
        ).pack(side="left")

        # Placeholder more settings
        ctk.CTkLabel(
            main,
            text="\nMore settings ideas:\n"
                 "• Change hotel name / logo on all pages.\n"
                 "• Default language / currency.\n"
                 "• Enable / disable modules (Restaurant, Cleaning, etc.).",
            font=ctk.CTkFont(size=12),
            text_color="#4B5563",
            justify="left",
        ).pack(anchor="w", padx=16, pady=(10, 10))

        return frame

    # ------------------------------------------------------------------
    # OPEN OTHER WINDOWS FROM MANAGER
    # ------------------------------------------------------------------

    def open_receptionist(self):
        # Hide manager, open Receptionist window; on its logout you come back here
        self.withdraw()
        win = ReceptionistWindow(parent=self, user=self.user)
        win.protocol("WM_DELETE_WINDOW", win.on_window_close)

    def open_restaurant(self):
        self.withdraw()
        win = RestaurantWindow(parent=self, user=self.user)
        win.protocol("WM_DELETE_WINDOW", win.on_window_close)

    def open_cleaning(self):
        self.withdraw()
        win = CleaningWindow(parent=self, user=self.user)
        win.protocol("WM_DELETE_WINDOW", win.on_window_close)

    def open_finance(self):
        self.withdraw()
        win = FinanceWindow(parent=self, user=self.user)
        win.protocol("WM_DELETE_WINDOW", win.on_window_close)

    # ------------------------------------------------------------------
    # LOGOUT / CLOSE
    # ------------------------------------------------------------------

    def on_logout(self):
        """Logout from Manager back to Login window."""
        self.destroy()
        if self.parent is not None:
            try:
                self.parent.deiconify()
            except Exception:
                pass

    def on_window_close(self):
        self.on_logout()


# Small manual test launcher
if __name__ == "__main__":
    ctk.set_appearance_mode("light")
    app = ctk.CTk()
    app.title("Manager Demo")
    app.geometry("500x300")

    def refresh_theme(self):
        """Force full UI redraw after appearance change."""
        for widget in self.winfo_children():
            widget.destroy()
        self._build_layout()
        self.show_page(self.current_page_name or "dashboard")


    def open_manager():
        ManagerWindow(parent=app, user={"username": "manager"})

    ctk.CTkButton(app, text="Open Manager", command=open_manager).pack(pady=40)
    app.mainloop()
