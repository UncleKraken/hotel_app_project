# ui/login.py

import customtkinter as ctk
from tkinter import messagebox
from ui.manager import ManagerWindow
from backend import users
from ui.receptionist import ReceptionistWindow
from ui.restaurant import RestaurantWindow
from ui.finance import FinanceWindow
from ui.cleaning import CleaningWindow


class LoginWindow(ctk.CTk):

    def __init__(self):
        super().__init__()

        self.title("InnKeeper • Login")
        self.geometry("500x300")
        self.resizable(False, False)

        # center on screen
        self.update_idletasks()
        w, h = 500, 300
        x = (self.winfo_screenwidth() // 2) - (w // 2)
        y = (self.winfo_screenheight() // 2) - (h // 2)
        self.geometry(f"{w}x{h}+{x}+{y}")

        # ensure demo users exist
        users.ensure_default_users()

        self._build_ui()

    def _build_ui(self):
        frame = ctk.CTkFrame(self, corner_radius=16)
        frame.pack(expand=True, fill="both", padx=20, pady=20)

        title = ctk.CTkLabel(
            frame,
            text="InnKeeper Login",
            font=ctk.CTkFont(size=22, weight="bold")
        )
        title.pack(pady=(20, 10))

        # Username
        row_user = ctk.CTkFrame(frame)
        row_user.pack(pady=6, padx=20, fill="x")

        ctk.CTkLabel(row_user, text="Username:", width=90, anchor="e").pack(
            side="left", padx=(0, 6)
        )
        self.username_entry = ctk.CTkEntry(row_user, placeholder_text="reception")
        self.username_entry.pack(side="left", fill="x", expand=True)

        # Password
        row_pass = ctk.CTkFrame(frame)
        row_pass.pack(pady=6, padx=20, fill="x")

        ctk.CTkLabel(row_pass, text="Password:", width=90, anchor="e").pack(
            side="left", padx=(0, 6)
        )
        self.password_entry = ctk.CTkEntry(row_pass, placeholder_text="1234", show="●")
        self.password_entry.pack(side="left", fill="x", expand=True)

        # Info label
        ctk.CTkLabel(
            frame,
            text="Demo logins:\nreception/1234 • waiter/1234 • clean/1234 • finance/1234",
            font=ctk.CTkFont(size=11),
        ).pack(pady=(8, 4))

        login_btn = ctk.CTkButton(frame, text="Login", width=180, command=self.on_login)
        login_btn.pack(pady=(10, 8))

        self.bind("<Return>", lambda e: self.on_login())

    # ---------- LOGIN LOGIC ----------

    def on_login(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()

        if not username or not password:
            messagebox.showwarning("Missing", "Please enter username and password.")
            return

        # Get user from DB
        user = users.get_user_by_username(username)

        if user is None:
            # Auto-create a user with default Receptionist role if not found
            users.create_user(username, password, username, "Receptionist")
            user = users.get_user_by_username(username)

        else:
            if user["password"] != password:
                messagebox.showerror("Login Failed", "Wrong password.")
                return

        role = user["role"]

        # ---------- ROUTING BASED ON ROLE ----------

        if role == "Receptionist":
            self.open_receptionist(user)

        elif role == "Bar & Restaurant":
            self.open_restaurant(user)

        elif role == "Cleaning":
            from ui.cleaning import CleaningWindow
            self.withdraw()
            win = CleaningWindow(parent=self, user=user)
            win.protocol("WM_DELETE_WINDOW", win.on_window_close)
            win.mainloop()

        elif role == "Finance":
            self.open_finance(user)

        elif role == "Manager":
            self.open_manager(user)

        else:
            messagebox.showinfo("Not ready", f"Role '{role}' UI not implemented yet.")

    # ---------- OPEN WINDOWS ----------

    def open_receptionist(self, user):
        self.withdraw()
        win = ReceptionistWindow(parent=self, user=user)
        win.protocol("WM_DELETE_WINDOW", win.on_window_close)

    def open_restaurant(self, user):
        self.withdraw()
        win = RestaurantWindow(parent=self, user=user)
        win.protocol("WM_DELETE_WINDOW", win.on_window_close)

    def open_finance(self, user):
        self.withdraw()
        win = FinanceWindow(parent=self, user=user)
        win.protocol("WM_DELETE_WINDOW", win.on_window_close)

    def open_manager(self, user: dict):
        self.withdraw()
        win = ManagerWindow(parent=self, user=user)
        # ManagerWindow handles its own close to return to login

    def open_cleaning(self, user):
        self.withdraw()
        win = CleaningWindow(parent=self, user=user)
        win.protocol("WM_DELETE_WINDOW", win.on_window_close)
