# ui/toolbox_ui.py

from typing import Any

import customtkinter as ctk
from tkinter import messagebox


class ToolboxWindow(ctk.CTkToplevel):
    """Simple settings / toolbox panel for receptionist."""

    def __init__(self, parent: Any):
        super().__init__(parent)
        self.parent = parent

        self.title("Toolbox / Settings")
        self.geometry("480x320")
        self.resizable(False, False)

        self._build_ui()
        self._center_on_parent()
        self.grab_set()
        self.focus()

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

    def _build_ui(self):
        main = ctk.CTkFrame(self, corner_radius=12)
        main.pack(expand=True, fill="both", padx=10, pady=10)

        title = ctk.CTkLabel(
            main,
            text="Reception toolbox / settings",
            font=ctk.CTkFont(size=18, weight="bold"),
        )
        title.pack(pady=(8, 4))

        # Appearance
        box_appearance = ctk.CTkFrame(main, corner_radius=10)
        box_appearance.pack(fill="x", padx=6, pady=(6, 4))

        ctk.CTkLabel(
            box_appearance,
            text="Appearance mode:",
            anchor="w",
        ).pack(side="left", padx=8, pady=6)

        mode_var = ctk.StringVar(value="Light")

        def on_mode_change(choice: str):
            if choice.lower() in ("light", "dark", "system"):
                ctk.set_appearance_mode(choice.lower())

        mode_menu = ctk.CTkOptionMenu(
            box_appearance,
            values=["Light", "Dark", "System"],
            variable=mode_var,
            command=on_mode_change,
            width=120,
        )
        mode_menu.pack(side="right", padx=8, pady=6)

        # Zoom tools
        box_zoom = ctk.CTkFrame(main, corner_radius=10)
        box_zoom.pack(fill="x", padx=6, pady=(4, 4))

        ctk.CTkLabel(
            box_zoom,
            text="Timeline zoom:",
            anchor="w",
        ).pack(side="left", padx=8, pady=6)

        def reset_zoom():
            if hasattr(self.parent, "zoom_slider"):
                self.parent.zoom_slider.set(36)
                self.parent._on_zoom_change(36)
                messagebox.showinfo("Zoom", "Days zoom reset to default.")
            else:
                messagebox.showwarning("Not available", "Zoom slider not found.")

        ctk.CTkButton(
            box_zoom,
            text="Reset to default",
            width=140,
            command=reset_zoom,
        ).pack(side="right", padx=8, pady=6)

        # About / info
        box_about = ctk.CTkFrame(main, corner_radius=10)
        box_about.pack(fill="both", expand=True, padx=6, pady=(4, 4))

        info_text = (
            "InnKeeper – demo build for university project.\n\n"
            "• Receptionist grid with colored reservations\n"
            "• Clients register, maintenance, reports\n"
            "• Designed to run on low-end Windows machines."
        )
        ctk.CTkLabel(
            box_about,
            text=info_text,
            justify="left",
            anchor="nw",
        ).pack(fill="both", expand=True, padx=8, pady=8)
