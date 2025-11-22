# ui/reports_ui.py

from typing import Any

import customtkinter as ctk


class ReportsWindow(ctk.CTkToplevel):
    """Simple reports overview – reads data from the parent receptionist window."""

    def __init__(self, parent: Any):
        super().__init__(parent)
        self.parent = parent

        self.title("Reception Reports")
        self.geometry("680x380")
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
            text="Reception – Summary reports",
            font=ctk.CTkFont(size=18, weight="bold"),
        )
        title.pack(pady=(8, 4))

        tabs = ctk.CTkTabview(main, width=640, height=300)
        tabs.pack(expand=True, fill="both", padx=6, pady=6)

        tab_res = tabs.add("Reservations")
        tab_clean = tabs.add("Cleaning")
        tab_maint = tabs.add("Maintenance")

        # Reservations summary (from parent.reservations)
        reservations = getattr(self.parent, "reservations", [])
        total = len(reservations)
        reserved = sum(1 for r in reservations if r.status == "reserved")
        present = sum(1 for r in reservations if r.status == "present")
        cleaning = sum(1 for r in reservations if r.status == "cleaning")
        finished = sum(1 for r in reservations if r.status == "finished")

        text_res = (
            f"Total reservations: {total}\n"
            f"• Reserved (future / not checked in): {reserved}\n"
            f"• Present (checked in): {present}\n"
            f"• Cleaning (checkout done, needs cleaning): {cleaning}\n"
            f"• Finished (checkout + cleaned): {finished}\n\n"
            f"This is a simple summary based on the receptionist grid.\n"
            "Later you can export this to PDF/Excel if needed."
        )

        ctk.CTkLabel(
            tab_res,
            text=text_res,
            justify="left",
            anchor="nw",
        ).pack(fill="both", expand=True, padx=10, pady=10)

        # Cleaning placeholder
        ctk.CTkLabel(
            tab_clean,
            text="Cleaning report\n\n"
                 "Later this tab can show rooms that needed cleaning and when they were marked finished.",
            justify="left",
            anchor="nw",
        ).pack(fill="both", expand=True, padx=10, pady=10)

        # Maintenance placeholder
        ctk.CTkLabel(
            tab_maint,
            text="Maintenance report\n\n"
                 "Later this tab can read real data from the Maintenance panel\n"
                 "and show counts by priority and status.",
            justify="left",
            anchor="nw",
        ).pack(fill="both", expand=True, padx=10, pady=10)
