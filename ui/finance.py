# ui/finance.py

import tkinter as tk
from datetime import date
from typing import Any, Dict

import customtkinter as ctk
from backend import finance


SOURCE_COLORS = {
    "Restaurant": "#FB7185",  # pink
    "Bar": "#22C55E",         # green
    "Hotel": "#3B82F6",       # blue
}


class FinanceWindow(ctk.CTkToplevel):
    """
    Finance dashboard window.
    Shows real data from finance_logs (SQLite) aggregated by day/source.
    """

    def __init__(self, parent: Any, user: Dict):
        super().__init__(parent)
        self.parent = parent
        self.user = user

        self.title("InnKeeper • Finance")
        self.geometry("1300x780")
        self.minsize(1100, 650)

        # Center on parent
        self.update_idletasks()
        px = parent.winfo_rootx()
        py = parent.winfo_rooty()
        pw = parent.winfo_width()
        ph = parent.winfo_height()
        w, h = 1300, 780
        x = px + (pw - w) // 2
        y = py + (ph - h) // 2
        self.geometry(f"{w}x{h}+{max(x,0)}+{max(y,0)}")

        # track current month
        today = date.today()
        self.year = today.year
        self.month = today.month

        # chart data container
        self.chart_daily: Dict[int, Dict[str, float]] = {}
        self.chart_canvas = None
        self.chart_items: Dict[int, tuple] = {}  # canvas_id -> (day, source, amount)
        self.chart_tooltip_label: ctk.CTkLabel | None = None

        self._build_ui()
        self._refresh_all()

    # ---------- UI BUILD ----------

    def _build_ui(self):
        self.configure(fg_color="#E5E7EB")

        main = ctk.CTkFrame(self, corner_radius=0, fg_color="#E5E7EB")
        main.pack(expand=True, fill="both", padx=10, pady=10)

        # Top row: title + export buttons
        top = ctk.CTkFrame(main, fg_color="#E5E7EB")
        top.pack(fill="x")

        title = ctk.CTkLabel(
            top,
            text="Finance",
            font=ctk.CTkFont(size=24, weight="bold"),
        )
        title.pack(side="left", padx=(4, 10), pady=4)

        export_frame = ctk.CTkFrame(top, fg_color="#E5E7EB")
        export_frame.pack(side="right", pady=4)

        ctk.CTkButton(
            export_frame,
            text="Export CSV",
            width=120,
            fg_color="#3B82F6",
            hover_color="#2563EB",
            command=self._export_csv,
        ).pack(side="left", padx=4)

        ctk.CTkButton(
            export_frame,
            text="Export TXT",
            width=120,
            fg_color="#10B981",
            hover_color="#059669",
            command=self._export_txt,
        ).pack(side="left", padx=4)

        # --- STAT CARDS ---
        cards = ctk.CTkFrame(main, fg_color="#E5E7EB")
        cards.pack(fill="x", pady=(6, 8))

        self.card_today = self._create_stat_card(cards, "Today's Revenue", "$0.00")
        self.card_month = self._create_stat_card(cards, "Monthly Revenue", "$0.00")
        self.card_pending = self._create_stat_card(cards, "Pending Payments", "$0.00")

        # --- MAIN AREA: chart + right sidebar ---
        middle = ctk.CTkFrame(main, fg_color="#E5E7EB")
        middle.pack(fill="both", expand=True)

        # left: chart + table
        left = ctk.CTkFrame(middle, fg_color="#E5E7EB")
        left.pack(side="left", fill="both", expand=True, padx=(0, 6))

        self._build_chart(left)
        self._build_transactions_table(left)

        # right: quick stats + outstanding
        right = ctk.CTkFrame(middle, fg_color="#E5E7EB", width=320)
        right.pack(side="right", fill="y")

        self._build_quick_stats(right)
        self._build_outstanding(right)

    def _create_stat_card(self, parent, title: str, value: str):
        frame = ctk.CTkFrame(parent, width=220, height=80, corner_radius=16, fg_color="#FFFFFF")
        frame.pack(side="left", padx=6)
        frame.pack_propagate(False)

        ctk.CTkLabel(
            frame, text=title, anchor="w",
            font=ctk.CTkFont(size=13, weight="bold"),
        ).pack(fill="x", padx=10, pady=(8, 0))

        lbl = ctk.CTkLabel(
            frame,
            text=value,
            anchor="w",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color="#111827",
        )
        lbl.pack(fill="x", padx=10, pady=(2, 8))

        return lbl

    # ---------- CHART ----------

    def _build_chart(self, parent):
        frame = ctk.CTkFrame(parent, fg_color="#FFFFFF", corner_radius=16)
        frame.pack(fill="both", expand=True, pady=(0, 6))

        ctk.CTkLabel(
            frame,
            text="Revenue This Month",
            font=ctk.CTkFont(size=16, weight="bold"),
        ).pack(pady=(8, 0))

        sub = ctk.CTkLabel(
            frame,
            text=f"Revenue per Day – {self.month:02d}/{self.year}",
            font=ctk.CTkFont(size=12),
            text_color="#6B7280",
        )
        sub.pack(pady=(0, 4))

        canvas = tk.Canvas(frame, bg="white", height=260, highlightthickness=0)
        canvas.pack(fill="x", padx=12, pady=(4, 2))
        canvas.bind("<Motion>", self._on_chart_motion)
        self.chart_canvas = canvas
        self.chart_items = {}

        # tooltip
        self.chart_tooltip_label = ctk.CTkLabel(
            frame,
            text=" ",
            anchor="w",
            text_color="#4B5563",
            font=ctk.CTkFont(size=11),
        )
        self.chart_tooltip_label.pack(fill="x", padx=12, pady=(0, 6))

        # legend
        legend = ctk.CTkFrame(frame, fg_color="#FFFFFF")
        legend.pack(pady=(0, 8))

        for source, color in SOURCE_COLORS.items():
            dot = ctk.CTkLabel(
                legend,
                text="●",
                text_color=color,
                font=ctk.CTkFont(size=16, weight="bold"),
            )
            dot.pack(side="left", padx=(6, 2))
            ctk.CTkLabel(
                legend,
                text=source,
                font=ctk.CTkFont(size=11),
                text_color="#374151",
            ).pack(side="left", padx=(0, 10))

    def _draw_chart(self):
        if self.chart_canvas is None:
            return

        c = self.chart_canvas
        c.delete("all")
        self.chart_items.clear()

        if not self.chart_daily:
            c.create_text(
                c.winfo_width() // 2,
                120,
                text="No data for this month yet.",
                fill="#9CA3AF",
                font=("Arial", 12, "italic"),
            )
            return

        # axis paddings
        left_pad = 40
        right_pad = 10
        top_pad = 10
        bottom_pad = 30

        width = c.winfo_width() or 800
        height = c.winfo_height() or 260

        # find max total per day (sum of sources)
        max_val = 0.0
        for day, srcs in self.chart_daily.items():
            day_sum = sum(srcs.values())
            if day_sum > max_val:
                max_val = day_sum

        if max_val <= 0:
            max_val = 1.0

        days = sorted(self.chart_daily.keys())
        n_days = len(days)
        bar_area_width = width - left_pad - right_pad
        if n_days == 0:
            return

        bar_width = max(10, bar_area_width / (n_days * 1.4))

        # Y-axis line
        c.create_line(left_pad, top_pad, left_pad, height - bottom_pad, fill="#9CA3AF")

        # X-axis line
        c.create_line(
            left_pad,
            height - bottom_pad,
            width - right_pad,
            height - bottom_pad,
            fill="#9CA3AF",
        )

        # draw bars
        for i, day in enumerate(days):
            x_center = left_pad + (i + 1) * bar_area_width / (n_days + 1)
            x0 = x_center - bar_width / 2
            x1 = x_center + bar_width / 2

            y_base = height - bottom_pad
            y_current = y_base

            # stacked per source
            for source, color in SOURCE_COLORS.items():
                val = self.chart_daily.get(day, {}).get(source, 0.0)
                if val <= 0:
                    continue
                bar_height = (val / max_val) * (height - top_pad - bottom_pad)
                y0 = y_current - bar_height
                rect_id = c.create_rectangle(
                    x0, y0, x1, y_current,
                    fill=color,
                    outline="white",
                    width=1,
                )
                self.chart_items[rect_id] = (day, source, val)
                y_current = y0

            # day label
            c.create_text(
                x_center,
                height - bottom_pad + 12,
                text=str(day),
                fill="#4B5563",
                font=("Arial", 9),
            )

    def _on_chart_motion(self, event):
        if self.chart_canvas is None or self.chart_tooltip_label is None:
            return

        ids = self.chart_canvas.find_withtag("current")
        for item_id in ids:
            if item_id in self.chart_items:
                day, source, amount = self.chart_items[item_id]
                self.chart_tooltip_label.configure(
                    text=f"Day {day} • {source}: {amount:.2f} €"
                )
                return

        self.chart_tooltip_label.configure(text=" ")

    # ---------- TRANSACTIONS TABLE ----------

    def _build_transactions_table(self, parent):
        frame = ctk.CTkFrame(parent, fg_color="#FFFFFF", corner_radius=16)
        frame.pack(fill="x", pady=(0, 4))

        ctk.CTkLabel(
            frame,
            text="Latest Transactions",
            font=ctk.CTkFont(size=14, weight="bold"),
        ).pack(anchor="w", padx=10, pady=(6, 2))

        self.tx_list = ctk.CTkTextbox(frame, height=130)
        self.tx_list.pack(fill="both", expand=True, padx=10, pady=(0, 8))

    # ---------- RIGHT SIDE ----------

    def _build_quick_stats(self, parent):
        frame = ctk.CTkFrame(parent, fg_color="#FFFFFF", corner_radius=16)
        frame.pack(fill="x", pady=(0, 6))

        ctk.CTkLabel(
            frame,
            text="Quick Stats",
            font=ctk.CTkFont(size=14, weight="bold"),
        ).pack(anchor="w", padx=10, pady=(8, 4))

        self.label_avg = ctk.CTkLabel(frame, text="Average Daily Revenue: €0.00", anchor="w")
        self.label_avg.pack(fill="x", padx=12, pady=(2, 0))

        self.label_best = ctk.CTkLabel(frame, text="Best Day: -", anchor="w")
        self.label_best.pack(fill="x", padx=12, pady=(2, 0))

        self.label_worst = ctk.CTkLabel(frame, text="Worst Day: -", anchor="w")
        self.label_worst.pack(fill="x", padx=12, pady=(2, 8))

    def _build_outstanding(self, parent):
        frame = ctk.CTkFrame(parent, fg_color="#FFFFFF", corner_radius=16)
        frame.pack(fill="both", expand=True, pady=(6, 0))

        ctk.CTkLabel(
            frame,
            text="Outstanding Payments",
            font=ctk.CTkFont(size=14, weight="bold"),
        ).pack(anchor="w", padx=10, pady=(8, 4))

        self.outstanding_box = ctk.CTkTextbox(frame)
        self.outstanding_box.pack(fill="both", expand=True, padx=10, pady=(0, 8))

    # ---------- DATA REFRESH ----------

    def _refresh_all(self):
        # stat cards
        today_total = finance.get_today_total()
        month_total, month_pending = finance.get_month_totals(self.year, self.month)

        self.card_today.configure(text=f"{today_total:.2f} €")
        self.card_month.configure(text=f"{month_total:.2f} €")
        self.card_pending.configure(text=f"{month_pending:.2f} €")

        # chart data
        daily, _ = finance.get_month_daily_by_source(self.year, self.month)
        self.chart_daily = daily
        self.after(50, self._draw_chart)  # after to ensure canvas has width

        # quick stats
        qs = finance.get_quick_stats(self.year, self.month)
        avg = qs["avg_per_day"]
        self.label_avg.configure(text=f"Average Daily Revenue: {avg:.2f} €")

        best = qs["best_day"]
        worst = qs["worst_day"]

        if best:
            self.label_best.configure(
                text=f"Best Day: {best[0]:02d}  –  {best[1]:.2f} €"
            )
        else:
            self.label_best.configure(text="Best Day: -")

        if worst:
            self.label_worst.configure(
                text=f"Worst Day: {worst[0]:02d}  –  {worst[1]:.2f} €"
            )
        else:
            self.label_worst.configure(text="Worst Day: -")

        # outstanding
        self.outstanding_box.delete("1.0", "end")
        ow = finance.get_outstanding_payments(limit=8)
        if not ow:
            self.outstanding_box.insert("end", "No outstanding payments.\n")
        else:
            for row in ow:
                self.outstanding_box.insert(
                    "end",
                    f"{row['date']} • {row['source']} • {row['description']} – {row['amount']:.2f} €\n",
                )

        # transactions
        self.tx_list.delete("1.0", "end")
        tx = finance.get_recent_transactions(limit=12)
        for row in tx:
            self.tx_list.insert(
                "end",
                f"{row['date']} • {row['source']} • {row['category']} • "
                f"{row['description']} – {row['amount']:.2f} € ({row['method']})\n",
            )

    # ---------- EXPORTS ----------

    def _export_csv(self):
        from datetime import datetime as _dt
        import csv
        import os

        now = _dt.now()
        filename = f"finance_{now.strftime('%Y%m%d_%H%M%S')}.csv"
        exports_dir = "exports"
        os.makedirs(exports_dir, exist_ok=True)
        filepath = os.path.join(exports_dir, filename)

        rows = finance.get_recent_transactions(limit=1000)

        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f, delimiter=";")
            writer.writerow(["date", "source", "category", "description", "amount", "method"])
            for r in rows:
                writer.writerow(
                    [
                        r["date"],
                        r["source"],
                        r["category"],
                        r["description"],
                        f"{r['amount']:.2f}",
                        r["method"],
                    ]
                )

        tk.messagebox.showinfo("Export", f"CSV exported to:\n{filepath}")

    def _export_txt(self):
        from datetime import datetime as _dt
        import os

        now = _dt.now()
        filename = f"finance_summary_{now.strftime('%Y%m%d_%H%M%S')}.txt"
        exports_dir = "exports"
        os.makedirs(exports_dir, exist_ok=True)
        filepath = os.path.join(exports_dir, filename)

        month_total, month_pending = finance.get_month_totals(self.year, self.month)
        qs = finance.get_quick_stats(self.year, self.month)

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(f"Finance summary for {self.month:02d}/{self.year}\n")
            f.write("=" * 40 + "\n\n")
            f.write(f"Total revenue: {month_total:.2f} €\n")
            f.write(f"Pending: {month_pending:.2f} €\n\n")
            f.write(f"Average per day: {qs['avg_per_day']:.2f} €\n")
            if qs["best_day"]:
                f.write(f"Best day: {qs['best_day'][0]:02d} – {qs['best_day'][1]:.2f} €\n")
            if qs["worst_day"]:
                f.write(f"Worst day: {qs['worst_day'][0]:02d} – {qs['worst_day'][1]:.2f} €\n")

        tk.messagebox.showinfo("Export", f"TXT exported to:\n{filepath}")

    # ---------- CLOSE ----------

    def on_window_close(self):
        if self.parent is not None:
            self.destroy()
            self.parent.deiconify()
        else:
            self.destroy()
