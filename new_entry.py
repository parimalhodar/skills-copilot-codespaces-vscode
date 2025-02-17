# --- new_entry.py ---

import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import DateEntry
from config import get_db_connection, style_config
from datetime import datetime
import sqlite3

class DataEntryManagement(tk.Toplevel):
    """A standalone window for managing True Copy Application entries."""

    def __init__(self, parent):
        super().__init__(parent)
        self.title("True Copy Application Management")
        self.geometry("1200x800")  # Initial geometry
        self.selected_entry_id = None  # Track the selected entry ID for editing
        self.last_receipt_number = None
        self.parent = parent  # Store parent for go_back

        # Configure style
        self.style = style_config()
        self.configure_custom_styles()

        self.create_widgets()
        self.load_entries()
        self.load_last_receipt_number()  # Load the last receipt number on startup

        # Set True Copy and Receipt number for auto
        self.new_true_copy_number()
        self.update_receipt_number()

        # Setup keyboard shortcuts
        self.bind('<Control-n>', self.new_entry)
        self.bind('<Control-s>', self.save_and_new)  # Save and new
        self.bind('<Control-r>', self.load_entries)
        self.bind('<Control-q>', self.destroy)
        self.bind('<Escape>', self.go_back)  # Go Back
        self.bind('<Return>', self.handle_enter_key)

    def configure_custom_styles(self):
        """Configure custom styles for widgets."""
        # No custom styles beyond what's in config.py for now.  You can add if needed.
        pass

    def create_widgets(self):
        """Creates the UI elements for the management window."""
        # Reduced padding below main_frame
        main_frame = ttk.Frame(self, style='Main.TFrame')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)  # REDUCE THE PADY=10

        # Pending Entries List (Treeview)
        self.pending_entry_tree = ttk.Treeview(main_frame,
                                               columns=("ID", "App Date", "Copy Type", "Category", "True Copy #",
                                                        "Advance", "Receipt #"),
                                               show="headings")
        self.pending_entry_tree.heading("ID", text="ID", anchor="center")
        self.pending_entry_tree.heading("App Date", text="App Date", anchor="center")
        self.pending_entry_tree.heading("Copy Type", text="Copy Type", anchor="center")  # Added Copy Type
        self.pending_entry_tree.heading("Category", text="Category", anchor="center")
        self.pending_entry_tree.heading("True Copy #", text="True Copy #", anchor="center")
        self.pending_entry_tree.heading("Advance", text="Advance", anchor="center")
        self.pending_entry_tree.heading("Receipt #", text="Receipt #", anchor="center")

        # Set column widths to automatically adjust
        for col in ("ID", "App Date", "Copy Type", "Category", "True Copy #", "Advance", "Receipt #"):
            self.pending_entry_tree.column(col, anchor="center", stretch=True)

        self.pending_entry_tree.pack(fill=tk.BOTH, expand=True, pady=10)  # Use grid for resizing
        self.pending_entry_tree.bind("<ButtonRelease-1>", self.on_pending_entry_select)  # Select entry

        # Add Scrollbar
        self.add_scrollbar(main_frame, self.pending_entry_tree)

        # Details and Summary Frame
        details_summary_frame = ttk.Frame(main_frame)
        details_summary_frame.pack(fill=tk.X, padx=10, pady=5)

        # Entry Details Frame (Left Side)
        details_frame = ttk.LabelFrame(details_summary_frame, text="Entry Details", padding=10)
        details_frame.pack(fill=tk.BOTH, expand=True, side=tk.LEFT, padx=5)

        ttk.Label(details_frame, text="App Date:", style='Main.TLabel').grid(row=0, column=0, sticky="w", padx=5,
                                                                              pady=2)
        self.app_date_entry = DateEntry(details_frame, date_pattern="yyyy-mm-dd")
        self.app_date_entry.grid(row=0, column=1, sticky="ew", padx=5, pady=2)
        self.app_date_entry.bind("<FocusOut>", self.new_true_copy_number) #UPDATE copy NUMBER

        ttk.Label(details_frame, text="Copy Type:", style='Main.TLabel').grid(row=1, column=0, sticky="w", padx=5,
                                                                               pady=2)
        self.copy_type_cb = ttk.Combobox(details_frame, values=["Certified Copy", "Simple Copy"], width=20,
                                         style='TCombobox')
        self.copy_type_cb.grid(row=1, column=1, sticky="ew", padx=5, pady=2)
        self.copy_type_cb.bind("<<ComboboxSelected>>", self.on_copy_type_select)
        self.copy_type_cb.set("Certified Copy")  # Default to Certified Copy

        ttk.Label(details_frame, text="Category:", style='Main.TLabel').grid(row=2, column=0, sticky="w", padx=5,
                                                                              pady=2)
        self.category_cb = ttk.Combobox(details_frame, values=["Urgent", "Ordinary"], width=20, style='TCombobox')
        self.category_cb.grid(row=2, column=1, sticky="ew", padx=5, pady=2)
        self.category_cb.bind("<<ComboboxSelected>>", self.new_true_copy_number) #Update true copy number

        ttk.Label(details_frame, text="True Copy #:", style='Main.TLabel').grid(row=3, column=0, sticky="w", padx=5,
                                                                                 pady=2)
        self.true_copy_number_entry = ttk.Entry(details_frame, width=20, style='Main.TEntry')
        self.true_copy_number_entry.grid(row=3, column=1, sticky="ew", padx=5, pady=2)

        ttk.Label(details_frame, text="Advance:", style='Main.TLabel').grid(row=4, column=0, sticky="w", padx=5,
                                                                             pady=2)
        self.advance_entry = ttk.Entry(details_frame, width=20, style='Main.TEntry')
        self.advance_entry.grid(row=4, column=1, sticky="ew", padx=5, pady=2)

        ttk.Label(details_frame, text="Receipt #:", style='Main.TLabel').grid(row=5, column=0, sticky="w", padx=5,
                                                                               pady=2)
        self.receipt_entry = ttk.Entry(details_frame, width=20, style='Main.TEntry')
        self.receipt_entry.grid(row=5, column=1, sticky="ew", padx=5, pady=2)

        ttk.Label(details_frame, text="Receipt Category:", style='Main.TLabel').grid(row=6, column=0, sticky="w",
                                                                                       padx=5, pady=2)
        self.receipt_category_cb = ttk.Combobox(details_frame, values=["advance", "recovery"], width=20,
                                                 style='TCombobox')
        self.receipt_category_cb.grid(row=6, column=1, sticky="ew", padx=5, pady=2)
        self.receipt_category_cb.set("advance")  # Default to advance

        # Summary Table Frame (Right Side)
        self.summary_frame = ttk.LabelFrame(details_summary_frame, text="Pending Applications Summary", padding=10)
        self.summary_frame.pack(fill=tk.BOTH, expand=True, side=tk.LEFT, padx=5)

        # Create Treeview for Summary
        self.summary_tree = ttk.Treeview(self.summary_frame,
                                         columns=("Amount", "Application Count", "Total Rupees"),
                                         show="headings")

        self.summary_tree.heading("Amount", text="Amount (Rs.)", anchor="center")
        self.summary_tree.heading("Application Count", text="Application Count", anchor="center")
        self.summary_tree.heading("Total Rupees", text="Total Rupees", anchor="center")

        self.summary_tree.column("Amount", anchor="center", width=150)
        self.summary_tree.column("Application Count", anchor="center", width=150)
        self.summary_tree.column("Total Rupees", anchor="center", width=150)

        self.summary_tree.pack(pady=5, fill=tk.BOTH, expand=True)

        self.update_summary_table()

        # Buttons Frame (Bottom)
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(pady=5)

        # Button Style and Layout
        btn_params = {'side': tk.LEFT, 'padx': 5}
        ttk.Button(button_frame, text="New Entry (Ctrl+N)", command=self.new_entry, style='Action.TButton').pack(
            **btn_params)
        ttk.Button(button_frame, text="Save and New (Ctrl+S)", command=self.save_and_new, style='Action.TButton').pack(
            **btn_params)
        ttk.Button(button_frame, text="Go to Dispose Entry", command=self.open_dispose_entry, style='Action.TButton').pack(
            **btn_params)
        ttk.Button(button_frame, text="Refresh (Ctrl+R)", command=self.load_entries,
                   style='Secondary.TButton').pack(**btn_params)
        ttk.Button(button_frame, text="Go Back (Esc)", command=self.go_back, style='Secondary.TButton').pack(
            **btn_params)
        ttk.Button(button_frame, text="Exit (Ctrl+Q)", command=self.destroy, style='Secondary.TButton').pack(
            **btn_params)

        self.on_copy_type_select()  # Set initial state of category combobox

    def generate_true_copy_number(self):
        """Generates a True Copy Number with prefix and based on the last number + 1 or starts from 001 for the current year."""
        year = datetime.now().year
        copy_type = self.copy_type_cb.get()
        category = self.category_cb.get() if copy_type == "Certified Copy" else None

        if copy_type == "Certified Copy":
            prefix = "CC"
        else:
            prefix = "SC"

        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()

                sql_query = """
                    SELECT true_copy_number
                    FROM true_copy_applications
                    WHERE strftime('%Y', application_date) = ?
                    AND copy_type = ?
                """
                params = [str(year), copy_type]

                if copy_type == "Certified Copy":
                    sql_query += " AND application_category = ?"
                    params.append(category)
                else:
                     sql_query += " AND application_category IS NULL"

                sql_query += " ORDER BY id DESC LIMIT 1"
                cursor.execute(sql_query, params)

                result = cursor.fetchone()

                if result:
                    last_number = result['true_copy_number'].split('/')[1]  # Extract number part (after prefix)
                    next_number = int(last_number) + 1
                    next_number_str = str(next_number).zfill(3)  # Pad with zeros
                else:
                    next_number_str = "001"  # Start from 001 if no entries this year

                # Auto-generate the number
                auto_true_copy_number = f"{prefix}/{next_number_str}/{year}"
                return auto_true_copy_number

        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Error generating True Copy #: {str(e)}")
            return None

    def new_true_copy_number(self, event=None):
        """Handles the creation of a new True Copy number and inserts it into the entry."""
        auto_true_copy_number = self.generate_true_copy_number()  # Generate the new True Copy number
        if auto_true_copy_number:
            self.true_copy_number_entry.delete(0, tk.END)
            self.true_copy_number_entry.insert(0, auto_true_copy_number)


    def update_summary_table(self):
        """Updates the summary table with the count of pending applications by amount."""
        for item in self.summary_tree.get_children():
            self.summary_tree.delete(item)

        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                sql_query = """
                    SELECT
                        advance_amount,
                        COUNT(*) AS application_count,
                        SUM(advance_amount) AS total_rupees
                    FROM
                        true_copy_applications
                    WHERE
                        status = 'Pending'
                    GROUP BY
                        advance_amount
                    ORDER BY
                        advance_amount DESC;
                """
                cursor.execute(sql_query)
                summary_data = cursor.fetchall()

                total_applications = 0
                total_rupees = 0

                for row in summary_data:
                    self.summary_tree.insert("", "end", values=(
                        row['advance_amount'],
                        row['application_count'],
                        row['total_rupees']
                    ))
                    total_applications += row['application_count']
                    total_rupees += row['total_rupees']

                # Insert Total Row
                self.summary_tree.insert("", "end", values=("Total", total_applications, total_rupees))

        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Error updating summary table: {str(e)}")

    def on_copy_type_select(self, event=None):
        """Handles the change of Copy Type selection, enabling/disabling category."""
        copy_type = self.copy_type_cb.get()
        if copy_type == "Certified Copy":
            self.category_cb.config(state='normal')  # Enable Category
            self.category_cb.set("Urgent")  # Set default when enabling
        else:
            self.category_cb.set("")
            self.category_cb.config(state='disabled')  # Disable Category
        self.new_true_copy_number()  # Generate new true copy number on copy type change

    def handle_enter_key(self, event):
        """Handle Enter key press: Modify entry or trigger focused button."""
        focused_widget = self.focus_get()  # Get the currently focused widget

        if focused_widget in [
            self.app_date_entry, self.copy_type_cb, self.category_cb,
            self.advance_entry, self.receipt_entry, self.receipt_category_cb
        ]:
            # If focus is on any entry field, save/modify the entry
            #self.save_and_new()
            self.save_entry(new_entry=True) 
        elif focused_widget == self.pending_entry_tree:
            # If focus is on the Treeview, do nothing
            pass
        elif isinstance(focused_widget, ttk.Button):
            # If focus is on a button, trigger its command
            focused_widget.invoke()

    def add_scrollbar(self, parent, tree):
        """Adds a vertical scrollbar to the treeview widget."""
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        tree.configure(yscrollcommand=scrollbar.set)

    def load_entries(self, event=None):
        """Loads only Pending True Copy Application entries from the database into the Treeview."""
        for item in self.pending_entry_tree.get_children():
            self.pending_entry_tree.delete(item)

        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                sql_query = """SELECT id, application_date, copy_type, application_category, true_copy_number,
                                       advance_amount, receipt_number
                                FROM true_copy_applications
                                WHERE status = 'Pending'
                                ORDER BY application_date DESC"""
                cursor.execute(sql_query)
                entries = cursor.fetchall()
                for entry in entries:
                    # Convert the entry tuple to a list for easier manipulation
                    entry_list = list(entry)
                    # Format the advance amount to display as a float with 2 decimal places
                    entry_list[5] = f"₹{entry_list[5]:.2f}"
                    self.pending_entry_tree.insert("", "end", values=entry_list)
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Error loading entries: {str(e)}")

        self.update_summary_table()  # Update summary table when loading entries.

    def on_pending_entry_select(self, event=None):
        """Populates entry details fields when an entry is selected in the Treeview."""
        selected_item = self.pending_entry_tree.selection()
        if not selected_item:
            # Clear the entry fields if no selection
            self.clear_entry_fields()
            return

        entry_id = self.pending_entry_tree.item(selected_item, "values")[0]
        self.selected_entry_id = entry_id

        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                sql_query = """SELECT application_date, copy_type, application_category, true_copy_number,
                                      advance_amount, receipt_number
                               FROM true_copy_applications
                               WHERE id = ?"""
                cursor.execute(sql_query, (entry_id,))
                entry = cursor.fetchone()

                if entry:
                    app_date, copy_type, category, true_copy_number, advance, receipt = entry
                    self.app_date_entry.set_date(datetime.strptime(app_date, "%Y-%m-%d"))
                    self.copy_type_cb.set(copy_type)
                    self.on_copy_type_select()

                    if copy_type == "Certified Copy":
                        self.category_cb.set(category)
                    else:
                        self.category_cb.set("")

                    self.true_copy_number_entry.delete(0, tk.END)
                    self.true_copy_number_entry.insert(0, true_copy_number)
                    self.advance_entry.delete(0, tk.END)
                    self.advance_entry.insert(0, str(advance))
                    self.receipt_entry.delete(0, tk.END)
                    self.receipt_entry.insert(0, receipt)

                    # Load Receipt Category based on receipt number and amount
                    sql_query = """SELECT payment_type
                                FROM receipt_register
                                WHERE receipt_number = ?
                                AND amount = ?"""

                    cursor.execute(sql_query, (receipt, advance))
                    receipt_data = cursor.fetchone()
                    if receipt_data:
                        self.receipt_category_cb.set(receipt_data['payment_type'])
                    else:
                        self.receipt_category_cb.set("advance")  # Default set to advance

                else:
                    self.clear_entry_fields()  # Clear if no entry found

        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Error fetching entry details: {str(e)}")

    def clear_entry_fields(self):
        """Clears all entry detail fields."""
        self.app_date_entry.set_date(datetime.now())
        self.copy_type_cb.set("Certified Copy")
        self.on_copy_type_select()  # update based on copy type
        self.true_copy_number_entry.delete(0, tk.END)
        self.advance_entry.delete(0, tk.END)
        #UPDATE recipt number
        self.update_receipt_number() # generate new recipt number
        self.receipt_entry.delete(0, tk.END)

        self.receipt_category_cb.set("advance")  # Reset the receipt category

        # Initialize receipt number when clearing
        self.load_last_receipt_number()
        next_receipt_number = self.get_next_receipt_number()
        self.receipt_entry.delete(0, tk.END)
        self.receipt_entry.insert(0, next_receipt_number)
        self.selected_entry_id = None
        self.new_true_copy_number()


    def new_entry(self, event=None):
        """Clears the entry details fields for creating a new entry."""
        self.clear_entry_fields()


    def save_and_new(self, event=None):
        """Saves the entry to the database and prepares for a new entry."""
        self.save_entry(new_entry=True)

    def save_entry(self, new_entry=False):
        """Saves the entry to the database."""
        app_date = self.app_date_entry.get_date().strftime("%Y-%m-%d")
        copy_type = self.copy_type_cb.get()
        category = self.category_cb.get() if copy_type == "Certified Copy" else None
        true_copy_number = self.true_copy_number_entry.get()  # Get from the entry (even though enabled)
        received_date = app_date  # Use the app_date as the received_date, since the UI element is removed
        advance = self.advance_entry.get()
        receipt = self.receipt_entry.get()
        receipt_category = self.receipt_category_cb.get()

        if not all([app_date, copy_type, true_copy_number, advance, receipt, receipt_category]):
            messagebox.showerror("Error", "All fields are required!")
            return

        if copy_type == "Certified Copy" and not category:
            messagebox.showerror("Error", "Category is required for Certified Copies!")
            return

        try:
            advance = float(advance)  # Ensure advance is a valid number
            with get_db_connection() as conn:
                cursor = conn.cursor()

                # Check if a receipt with the same number already exists
                cursor.execute("SELECT COUNT(*) FROM receipt_register WHERE receipt_number = ?", (receipt,))
                receipt_count = cursor.fetchone()[0]

                if receipt_count > 0:
                    messagebox.showerror("Error", "Receipt number already exists!")
                    return

                # Create a new entry with default 'Pending' status
                sql_query = """INSERT INTO true_copy_applications
                               (application_date, copy_type, application_category, true_copy_number,
                                received_date, advance_amount, receipt_number, status)
                               VALUES (?, ?, ?, ?, ?, ?, ?, 'Pending')"""
                cursor.execute(sql_query,
                               (app_date, copy_type, category, true_copy_number, received_date, advance, receipt))
                conn.commit()

                # Add entry to receipt register
                receipt_date = datetime.now().strftime("%Y-%m-%d")
                sql_query = """INSERT INTO receipt_register (receipt_date, receipt_number, payment_type, amount, true_copy_number)
                               VALUES (?, ?, ?, ?, ?)"""
                cursor.execute(sql_query, (receipt_date, receipt, receipt_category, advance, true_copy_number))
                conn.commit()

                messagebox.showinfo("Success", "Entry created successfully!")

                self.load_entries()  # Refresh the entry list

                if new_entry:
                    self.new_entry()  # Prepare for a new entry if save_and_new


        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Failed to save entry: {str(e)}")
        except ValueError:
            messagebox.showerror("Input Error", f"Invalid input value. Please enter a valid number.")
        finally:
             self.update_receipt_number() # update next receipt number



    def load_last_receipt_number(self):
        """Loads the last used receipt number from the database."""
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT receipt_number FROM receipt_register
                    WHERE receipt_number IS NOT NULL
                    ORDER BY receipt_number DESC
                    LIMIT 1
                """)
                result = cursor.fetchone()
                if result and (result[0] is not None):
                    # Extract only the numeric part of the receipt number and convert to integer
                    receipt_number_str = ''.join(filter(str.isdigit, result[0]))
                    self.last_receipt_number = int(receipt_number_str)
                else:
                    self.last_receipt_number = 0  # Start from 1 if no previous entries
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Error loading last receipt number: {str(e)}")
            self.last_receipt_number = 0

    def get_next_receipt_number(self):
        """Generates the next receipt number based on the last number."""
         # Load the last receipt number to ensure that we are using the most recent one
        self.load_last_receipt_number()
        if self.last_receipt_number is not None:
            next_number = self.last_receipt_number + 1
            next_number_str = str(next_number)  # .zfill(3)  # Pad with zeros, if needed
        else:
            next_number_str = "1"  # Start from 1 if no previous entries

        return next_number_str

    def update_receipt_number(self):
         # generate the next receipt number, not only setting it
        next_receipt_number = self.get_next_receipt_number()
        self.receipt_entry.delete(0, tk.END)
        self.receipt_entry.insert(0, next_receipt_number)

    def go_back(self, event=None):
        """Closes the current window."""
        if self.parent:
            self.parent.focus_set()
        self.destroy()

    def open_dispose_entry(self, event=None):
        """Open the Dispose Entry window."""
        from dispose_entry import DisposeEntryForm  # Import here to avoid circular imports
        DisposeEntryForm(self)

    def destroy(self, event=None):
        """Closes the current window."""
        super().destroy()

if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()
    app = DataEntryManagement(root)
    app.mainloop()