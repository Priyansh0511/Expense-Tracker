# ============================================================
#   EXPENSE TRACKER — Complete Project
#   Libraries: Tkinter, tkcalendar, SQLite3
# ============================================================

import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import DateEntry
import sqlite3
from datetime import datetime


# ─────────────────────────────────────────────
#  DATABASE SETUP
# ─────────────────────────────────────────────

def init_db():
    """Create the database and table if they don't exist."""
    conn = sqlite3.connect("expenses.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            date      TEXT    NOT NULL,
            payee     TEXT    NOT NULL,
            category  TEXT    NOT NULL,
            amount    REAL    NOT NULL,
            note      TEXT
        )
    """)
    conn.commit()
    conn.close()


def fetch_all_expenses():
    """Return all rows from the expenses table."""
    conn = sqlite3.connect("expenses.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM expenses ORDER BY date DESC")
    rows = cursor.fetchall()
    conn.close()
    return rows


def add_expense(date, payee, category, amount, note):
    """Insert a new expense record."""
    conn = sqlite3.connect("expenses.db")
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO expenses (date, payee, category, amount, note) VALUES (?, ?, ?, ?, ?)",
        (date, payee, category, amount, note)
    )
    conn.commit()
    conn.close()


def update_expense(expense_id, date, payee, category, amount, note):
    """Update an existing expense record."""
    conn = sqlite3.connect("expenses.db")
    cursor = conn.cursor()
    cursor.execute(
        """UPDATE expenses
           SET date=?, payee=?, category=?, amount=?, note=?
           WHERE id=?""",
        (date, payee, category, amount, note, expense_id)
    )
    conn.commit()
    conn.close()


def delete_expense(expense_id):
    """Delete an expense record by ID."""
    conn = sqlite3.connect("expenses.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM expenses WHERE id=?", (expense_id,))
    conn.commit()
    conn.close()


def search_expenses(keyword):
    """Search expenses by payee, category, or note."""
    conn = sqlite3.connect("expenses.db")
    cursor = conn.cursor()
    like = f"%{keyword}%"
    cursor.execute(
        """SELECT * FROM expenses
           WHERE payee LIKE ? OR category LIKE ? OR note LIKE ?
           ORDER BY date DESC""",
        (like, like, like)
    )
    rows = cursor.fetchall()
    conn.close()
    return rows


# ─────────────────────────────────────────────
#  MAIN APPLICATION CLASS
# ─────────────────────────────────────────────

class ExpenseTrackerApp:

    CATEGORIES = [
        "Food & Dining",
        "Transport",
        "Shopping",
        "Entertainment",
        "Health & Medical",
        "Bills & Utilities",
        "Education",
        "Travel",
        "Rent",
        "Other",
    ]

    # ── Colour palette ──────────────────────
    BG_MAIN      = "#1e1e2e"   # dark navy — main background
    BG_PANEL     = "#2a2a3e"   # slightly lighter panel
    BG_CARD      = "#313149"   # form card background
    ACCENT       = "#7c6af7"   # purple accent
    ACCENT_HOVER = "#6a59e0"
    TEXT_LIGHT   = "#e0e0f0"
    TEXT_DIM     = "#9090b0"
    SUCCESS      = "#4caf82"
    DANGER       = "#f25f5c"
    WARNING      = "#f5a623"
    ROW_ODD      = "#272738"
    ROW_EVEN     = "#2f2f46"
    HEADER_BG    = "#3a3a5c"

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("💸 Expense Tracker")
        self.root.geometry("1150x720")
        self.root.minsize(960, 640)
        self.root.configure(bg=self.BG_MAIN)

        # Track which row is being edited
        self.editing_id = None

        self._build_styles()
        self._build_ui()
        self.refresh_table()
        self.update_total_label()

    # ── Ttk styles ──────────────────────────
    def _build_styles(self):
        style = ttk.Style()
        style.theme_use("clam")

        # Treeview body
        style.configure(
            "Custom.Treeview",
            background=self.ROW_ODD,
            foreground=self.TEXT_LIGHT,
            fieldbackground=self.ROW_ODD,
            rowheight=32,
            font=("Segoe UI", 10),
            borderwidth=0,
        )
        style.configure(
            "Custom.Treeview.Heading",
            background=self.HEADER_BG,
            foreground=self.TEXT_LIGHT,
            font=("Segoe UI", 10, "bold"),
            relief="flat",
        )
        style.map(
            "Custom.Treeview",
            background=[("selected", self.ACCENT)],
            foreground=[("selected", "#ffffff")],
        )
        style.map(
            "Custom.Treeview.Heading",
            background=[("active", self.ACCENT)],
        )

        # Scrollbar
        style.configure(
            "Custom.Vertical.TScrollbar",
            background=self.BG_PANEL,
            troughcolor=self.BG_MAIN,
            arrowcolor=self.TEXT_DIM,
            borderwidth=0,
        )

        # Combobox
        style.configure(
            "Custom.TCombobox",
            fieldbackground=self.BG_CARD,
            background=self.BG_CARD,
            foreground=self.TEXT_LIGHT,
            selectbackground=self.ACCENT,
            selectforeground="#ffffff",
            arrowcolor=self.ACCENT,
        )
        style.map(
            "Custom.TCombobox",
            fieldbackground=[("readonly", self.BG_CARD)],
            foreground=[("readonly", self.TEXT_LIGHT)],
        )

    # ── Master layout ────────────────────────
    def _build_ui(self):
        # ── Top banner ──────────────────────
        banner = tk.Frame(self.root, bg=self.BG_PANEL, height=60)
        banner.pack(fill="x", side="top")
        banner.pack_propagate(False)

        tk.Label(
            banner,
            text="💸  Expense Tracker",
            font=("Segoe UI", 20, "bold"),
            bg=self.BG_PANEL,
            fg=self.ACCENT,
        ).pack(side="left", padx=24, pady=12)

        self.total_label = tk.Label(
            banner,
            text="Total: ₹ 0.00",
            font=("Segoe UI", 14, "bold"),
            bg=self.BG_PANEL,
            fg=self.SUCCESS,
        )
        self.total_label.pack(side="right", padx=24)

        # ── Body: left form + right table ───
        body = tk.Frame(self.root, bg=self.BG_MAIN)
        body.pack(fill="both", expand=True, padx=16, pady=12)

        self._build_form(body)
        self._build_table_section(body)

    # ── LEFT — input form ───────────────────
    def _build_form(self, parent):
        form_frame = tk.Frame(parent, bg=self.BG_CARD, bd=0)
        form_frame.pack(side="left", fill="y", padx=(0, 12), pady=0)
        form_frame.pack_propagate(False)
        form_frame.configure(width=310)

        tk.Label(
            form_frame,
            text="Add / Edit Expense",
            font=("Segoe UI", 13, "bold"),
            bg=self.BG_CARD,
            fg=self.TEXT_LIGHT,
        ).pack(pady=(20, 4), padx=16, anchor="w")

        tk.Frame(form_frame, bg=self.ACCENT, height=2).pack(fill="x", padx=16, pady=(0, 16))

        # helper to build a labelled field row
        def field(label_text):
            tk.Label(
                form_frame,
                text=label_text,
                font=("Segoe UI", 9, "bold"),
                bg=self.BG_CARD,
                fg=self.TEXT_DIM,
            ).pack(anchor="w", padx=16, pady=(8, 2))

        # Date
        field("📅  Date")
        self.date_entry = DateEntry(
            form_frame,
            width=26,
            background=self.ACCENT,
            foreground="white",
            borderwidth=0,
            date_pattern="yyyy-mm-dd",
            font=("Segoe UI", 10),
        )
        self.date_entry.pack(padx=16, pady=(0, 4), anchor="w")

        # Payee
        field("👤  Payee")
        self.payee_var = tk.StringVar()
        self._styled_entry(form_frame, self.payee_var, "e.g. Amazon, Zomato…")

        # Category
        field("🏷️  Category")
        self.category_var = tk.StringVar()
        cat_box = ttk.Combobox(
            form_frame,
            textvariable=self.category_var,
            values=self.CATEGORIES,
            state="readonly",
            style="Custom.TCombobox",
            font=("Segoe UI", 10),
            width=26,
        )
        cat_box.current(0)
        cat_box.pack(padx=16, pady=(0, 4), anchor="w")

        # Amount
        field("💰  Amount (₹)")
        self.amount_var = tk.StringVar()
        self._styled_entry(form_frame, self.amount_var, "e.g. 500.00")

        # Note
        field("📝  Note (optional)")
        self.note_var = tk.StringVar()
        self._styled_entry(form_frame, self.note_var, "Short description…")

        # Buttons
        btn_frame = tk.Frame(form_frame, bg=self.BG_CARD)
        btn_frame.pack(fill="x", padx=16, pady=20)

        self.submit_btn = self._make_button(
            btn_frame, "➕  Add Expense", self.ACCENT, self.on_submit
        )
        self.submit_btn.pack(fill="x", pady=(0, 8))

        self._make_button(
            btn_frame, "🔄  Clear Form", self.BG_PANEL, self.clear_form,
            fg=self.TEXT_DIM
        ).pack(fill="x")

        # ── Search bar (below buttons) ───────
        tk.Frame(form_frame, bg=self.ACCENT, height=2).pack(fill="x", padx=16, pady=(8, 12))

        tk.Label(
            form_frame,
            text="🔍  Search",
            font=("Segoe UI", 9, "bold"),
            bg=self.BG_CARD,
            fg=self.TEXT_DIM,
        ).pack(anchor="w", padx=16)

        search_row = tk.Frame(form_frame, bg=self.BG_CARD)
        search_row.pack(fill="x", padx=16, pady=(4, 0))

        self.search_var = tk.StringVar()
        search_entry = tk.Entry(
            search_row,
            textvariable=self.search_var,
            font=("Segoe UI", 10),
            bg=self.BG_MAIN,
            fg=self.TEXT_LIGHT,
            insertbackground=self.ACCENT,
            relief="flat",
            bd=4,
        )
        search_entry.pack(side="left", fill="x", expand=True)
        search_entry.bind("<KeyRelease>", self.on_search)

        self._make_button(
            search_row, "✖", self.BG_PANEL, self.clear_search,
            fg=self.DANGER, width=3
        ).pack(side="left", padx=(4, 0))

    def _styled_entry(self, parent, textvariable, placeholder=""):
        entry = tk.Entry(
            parent,
            textvariable=textvariable,
            font=("Segoe UI", 10),
            bg=self.BG_MAIN,
            fg=self.TEXT_LIGHT,
            insertbackground=self.ACCENT,
            relief="flat",
            bd=6,
            width=28,
        )
        entry.pack(padx=16, pady=(0, 4), anchor="w")

        # Placeholder logic
        if placeholder:
            entry.insert(0, placeholder)
            entry.config(fg=self.TEXT_DIM)

            def on_focus_in(e):
                if entry.get() == placeholder:
                    entry.delete(0, "end")
                    entry.config(fg=self.TEXT_LIGHT)

            def on_focus_out(e):
                if entry.get() == "":
                    entry.insert(0, placeholder)
                    entry.config(fg=self.TEXT_DIM)

            entry.bind("<FocusIn>", on_focus_in)
            entry.bind("<FocusOut>", on_focus_out)

        return entry

    def _make_button(self, parent, text, bg, command, fg="#ffffff", width=None):
        kwargs = dict(
            text=text,
            bg=bg,
            fg=fg,
            font=("Segoe UI", 10, "bold"),
            relief="flat",
            cursor="hand2",
            activebackground=self.ACCENT_HOVER,
            activeforeground="#ffffff",
            padx=10,
            pady=8,
            command=command,
        )
        if width:
            kwargs["width"] = width
        btn = tk.Button(parent, **kwargs)
        return btn

    # ── RIGHT — table section ───────────────
    def _build_table_section(self, parent):
        right = tk.Frame(parent, bg=self.BG_MAIN)
        right.pack(side="left", fill="both", expand=True)

        # Action bar above table
        action_bar = tk.Frame(right, bg=self.BG_MAIN)
        action_bar.pack(fill="x", pady=(0, 8))

        tk.Label(
            action_bar,
            text="All Expenses",
            font=("Segoe UI", 13, "bold"),
            bg=self.BG_MAIN,
            fg=self.TEXT_LIGHT,
        ).pack(side="left")

        self._make_button(
            action_bar, "🗑️  Delete Selected", self.DANGER, self.on_delete
        ).pack(side="right", padx=(8, 0))

        self._make_button(
            action_bar, "✏️  Edit Selected", self.WARNING, self.on_edit
        ).pack(side="right")

        # Treeview + scrollbar
        tree_frame = tk.Frame(right, bg=self.BG_MAIN)
        tree_frame.pack(fill="both", expand=True)

        columns = ("ID", "Date", "Payee", "Category", "Amount", "Note")
        self.tree = ttk.Treeview(
            tree_frame,
            columns=columns,
            show="headings",
            style="Custom.Treeview",
            selectmode="browse",
        )

        col_widths = {"ID": 40, "Date": 100, "Payee": 160, "Category": 140,
                      "Amount": 90, "Note": 220}
        col_anchors = {"ID": "center", "Amount": "center", "Date": "center"}

        for col in columns:
            self.tree.heading(col, text=col,
                              command=lambda c=col: self.sort_column(c, False))
            self.tree.column(
                col,
                width=col_widths.get(col, 120),
                anchor=col_anchors.get(col, "w"),
                stretch=(col == "Note"),
            )

        scrollbar = ttk.Scrollbar(
            tree_frame,
            orient="vertical",
            command=self.tree.yview,
            style="Custom.Vertical.TScrollbar",
        )
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Alternating row tags
        self.tree.tag_configure("odd",  background=self.ROW_ODD,  foreground=self.TEXT_LIGHT)
        self.tree.tag_configure("even", background=self.ROW_EVEN, foreground=self.TEXT_LIGHT)

        # Double-click to edit
        self.tree.bind("<Double-1>", lambda e: self.on_edit())

        # Status bar
        self.status_var = tk.StringVar(value="Ready")
        tk.Label(
            right,
            textvariable=self.status_var,
            font=("Segoe UI", 9),
            bg=self.BG_MAIN,
            fg=self.TEXT_DIM,
            anchor="w",
        ).pack(fill="x", pady=(6, 0))

    # ─────────────────────────────────────────
    #  CRUD LOGIC
    # ─────────────────────────────────────────

    def get_form_values(self):
        """Return a dict of current form values; returns None on validation error."""
        date     = self.date_entry.get_date().strftime("%Y-%m-%d")
        payee    = self.payee_var.get().strip()
        category = self.category_var.get().strip()
        note     = self.note_var.get().strip()

        # Strip placeholder text
        placeholders = {"e.g. Amazon, Zomato…", "e.g. 500.00", "Short description…"}
        if payee    in placeholders: payee    = ""
        if note     in placeholders: note     = ""
        amount_raw = self.amount_var.get().strip()
        if amount_raw in placeholders: amount_raw = ""

        if not payee:
            messagebox.showwarning("Missing Field", "Please enter a Payee name.")
            return None
        if not amount_raw:
            messagebox.showwarning("Missing Field", "Please enter an Amount.")
            return None
        try:
            amount = float(amount_raw)
            if amount <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Invalid Amount", "Amount must be a positive number.")
            return None

        return {"date": date, "payee": payee, "category": category,
                "amount": amount, "note": note}

    def on_submit(self):
        vals = self.get_form_values()
        if vals is None:
            return

        if self.editing_id is not None:
            update_expense(self.editing_id, **vals)
            self.set_status(f"✅ Updated expense #{self.editing_id}")
            self.editing_id = None
            self.submit_btn.config(text="➕  Add Expense", bg=self.ACCENT)
        else:
            add_expense(**vals)
            self.set_status(f"✅ Added expense for {vals['payee']}")

        self.clear_form()
        self.refresh_table()
        self.update_total_label()

    def on_edit(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo("Select a Row", "Click on an expense row first.")
            return

        item = self.tree.item(selected[0])
        values = item["values"]  # (ID, Date, Payee, Category, Amount, Note)

        self.editing_id = values[0]
        self.submit_btn.config(text="💾  Save Changes", bg=self.WARNING)

        # Populate form
        try:
            self.date_entry.set_date(datetime.strptime(str(values[1]), "%Y-%m-%d"))
        except Exception:
            pass

        self.payee_var.set(values[2])
        self.category_var.set(values[3])
        self.amount_var.set(values[4])
        self.note_var.set(values[5] if values[5] else "")

        self.set_status(f"✏️  Editing expense #{self.editing_id}")

    def on_delete(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo("Select a Row", "Click on an expense row first.")
            return

        item   = self.tree.item(selected[0])
        exp_id = item["values"][0]
        payee  = item["values"][2]

        confirm = messagebox.askyesno(
            "Confirm Delete",
            f"Delete the expense for '{payee}' (ID #{exp_id})?\nThis cannot be undone."
        )
        if confirm:
            delete_expense(exp_id)
            self.refresh_table()
            self.update_total_label()
            self.set_status(f"🗑️  Deleted expense #{exp_id}")
            if self.editing_id == exp_id:
                self.editing_id = None
                self.submit_btn.config(text="➕  Add Expense", bg=self.ACCENT)
                self.clear_form()

    def on_search(self, event=None):
        keyword = self.search_var.get().strip()
        if keyword:
            rows = search_expenses(keyword)
        else:
            rows = fetch_all_expenses()
        self.populate_table(rows)
        self.set_status(f"🔍 Found {len(rows)} result(s) for '{keyword}'" if keyword else "Ready")

    def clear_search(self):
        self.search_var.set("")
        self.refresh_table()
        self.set_status("Ready")

    def clear_form(self):
        self.payee_var.set("")
        self.amount_var.set("")
        self.note_var.set("")
        self.category_var.set(self.CATEGORIES[0])
        self.date_entry.set_date(datetime.today())
        self.editing_id = None
        self.submit_btn.config(text="➕  Add Expense", bg=self.ACCENT)

    # ─────────────────────────────────────────
    #  TABLE HELPERS
    # ─────────────────────────────────────────

    def refresh_table(self):
        rows = fetch_all_expenses()
        self.populate_table(rows)

    def populate_table(self, rows):
        # Clear existing rows
        for item in self.tree.get_children():
            self.tree.delete(item)

        for i, row in enumerate(rows):
            tag = "odd" if i % 2 == 0 else "even"
            # Format amount with ₹ symbol
            display = list(row)
            display[4] = f"₹ {row[4]:,.2f}"
            self.tree.insert("", "end", values=display, tags=(tag,))

        self.set_status(f"{len(rows)} expense(s) loaded.")

    def update_total_label(self):
        rows = fetch_all_expenses()
        total = sum(r[4] for r in rows)
        self.total_label.config(text=f"Total: ₹ {total:,.2f}")

    def set_status(self, msg):
        self.status_var.set(msg)

    def sort_column(self, col, reverse):
        """Sort treeview by column when heading is clicked."""
        items = [(self.tree.set(k, col), k) for k in self.tree.get_children("")]
        try:
            items.sort(key=lambda t: float(t[0].replace("₹", "").replace(",", "").strip()),
                       reverse=reverse)
        except ValueError:
            items.sort(reverse=reverse)

        for index, (_, k) in enumerate(items):
            self.tree.move(k, "", index)
            tag = "odd" if index % 2 == 0 else "even"
            self.tree.item(k, tags=(tag,))

        self.tree.heading(col, command=lambda: self.sort_column(col, not reverse))


# ─────────────────────────────────────────────
#  ENTRY POINT
# ─────────────────────────────────────────────

if __name__ == "__main__":
    init_db()
    root = tk.Tk()
    app = ExpenseTrackerApp(root)
    root.mainloop()
