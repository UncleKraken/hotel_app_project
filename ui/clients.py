# ui/clients.py

import customtkinter as ctk
from tkinter import messagebox


class ClientsWindow(ctk.CTkToplevel):

    def __init__(self, parent):
        super().__init__(parent)

        self.title("Clients Registry")
        self.geometry("900x520")
        self.minsize(800, 450)
        self.parent = parent

        # Make window appear in front
        self.lift()
        self.focus_force()
        self.grab_set()

        # After window is drawn → center it
        self.after(50, self.center_on_screen)

        # MAIN LAYOUT
        main = ctk.CTkFrame(self, fg_color="#E4E5E7", corner_radius=12)
        main.pack(fill="both", expand=True, padx=12, pady=12)

        # TITLE
        title = ctk.CTkLabel(
            main,
            text="Client Register",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title.pack(pady=(10, 6))

        # TABLE AREA
        table_frame = ctk.CTkFrame(main, fg_color="#D9D9D9", corner_radius=10)
        table_frame.pack(fill="both", expand=True, padx=20, pady=10)

        self.table = ctk.CTkTextbox(table_frame, fg_color="white", text_color="black")
        self.table.pack(fill="both", expand=True, padx=10, pady=10)

        self.table.insert("1.0", "No clients added yet.\n")
        self.table.configure(state="disabled")

        # BUTTON BAR
        btn_frame = ctk.CTkFrame(main, fg_color="#E4E5E7")
        btn_frame.pack(pady=6)

        ctk.CTkButton(
            btn_frame, text="Add", width=120, fg_color="#2E8AD7",
            hover_color="#2270AD", command=self.open_add_client
        ).pack(side="left", padx=8)

        ctk.CTkButton(
            btn_frame, text="Edit", width=120, fg_color="#2E8AD7",
            hover_color="#2270AD"
        ).pack(side="left", padx=8)

        ctk.CTkButton(
            btn_frame, text="Close", width=120, fg_color="#7A7A7A",
            hover_color="#5C5C5C", command=self.destroy
        ).pack(side="left", padx=8)

    # ------------------ CENTER WINDOW ------------------

    def center_on_screen(self):
        """Centers this Toplevel window on the screen."""
        self.update_idletasks()

        w = self.winfo_width()
        h = self.winfo_height()

        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()

        x = (sw // 2) - (w // 2)
        y = (sh // 2) - (h // 2)

        self.geometry(f"{w}x{h}+{x}+{y}")
        self.lift()
        self.focus_force()

    # ------------------ ADD NEW CLIENT ------------------

    def open_add_client(self):
        win = ctk.CTkToplevel(self)
        win.title("New client")
        win.geometry("360x300")
        win.resizable(False, False)

        win.lift()
        win.focus_force()
        win.grab_set()

        # After drawn → center
        win.after(30, lambda: self._center_child(win))

        # FORM
        frame = ctk.CTkFrame(win, corner_radius=12)
        frame.pack(expand=True, fill="both", padx=15, pady=15)

        ctk.CTkLabel(frame, text="New client", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=8)

        self.fname = ctk.CTkEntry(frame, placeholder_text="First name")
        self.fname.pack(pady=6)

        self.lname = ctk.CTkEntry(frame, placeholder_text="Last name")
        self.lname.pack(pady=6)

        self.phone = ctk.CTkEntry(frame, placeholder_text="+355...")
        self.phone.pack(pady=6)

        self.email = ctk.CTkEntry(frame, placeholder_text="name@email.com")
        self.email.pack(pady=6)

        # BUTTON
        save_btn = ctk.CTkButton(
            frame, text="Add Client", width=180,
            fg_color="#1BAA57", hover_color="#158944",
            command=lambda: self._save_new_client(win)
        )
        save_btn.pack(pady=10)

    def _center_child(self, child):
        """Centers popup relative to the full screen."""
        child.update_idletasks()

        w = child.winfo_width()
        h = child.winfo_height()
        sw = child.winfo_screenwidth()
        sh = child.winfo_screenheight()

        x = (sw // 2) - (w // 2)
        y = (sh // 2) - (h // 2)

        child.geometry(f"{w}x{h}+{x}+{y}")
        child.lift()
        child.focus_force()

    # ------------------ SAVE CLIENT ------------------

    def _save_new_client(self, popup):
        fname = self.fname.get().strip()
        lname = self.lname.get().strip()
        phone = self.phone.get().strip()
        email = self.email.get().strip()

        if not fname or not lname:
            messagebox.showwarning("Missing", "First and last name required.")
            return

        full = f"{fname} {lname} | {phone} | {email}\n"

        self.table.configure(state="normal")
        self.table.insert("end", full)
        self.table.configure(state="disabled")

        popup.destroy()
