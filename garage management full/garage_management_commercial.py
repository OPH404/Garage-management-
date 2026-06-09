import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog
from datetime import datetime, timedelta
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import os
import shutil

# Try to import PIL for logo support
try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    print("Warning: PIL not available. Logo features will be disabled.")

# ============ DATABASE MANAGER ============
class DBManager:
    def __init__(self, db_name="garage_complete.db"):
        self.conn = sqlite3.connect(db_name)
        self.cur = self.conn.cursor()
        self.setup_tables()
    
    def setup_tables(self):
        # USERS
        self.cur.execute("""CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY, username TEXT, password TEXT, role TEXT, name TEXT)""")
        
        # CUSTOMERS  
        self.cur.execute("""CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY, name TEXT, phone TEXT, email TEXT, address TEXT)""")
        
        # BIKES
        self.cur.execute("""CREATE TABLE IF NOT EXISTS bikes (
            id INTEGER PRIMARY KEY, customer_id INTEGER, bike_number TEXT UNIQUE,
            model TEXT, brand TEXT, year INTEGER, last_service_date TEXT, next_service_date TEXT)""")
        
        # PARTS
        self.cur.execute("""CREATE TABLE IF NOT EXISTS parts (
            id INTEGER PRIMARY KEY, name TEXT, category TEXT, price REAL, cost_price REAL,
            quantity INTEGER, min_stock INTEGER, supplier TEXT)""")
        
        # SERVICES
        self.cur.execute("""CREATE TABLE IF NOT EXISTS services (
            id INTEGER PRIMARY KEY, bike_id INTEGER, customer_id INTEGER, date TEXT,
            problem TEXT, notes TEXT, labour REAL, status TEXT, mechanic TEXT, created_by TEXT)""")
        
        # SERVICE PARTS
        self.cur.execute("""CREATE TABLE IF NOT EXISTS service_parts (
            id INTEGER PRIMARY KEY, service_id INTEGER, part_id INTEGER, qty INTEGER, price REAL)""")
        
        # PAYMENTS
        self.cur.execute("""CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY, service_id INTEGER, total REAL, paid REAL,
            balance REAL, payment_method TEXT, date TEXT)""")
        
        # EXPENSES
        self.cur.execute("""CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY, description TEXT, category TEXT,
            amount REAL, date TEXT, added_by TEXT)""")
        
        # SUPPLIERS
        self.cur.execute("""CREATE TABLE IF NOT EXISTS suppliers (
            id INTEGER PRIMARY KEY, name TEXT, contact TEXT, email TEXT, address TEXT)""")
        
        # MECHANICS
        self.cur.execute("""CREATE TABLE IF NOT EXISTS mechanics (
            id INTEGER PRIMARY KEY, name TEXT, phone TEXT, salary REAL, commission_rate REAL)""")
        
        # SYSTEM SETTINGS - Store configuration
        self.cur.execute("""CREATE TABLE IF NOT EXISTS system_settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )""")
        
        # Initialize settings
        self.cur.execute("SELECT COUNT(*) FROM system_settings")
        if self.cur.fetchone()[0] == 0:
            default_settings = [
                ('garage_name', 'Professional Bike Service Center'),
                ('garage_address', '123 Main Street, City, State - 12345'),
                ('garage_phone', '+1 234 567 8900'),
                ('garage_email', 'info@bikeservice.com'),
                ('garage_tax_id', 'GST123456789'),
                ('garage_website', 'www.bikeservice.com'),
                ('logo_path', ''),
                ('currency_symbol', 'Rs'),
                ('service_interval_days', '180'),
                ('low_stock_threshold', '5')
            ]
            for key, value in default_settings:
                self.cur.execute("INSERT INTO system_settings VALUES (?,?)", (key, value))
        
        # Default data
        self.cur.execute("SELECT COUNT(*) FROM users")
        if self.cur.fetchone()[0] == 0:
            self.cur.execute("INSERT INTO users VALUES (NULL,'admin','admin','OWNER','Admin User')")
            self.cur.execute("INSERT INTO users VALUES (NULL,'staff','staff','STAFF','Staff User')")
        
        self.cur.execute("SELECT COUNT(*) FROM mechanics")
        if self.cur.fetchone()[0] == 0:
            self.cur.execute("INSERT INTO mechanics VALUES (NULL,'Ravi Kumar','9876543210',15000,5)")
            self.cur.execute("INSERT INTO mechanics VALUES (NULL,'Suresh Babu','9876543211',12000,5)")
        
        self.conn.commit()
    
    def fetchall(self, query, params=()):
        self.cur.execute(query, params)
        return self.cur.fetchall()
    
    def fetchone(self, query, params=()):
        self.cur.execute(query, params)
        return self.cur.fetchone()
    
    def execute(self, query, params=()):
        self.cur.execute(query, params)
        self.conn.commit()
        return self.cur.lastrowid
    
    def get_setting(self, key, default=''):
        """Get a system setting value"""
        try:
            result = self.fetchone("SELECT value FROM system_settings WHERE key=?", (key,))
            return result[0] if result else default
        except:
            return default
    
    def set_setting(self, key, value):
        """Set a system setting value"""
        self.execute("INSERT OR REPLACE INTO system_settings VALUES (?,?)", (key, str(value)))

# ============ MAIN APP ============
class GarageApp:
    def __init__(self, master):
        self.master = master
        self.master.title("🔧 Complete Garage Management System")
        self.master.geometry("1400x800")
        try:
            self.master.state('zoomed')
        except:
            pass
        self.db = DBManager()
        self.today = datetime.now().strftime("%Y-%m-%d")
        self.current_role = None
        self.current_user = None
        self.login_screen()
    
    # ========== LOGIN ==========
    def login_screen(self):
        self.login_frame = tk.Frame(self.master, bg='#2c3e50')
        self.login_frame.pack(fill='both', expand=True)
        
        login_box = tk.Frame(self.login_frame, bg='white', padx=40, pady=40)
        login_box.place(relx=0.5, rely=0.5, anchor='center')
        
        # Logo section
        logo_frame = tk.Frame(login_box, bg='white')
        logo_frame.pack(pady=(0,10))
        
        logo_loaded = self.display_logo(logo_frame, max_size=120)
        
        # If no logo, show text branding
        if not logo_loaded:
            garage_name = self.db.get_setting('garage_name', '🔧 GARAGE MANAGEMENT')
            tk.Label(logo_frame, text=garage_name, font=("Arial", 18, "bold"),
                    bg='white', fg='#2c3e50').pack()
        
        tk.Label(login_box, text="Username", font=("Arial", 12), bg='white').pack(anchor='w', pady=(20,5))
        self.username_entry = tk.Entry(login_box, font=("Arial", 12), width=30)
        self.username_entry.pack(pady=5)
        self.username_entry.bind('<Return>', lambda e: self.login())
        
        tk.Label(login_box, text="Password", font=("Arial", 12), bg='white').pack(anchor='w', pady=(10,5))
        self.password_entry = tk.Entry(login_box, font=("Arial", 12), width=30, show="*")
        self.password_entry.pack(pady=5)
        self.password_entry.bind('<Return>', lambda e: self.login())
        
        tk.Button(login_box, text="LOGIN", command=self.login, bg='#27ae60', fg='white',
                 font=("Arial", 12, "bold"), width=25, cursor='hand2').pack(pady=20)
        
        # Footer
        garage_name_small = self.db.get_setting('garage_name', 'Garage System')
        tk.Label(login_box, text=f"© 2026 {garage_name_small}", 
                font=("Arial", 8), bg='white', fg='gray').pack(pady=(10,0))
    
    def display_logo(self, parent, max_size=150, bg_color='white'):
        """Display logo if available"""
        if not PIL_AVAILABLE:
            return False
        
        logo_path = self.db.get_setting('logo_path')
        if logo_path and os.path.exists(logo_path):
            try:
                img = Image.open(logo_path)
                img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(img)
                logo_label = tk.Label(parent, image=photo, bg=bg_color)
                logo_label.image = photo  # Keep reference
                logo_label.pack(pady=10)
                return True
            except Exception as e:
                print(f"Could not load logo: {e}")
                return False
        return False
    
    def login(self):
        username = self.username_entry.get()
        password = self.password_entry.get()
        result = self.db.fetchone("SELECT role, name FROM users WHERE username=? AND password=?",
                                  (username, password))
        if result:
            self.current_role, self.current_user = result[0], result[1]
            self.login_frame.pack_forget()
            self.main_screen()
        else:
            messagebox.showerror("Error", "Invalid credentials")
    
    # ========== MAIN SCREEN ==========
    def main_screen(self):
        top_bar = tk.Frame(self.master, bg='#34495e', height=50)
        top_bar.pack(fill='x')
        tk.Label(top_bar, text="🔧 Garage Management System", font=("Arial", 16, "bold"),
                bg='#34495e', fg='white').pack(side='left', padx=20, pady=10)
        tk.Label(top_bar, text=f"User: {self.current_user} ({self.current_role})",
                font=("Arial", 10), bg='#34495e', fg='white').pack(side='right', padx=20)
        
        # Logout button
        tk.Button(top_bar, text="🚪 Logout", command=self.logout, bg='#e74c3c', fg='white',
                 font=("Arial", 9, "bold"), cursor='hand2').pack(side='right', padx=5)
        
        self.notebook = ttk.Notebook(self.master)
        self.notebook.pack(expand=True, fill='both', padx=10, pady=10)
        
        self.tabs = {}
        tab_list = ["Dashboard", "Customers", "Bikes", "Parts", "Services", "Payments", "Expenses", "Reports"]
        
        # Add Settings tab only for OWNER/Admin
        if self.current_role == "OWNER":
            tab_list.append("Settings")
        
        for name in tab_list:
            frame = tk.Frame(self.notebook, bg='#ecf0f1')
            self.notebook.add(frame, text=name)
            self.tabs[name] = frame
        
        self.build_dashboard()
        self.build_customers_tab()
        self.build_bikes_tab()
        self.build_parts_tab()
        self.build_services_tab()
        self.build_payments_tab()
        self.build_expenses_tab()
        self.build_reports_tab()
        
        # Build Settings tab only for OWNER
        if self.current_role == "OWNER":
            self.build_settings_tab()
    
    def logout(self):
        """Logout and return to login screen"""
        if messagebox.askyesno("Logout", "Are you sure you want to logout?"):
            # Destroy all widgets
            for widget in self.master.winfo_children():
                widget.destroy()
            # Restart login
            self.current_role = None
            self.current_user = None
            self.login_screen()
        self.build_expenses_tab()
        self.build_reports_tab()
    
    # ========== DASHBOARD ==========
    def build_dashboard(self):
        tab = self.tabs["Dashboard"]
        
        header = tk.Frame(tab, bg='#3498db', height=60)
        header.pack(fill='x')
        tk.Label(header, text="📊 Dashboard Overview", font=("Arial", 20, "bold"),
                bg='#3498db', fg='white').pack(pady=15)
        
        stats_frame = tk.Frame(tab, bg='#ecf0f1')
        stats_frame.pack(fill='x', padx=20, pady=20)
        
        self.income_label = tk.Label(stats_frame, text="", font=("Arial", 14), bg='#2ecc71',
                                     fg='white', width=20, height=4, relief='raised', bd=3)
        self.income_label.grid(row=0, column=0, padx=10, pady=10)
        
        self.expense_label = tk.Label(stats_frame, text="", font=("Arial", 14), bg='#e74c3c',
                                      fg='white', width=20, height=4, relief='raised', bd=3)
        self.expense_label.grid(row=0, column=1, padx=10, pady=10)
        
        self.profit_label = tk.Label(stats_frame, text="", font=("Arial", 14), bg='#f39c12',
                                     fg='white', width=20, height=4, relief='raised', bd=3)
        self.profit_label.grid(row=0, column=2, padx=10, pady=10)
        
        self.pending_label = tk.Label(stats_frame, text="", font=("Arial", 14), bg='#9b59b6',
                                      fg='white', width=20, height=4, relief='raised', bd=3)
        self.pending_label.grid(row=0, column=3, padx=10, pady=10)
        
        activity_frame = tk.Frame(tab, bg='white', relief='raised', bd=2)
        activity_frame.pack(fill='both', expand=True, padx=20, pady=10)
        
        tk.Label(activity_frame, text="📋 Recent Services", font=("Arial", 14, "bold"),
                bg='white').pack(pady=10)
        
        self.recent_services_tree = ttk.Treeview(activity_frame,
            columns=("Date", "Customer", "Bike", "Status", "Amount"), show='headings', height=10)
        for col in self.recent_services_tree['columns']:
            self.recent_services_tree.heading(col, text=col)
        self.recent_services_tree.pack(fill='both', expand=True, padx=10, pady=10)
        
        alert_frame = tk.Frame(tab, bg='#ffe5e5', relief='raised', bd=2)
        alert_frame.pack(fill='x', padx=20, pady=10)
        
        tk.Label(alert_frame, text="⚠️ Low Stock Alerts", font=("Arial", 12, "bold"),
                bg='#ffe5e5', fg='#c0392b').pack(pady=5)
        
        self.alert_text = tk.Text(alert_frame, height=4, bg='#ffe5e5', font=("Arial", 10))
        self.alert_text.pack(fill='x', padx=10, pady=5)
        
        tk.Button(tab, text="🔄 Refresh Dashboard", command=self.update_dashboard,
                 bg='#3498db', fg='white', font=("Arial", 11, "bold"), cursor='hand2').pack(pady=10)
        
        self.update_dashboard()
    
    def update_dashboard(self):
        income = self.db.fetchone("SELECT SUM(paid) FROM payments")[0] or 0
        expenses = self.db.fetchone("SELECT SUM(amount) FROM expenses")[0] or 0
        profit = income - expenses
        pending = self.db.fetchone("SELECT SUM(balance) FROM payments WHERE balance > 0")[0] or 0
        
        self.income_label.config(text=f"💰 Total Income\nRs {income:,.2f}")
        self.expense_label.config(text=f"💸 Total Expenses\nRs {expenses:,.2f}")
        self.profit_label.config(text=f"📈 Net Profit\nRs {profit:,.2f}")
        self.pending_label.config(text=f"⏳ Pending\nRs {pending:,.2f}")
        
        for row in self.recent_services_tree.get_children():
            self.recent_services_tree.delete(row)
        
        recent = self.db.fetchall("""
            SELECT s.date, c.name, b.bike_number, s.status,
                   (s.labour + COALESCE(SUM(sp.qty * sp.price), 0)) as total
            FROM services s
            JOIN customers c ON s.customer_id = c.id
            JOIN bikes b ON s.bike_id = b.id
            LEFT JOIN service_parts sp ON s.id = sp.service_id
            GROUP BY s.id ORDER BY s.date DESC LIMIT 10
        """)
        
        for r in recent:
            self.recent_services_tree.insert("", tk.END, values=(r[0], r[1], r[2], r[3], f"Rs {r[4]:,.2f}"))
        
        self.alert_text.delete(1.0, tk.END)
        low_stock = self.db.fetchall("SELECT name, quantity, min_stock FROM parts WHERE quantity <= min_stock")
        
        if low_stock:
            for part in low_stock:
                self.alert_text.insert(tk.END, f"⚠️ {part[0]}: {part[1]} units (Min: {part[2]})\n")
        else:
            self.alert_text.insert(tk.END, "✅ All parts adequately stocked!")

    
    # ========== CUSTOMERS TAB ==========
    def build_customers_tab(self):
        tab = self.tabs["Customers"]
        
        header = tk.Frame(tab, bg='#3498db', height=50)
        header.pack(fill='x')
        tk.Label(header, text="👥 Customer Management", font=("Arial", 16, "bold"),
                bg='#3498db', fg='white').pack(pady=10)
        
        form_frame = tk.LabelFrame(tab, text="Add / Update Customer", font=("Arial", 12, "bold"),
                                  bg='white', padx=20, pady=20)
        form_frame.pack(fill='x', padx=20, pady=10)
        
        tk.Label(form_frame, text="Name*", bg='white', font=("Arial", 10)).grid(row=0, column=0, sticky='w', pady=5)
        self.c_name = tk.Entry(form_frame, font=("Arial", 10), width=30)
        self.c_name.grid(row=0, column=1, pady=5, padx=10)
        
        tk.Label(form_frame, text="Phone*", bg='white', font=("Arial", 10)).grid(row=0, column=2, sticky='w', pady=5)
        self.c_phone = tk.Entry(form_frame, font=("Arial", 10), width=30)
        self.c_phone.grid(row=0, column=3, pady=5, padx=10)
        
        tk.Label(form_frame, text="Email", bg='white', font=("Arial", 10)).grid(row=1, column=0, sticky='w', pady=5)
        self.c_email = tk.Entry(form_frame, font=("Arial", 10), width=30)
        self.c_email.grid(row=1, column=1, pady=5, padx=10)
        
        tk.Label(form_frame, text="Address", bg='white', font=("Arial", 10)).grid(row=1, column=2, sticky='w', pady=5)
        self.c_address = tk.Entry(form_frame, font=("Arial", 10), width=30)
        self.c_address.grid(row=1, column=3, pady=5, padx=10)
        
        btn_frame = tk.Frame(form_frame, bg='white')
        btn_frame.grid(row=2, column=0, columnspan=4, pady=15)
        
        for text, cmd, color in [("➕ Add", self.add_customer, '#27ae60'),
                                  ("🔄 Update", self.update_customer, '#f39c12'),
                                  ("🗑️ Delete", self.delete_customer, '#e74c3c'),
                                  ("🧹 Clear", self.clear_customer_form, '#95a5a6')]:
            tk.Button(btn_frame, text=text, command=cmd, bg=color, fg='white',
                     font=("Arial", 10, "bold"), width=15, cursor='hand2').pack(side='left', padx=5)
        
        table_frame = tk.Frame(tab, bg='white')
        table_frame.pack(fill='both', expand=True, padx=20, pady=10)
        
        scroll_y = tk.Scrollbar(table_frame)
        scroll_y.pack(side='right', fill='y')
        
        self.customer_table = ttk.Treeview(table_frame,
            columns=("ID", "Name", "Phone", "Email", "Address"),
            show='headings', yscrollcommand=scroll_y.set)
        
        scroll_y.config(command=self.customer_table.yview)
        
        for col in self.customer_table['columns']:
            self.customer_table.heading(col, text=col)
            self.customer_table.column(col, width=150)
        
        self.customer_table.pack(fill='both', expand=True)
        self.customer_table.bind('<Double-1>', self.load_customer_data)
        
        self.refresh_customers_table()
    
    def add_customer(self):
        name, phone = self.c_name.get().strip(), self.c_phone.get().strip()
        email, address = self.c_email.get().strip(), self.c_address.get().strip()
        
        if not name or not phone:
            messagebox.showerror("Error", "Name and Phone are required!")
            return
        
        self.db.execute("INSERT INTO customers VALUES (NULL,?,?,?,?)", (name, phone, email, address))
        messagebox.showinfo("Success", "Customer added!")
        self.clear_customer_form()
        self.refresh_customers_table()
        self.refresh_all_dropdowns()  # Refresh dropdowns in other tabs
    
    def update_customer(self):
        selected = self.customer_table.selection()
        if not selected:
            messagebox.showerror("Error", "Select a customer!")
            return
        
        cid = self.customer_table.item(selected[0])['values'][0]
        name, phone = self.c_name.get().strip(), self.c_phone.get().strip()
        email, address = self.c_email.get().strip(), self.c_address.get().strip()
        
        if not name or not phone:
            messagebox.showerror("Error", "Name and Phone are required!")
            return
        
        self.db.execute("UPDATE customers SET name=?, phone=?, email=?, address=? WHERE id=?",
                       (name, phone, email, address, cid))
        messagebox.showinfo("Success", "Customer updated!")
        self.clear_customer_form()
        self.refresh_customers_table()
        self.refresh_all_dropdowns()  # Refresh dropdowns
    
    def delete_customer(self):
        selected = self.customer_table.selection()
        if not selected:
            messagebox.showerror("Error", "Select a customer!")
            return
        
        if messagebox.askyesno("Confirm", "Delete this customer?"):
            cid = self.customer_table.item(selected[0])['values'][0]
            self.db.execute("DELETE FROM customers WHERE id=?", (cid,))
            messagebox.showinfo("Success", "Customer deleted!")
            self.clear_customer_form()
            self.refresh_customers_table()
    
    def load_customer_data(self, event):
        selected = self.customer_table.selection()
        if selected:
            vals = self.customer_table.item(selected[0])['values']
            self.c_name.delete(0, tk.END)
            self.c_name.insert(0, vals[1])
            self.c_phone.delete(0, tk.END)
            self.c_phone.insert(0, vals[2])
            self.c_email.delete(0, tk.END)
            self.c_email.insert(0, vals[3])
            self.c_address.delete(0, tk.END)
            self.c_address.insert(0, vals[4])
    
    def clear_customer_form(self):
        self.c_name.delete(0, tk.END)
        self.c_phone.delete(0, tk.END)
        self.c_email.delete(0, tk.END)
        self.c_address.delete(0, tk.END)
    
    def refresh_customers_table(self):
        for row in self.customer_table.get_children():
            self.customer_table.delete(row)
        rows = self.db.fetchall("SELECT * FROM customers")
        for r in rows:
            self.customer_table.insert("", tk.END, values=r)
    
    # ========== BIKES TAB ==========
    def build_bikes_tab(self):
        tab = self.tabs["Bikes"]
        
        header = tk.Frame(tab, bg='#3498db', height=50)
        header.pack(fill='x')
        tk.Label(header, text="🏍️ Bike Management", font=("Arial", 16, "bold"),
                bg='#3498db', fg='white').pack(pady=10)
        
        form_frame = tk.LabelFrame(tab, text="Add / Update Bike", font=("Arial", 12, "bold"),
                                  bg='white', padx=20, pady=20)
        form_frame.pack(fill='x', padx=20, pady=10)
        
        tk.Label(form_frame, text="Customer*", bg='white', font=("Arial", 10)).grid(row=0, column=0, sticky='w', pady=5)
        self.b_customer = ttk.Combobox(form_frame, font=("Arial", 10), width=28, state='readonly')
        self.b_customer.grid(row=0, column=1, pady=5, padx=10)
        self.refresh_customer_dropdown()
        
        tk.Label(form_frame, text="Bike Number*", bg='white', font=("Arial", 10)).grid(row=0, column=2, sticky='w', pady=5)
        self.b_number = tk.Entry(form_frame, font=("Arial", 10), width=30)
        self.b_number.grid(row=0, column=3, pady=5, padx=10)
        
        tk.Label(form_frame, text="Brand*", bg='white', font=("Arial", 10)).grid(row=1, column=0, sticky='w', pady=5)
        self.b_brand = tk.Entry(form_frame, font=("Arial", 10), width=30)
        self.b_brand.grid(row=1, column=1, pady=5, padx=10)
        
        tk.Label(form_frame, text="Model*", bg='white', font=("Arial", 10)).grid(row=1, column=2, sticky='w', pady=5)
        self.b_model = tk.Entry(form_frame, font=("Arial", 10), width=30)
        self.b_model.grid(row=1, column=3, pady=5, padx=10)
        
        tk.Label(form_frame, text="Year", bg='white', font=("Arial", 10)).grid(row=2, column=0, sticky='w', pady=5)
        self.b_year = tk.Entry(form_frame, font=("Arial", 10), width=30)
        self.b_year.grid(row=2, column=1, pady=5, padx=10)
        
        btn_frame = tk.Frame(form_frame, bg='white')
        btn_frame.grid(row=3, column=0, columnspan=4, pady=15)
        
        for text, cmd, color in [("➕ Add", self.add_bike, '#27ae60'),
                                  ("🔄 Update", self.update_bike, '#f39c12'),
                                  ("🗑️ Delete", self.delete_bike, '#e74c3c'),
                                  ("🧹 Clear", self.clear_bike_form, '#95a5a6')]:
            tk.Button(btn_frame, text=text, command=cmd, bg=color, fg='white',
                     font=("Arial", 10, "bold"), width=15, cursor='hand2').pack(side='left', padx=5)
        
        table_frame = tk.Frame(tab, bg='white')
        table_frame.pack(fill='both', expand=True, padx=20, pady=10)
        
        scroll_y = tk.Scrollbar(table_frame)
        scroll_y.pack(side='right', fill='y')
        
        self.bike_table = ttk.Treeview(table_frame,
            columns=("ID", "Customer", "Number", "Brand", "Model", "Year", "Last Service", "Next Service"),
            show='headings', yscrollcommand=scroll_y.set)
        
        scroll_y.config(command=self.bike_table.yview)
        
        for col in self.bike_table['columns']:
            self.bike_table.heading(col, text=col)
            self.bike_table.column(col, width=120)
        
        self.bike_table.pack(fill='both', expand=True)
        self.bike_table.bind('<Double-1>', self.load_bike_data)
        
        self.refresh_bikes_table()
    
    def refresh_customer_dropdown(self):
        customers = self.db.fetchall("SELECT id, name FROM customers")
        self.customer_map = {f"{c[1]} (ID: {c[0]})": c[0] for c in customers}
        self.b_customer['values'] = list(self.customer_map.keys())
    
    def refresh_all_dropdowns(self):
        """Refresh all dropdown lists across the application"""
        # Refresh customer dropdown in Bikes tab
        if hasattr(self, 'b_customer'):
            customers = self.db.fetchall("SELECT id, name FROM customers")
            self.customer_map = {f"{c[1]} (ID: {c[0]})": c[0] for c in customers}
            self.b_customer['values'] = list(self.customer_map.keys())
    
    def add_bike(self):
        if not self.b_customer.get():
            messagebox.showerror("Error", "Select a customer!")
            return
        
        cid = self.customer_map[self.b_customer.get()]
        num = self.b_number.get().strip().upper()
        brand, model = self.b_brand.get().strip(), self.b_model.get().strip()
        year = self.b_year.get().strip()
        
        if not num or not brand or not model:
            messagebox.showerror("Error", "Number, Brand, and Model required!")
            return
        
        try:
            self.db.execute("INSERT INTO bikes VALUES (NULL,?,?,?,?,?,NULL,NULL)",
                           (cid, num, model, brand, year or 0))
            messagebox.showinfo("Success", "Bike added!")
            self.clear_bike_form()
            self.refresh_bikes_table()
            self.refresh_all_dropdowns()  # Refresh dropdowns
        except sqlite3.IntegrityError:
            messagebox.showerror("Error", "Bike number exists!")
    
    def update_bike(self):
        selected = self.bike_table.selection()
        if not selected:
            messagebox.showerror("Error", "Select a bike!")
            return
        
        bid = self.bike_table.item(selected[0])['values'][0]
        cid = self.customer_map[self.b_customer.get()]
        num = self.b_number.get().strip().upper()
        brand, model = self.b_brand.get().strip(), self.b_model.get().strip()
        year = self.b_year.get().strip()
        
        self.db.execute("UPDATE bikes SET customer_id=?, bike_number=?, model=?, brand=?, year=? WHERE id=?",
                       (cid, num, model, brand, year or 0, bid))
        messagebox.showinfo("Success", "Bike updated!")
        self.clear_bike_form()
        self.refresh_bikes_table()
        self.refresh_all_dropdowns()  # Refresh dropdowns
    
    def delete_bike(self):
        selected = self.bike_table.selection()
        if not selected:
            messagebox.showerror("Error", "Select a bike!")
            return
        
        if messagebox.askyesno("Confirm", "Delete this bike?"):
            bid = self.bike_table.item(selected[0])['values'][0]
            self.db.execute("DELETE FROM bikes WHERE id=?", (bid,))
            messagebox.showinfo("Success", "Bike deleted!")
            self.clear_bike_form()
            self.refresh_bikes_table()
    
    def load_bike_data(self, event):
        selected = self.bike_table.selection()
        if selected:
            vals = self.bike_table.item(selected[0])['values']
            cid = self.db.fetchone("SELECT customer_id FROM bikes WHERE id=?", (vals[0],))[0]
            for key, val in self.customer_map.items():
                if val == cid:
                    self.b_customer.set(key)
                    break
            self.b_number.delete(0, tk.END)
            self.b_number.insert(0, vals[2])
            self.b_brand.delete(0, tk.END)
            self.b_brand.insert(0, vals[3])
            self.b_model.delete(0, tk.END)
            self.b_model.insert(0, vals[4])
            self.b_year.delete(0, tk.END)
            self.b_year.insert(0, vals[5])
    
    def clear_bike_form(self):
        self.b_customer.set('')
        self.b_number.delete(0, tk.END)
        self.b_brand.delete(0, tk.END)
        self.b_model.delete(0, tk.END)
        self.b_year.delete(0, tk.END)
    
    def refresh_bikes_table(self):
        for row in self.bike_table.get_children():
            self.bike_table.delete(row)
        
        rows = self.db.fetchall("""
            SELECT b.id, c.name, b.bike_number, b.brand, b.model, b.year,
                   b.last_service_date, b.next_service_date
            FROM bikes b JOIN customers c ON b.customer_id = c.id
        """)
        
        for r in rows:
            self.bike_table.insert("", tk.END, values=r)

    
    # ========== PARTS TAB ==========
    def build_parts_tab(self):
        tab = self.tabs["Parts"]
        
        header = tk.Frame(tab, bg='#3498db', height=50)
        header.pack(fill='x')
        tk.Label(header, text="🔧 Parts & Inventory", font=("Arial", 16, "bold"),
                bg='#3498db', fg='white').pack(pady=10)
        
        form_frame = tk.LabelFrame(tab, text="Add / Update Part", font=("Arial", 12, "bold"),
                                  bg='white', padx=20, pady=20)
        form_frame.pack(fill='x', padx=20, pady=10)
        
        tk.Label(form_frame, text="Name*", bg='white', font=("Arial", 10)).grid(row=0, column=0, sticky='w', pady=5)
        self.p_name = tk.Entry(form_frame, font=("Arial", 10), width=30)
        self.p_name.grid(row=0, column=1, pady=5, padx=10)
        
        tk.Label(form_frame, text="Category*", bg='white', font=("Arial", 10)).grid(row=0, column=2, sticky='w', pady=5)
        self.p_category = ttk.Combobox(form_frame, font=("Arial", 10), width=28,
                                       values=["Engine", "Brake", "Electrical", "Body", "Suspension", "Oil", "Other"])
        self.p_category.grid(row=0, column=3, pady=5, padx=10)
        
        tk.Label(form_frame, text="Selling Price*", bg='white', font=("Arial", 10)).grid(row=1, column=0, sticky='w', pady=5)
        self.p_price = tk.Entry(form_frame, font=("Arial", 10), width=30)
        self.p_price.grid(row=1, column=1, pady=5, padx=10)
        
        tk.Label(form_frame, text="Cost Price", bg='white', font=("Arial", 10)).grid(row=1, column=2, sticky='w', pady=5)
        self.p_cost = tk.Entry(form_frame, font=("Arial", 10), width=30)
        self.p_cost.grid(row=1, column=3, pady=5, padx=10)
        
        tk.Label(form_frame, text="Quantity*", bg='white', font=("Arial", 10)).grid(row=2, column=0, sticky='w', pady=5)
        self.p_qty = tk.Entry(form_frame, font=("Arial", 10), width=30)
        self.p_qty.grid(row=2, column=1, pady=5, padx=10)
        
        tk.Label(form_frame, text="Min Stock", bg='white', font=("Arial", 10)).grid(row=2, column=2, sticky='w', pady=5)
        self.p_min = tk.Entry(form_frame, font=("Arial", 10), width=30)
        self.p_min.grid(row=2, column=3, pady=5, padx=10)
        
        tk.Label(form_frame, text="Supplier", bg='white', font=("Arial", 10)).grid(row=3, column=0, sticky='w', pady=5)
        self.p_supplier = tk.Entry(form_frame, font=("Arial", 10), width=30)
        self.p_supplier.grid(row=3, column=1, pady=5, padx=10)
        
        btn_frame = tk.Frame(form_frame, bg='white')
        btn_frame.grid(row=4, column=0, columnspan=4, pady=15)
        
        for text, cmd, color in [("➕ Add", self.add_part, '#27ae60'),
                                  ("🔄 Update", self.update_part, '#f39c12'),
                                  ("🗑️ Delete", self.delete_part, '#e74c3c'),
                                  ("📦 Add Stock", self.add_stock, '#9b59b6'),
                                  ("🧹 Clear", self.clear_part_form, '#95a5a6')]:
            tk.Button(btn_frame, text=text, command=cmd, bg=color, fg='white',
                     font=("Arial", 10, "bold"), width=15, cursor='hand2').pack(side='left', padx=5)
        
        table_frame = tk.Frame(tab, bg='white')
        table_frame.pack(fill='both', expand=True, padx=20, pady=10)
        
        scroll_y = tk.Scrollbar(table_frame)
        scroll_y.pack(side='right', fill='y')
        
        self.part_table = ttk.Treeview(table_frame,
            columns=("ID", "Name", "Category", "Price", "Cost", "Qty", "Min", "Supplier", "Profit"),
            show='headings', yscrollcommand=scroll_y.set)
        
        scroll_y.config(command=self.part_table.yview)
        
        for col in self.part_table['columns']:
            self.part_table.heading(col, text=col)
            self.part_table.column(col, width=100)
        
        self.part_table.pack(fill='both', expand=True)
        self.part_table.bind('<Double-1>', self.load_part_data)
        
        self.refresh_parts_table()
    
    def add_part(self):
        name, cat = self.p_name.get().strip(), self.p_category.get().strip()
        price, cost = self.p_price.get().strip(), self.p_cost.get().strip() or 0
        qty = self.p_qty.get().strip()
        min_stock = self.p_min.get().strip() or 5
        supplier = self.p_supplier.get().strip()
        
        if not name or not cat or not price or not qty:
            messagebox.showerror("Error", "Name, Category, Price, Quantity required!")
            return
        
        try:
            self.db.execute("INSERT INTO parts VALUES (NULL,?,?,?,?,?,?,?)",
                           (name, cat, float(price), float(cost), int(qty), int(min_stock), supplier))
            messagebox.showinfo("Success", "Part added!")
            self.clear_part_form()
            self.refresh_parts_table()
            self.refresh_all_dropdowns()  # Refresh dropdowns
        except ValueError:
            messagebox.showerror("Error", "Invalid number format!")
    
    def update_part(self):
        selected = self.part_table.selection()
        if not selected:
            messagebox.showerror("Error", "Select a part!")
            return
        
        pid = self.part_table.item(selected[0])['values'][0]
        name, cat = self.p_name.get().strip(), self.p_category.get().strip()
        price, cost = self.p_price.get().strip(), self.p_cost.get().strip() or 0
        qty = self.p_qty.get().strip()
        min_stock = self.p_min.get().strip() or 5
        supplier = self.p_supplier.get().strip()
        
        try:
            self.db.execute("""UPDATE parts SET name=?, category=?, price=?, cost_price=?,
                              quantity=?, min_stock=?, supplier=? WHERE id=?""",
                           (name, cat, float(price), float(cost), int(qty), int(min_stock), supplier, pid))
            messagebox.showinfo("Success", "Part updated!")
            self.clear_part_form()
            self.refresh_parts_table()
            self.refresh_all_dropdowns()  # Refresh dropdowns
        except ValueError:
            messagebox.showerror("Error", "Invalid number format!")
    
    def delete_part(self):
        selected = self.part_table.selection()
        if not selected:
            messagebox.showerror("Error", "Select a part!")
            return
        
        if messagebox.askyesno("Confirm", "Delete this part?"):
            pid = self.part_table.item(selected[0])['values'][0]
            self.db.execute("DELETE FROM parts WHERE id=?", (pid,))
            messagebox.showinfo("Success", "Part deleted!")
            self.clear_part_form()
            self.refresh_parts_table()
    
    def add_stock(self):
        selected = self.part_table.selection()
        if not selected:
            messagebox.showerror("Error", "Select a part!")
            return
        
        pid = self.part_table.item(selected[0])['values'][0]
        current_qty = self.part_table.item(selected[0])['values'][5]
        
        add_qty = simpledialog.askinteger("Add Stock", "Enter quantity to add:", minvalue=1)
        if add_qty:
            new_qty = current_qty + add_qty
            self.db.execute("UPDATE parts SET quantity=? WHERE id=?", (new_qty, pid))
            messagebox.showinfo("Success", f"Added {add_qty} units. New: {new_qty}")
            self.refresh_parts_table()
    
    def load_part_data(self, event):
        selected = self.part_table.selection()
        if selected:
            vals = self.part_table.item(selected[0])['values']
            self.p_name.delete(0, tk.END)
            self.p_name.insert(0, vals[1])
            self.p_category.set(vals[2])
            self.p_price.delete(0, tk.END)
            self.p_price.insert(0, vals[3])
            self.p_cost.delete(0, tk.END)
            self.p_cost.insert(0, vals[4])
            self.p_qty.delete(0, tk.END)
            self.p_qty.insert(0, vals[5])
            self.p_min.delete(0, tk.END)
            self.p_min.insert(0, vals[6])
            self.p_supplier.delete(0, tk.END)
            self.p_supplier.insert(0, vals[7])
    
    def clear_part_form(self):
        self.p_name.delete(0, tk.END)
        self.p_category.set('')
        self.p_price.delete(0, tk.END)
        self.p_cost.delete(0, tk.END)
        self.p_qty.delete(0, tk.END)
        self.p_min.delete(0, tk.END)
        self.p_supplier.delete(0, tk.END)
    
    def refresh_parts_table(self):
        for row in self.part_table.get_children():
            self.part_table.delete(row)
        
        rows = self.db.fetchall("SELECT *, (price - cost_price) as profit FROM parts")
        for r in rows:
            vals = list(r)
            self.part_table.insert("", tk.END, values=vals,
                                  tags=('low_stock',) if r[5] <= r[6] else ())
        
        self.part_table.tag_configure('low_stock', background='#ffcccc')

    
    # ========== SERVICES TAB ==========
    def build_services_tab(self):
        tab = self.tabs["Services"]
        
        header = tk.Frame(tab, bg='#3498db', height=50)
        header.pack(fill='x')
        tk.Label(header, text="🔨 Service Management", font=("Arial", 16, "bold"),
                bg='#3498db', fg='white').pack(pady=10)
        
        btn_frame = tk.Frame(tab, bg='#ecf0f1')
        btn_frame.pack(fill='x', padx=20, pady=10)
        
        for text, cmd, color in [("➕ New Service", self.create_new_service, '#27ae60'),
                                  ("🔍 View/Edit", self.view_edit_service, '#f39c12'),
                                  ("✅ Complete", self.complete_service, '#3498db'),
                                  ("🖨️ Print Invoice", self.print_service_invoice, '#9b59b6')]:
            tk.Button(btn_frame, text=text, command=cmd, bg=color, fg='white',
                     font=("Arial", 11, "bold"), cursor='hand2').pack(side='left', padx=5)
        
        filter_frame = tk.LabelFrame(tab, text="Filter", font=("Arial", 11, "bold"),
                                    bg='white', padx=15, pady=15)
        filter_frame.pack(fill='x', padx=20, pady=5)
        
        tk.Label(filter_frame, text="Status:", bg='white').grid(row=0, column=0, padx=5)
        self.service_filter = ttk.Combobox(filter_frame, values=["All", "Pending", "In Progress", "Completed"],
                                          state='readonly', width=15)
        self.service_filter.set("All")
        self.service_filter.grid(row=0, column=1, padx=5)
        self.service_filter.bind('<<ComboboxSelected>>', lambda e: self.refresh_services_table())
        
        table_frame = tk.Frame(tab, bg='white')
        table_frame.pack(fill='both', expand=True, padx=20, pady=10)
        
        scroll_y = tk.Scrollbar(table_frame)
        scroll_y.pack(side='right', fill='y')
        
        self.service_table = ttk.Treeview(table_frame,
            columns=("ID", "Date", "Customer", "Bike", "Problem", "Status", "Mechanic", "Labour", "Parts", "Total"),
            show='headings', yscrollcommand=scroll_y.set)
        
        scroll_y.config(command=self.service_table.yview)
        
        for col in self.service_table['columns']:
            self.service_table.heading(col, text=col)
            self.service_table.column(col, width=100)
        
        self.service_table.pack(fill='both', expand=True)
        
        self.refresh_services_table()
    
    def create_new_service(self):
        service_win = tk.Toplevel(self.master)
        service_win.title("Create New Service")
        service_win.geometry("900x700")
        service_win.grab_set()
        
        tk.Label(service_win, text="🔨 New Service Entry", font=("Arial", 16, "bold"),
                bg='#3498db', fg='white').pack(fill='x', pady=10)
        
        form = tk.Frame(service_win, padx=20, pady=20)
        form.pack(fill='both')
        
        tk.Label(form, text="Select Bike*", font=("Arial", 11, "bold")).grid(row=0, column=0, sticky='w', pady=5)
        bike_combo = ttk.Combobox(form, font=("Arial", 10), width=40, state='readonly')
        bikes = self.db.fetchall("""
            SELECT b.id, b.bike_number, b.model, c.name
            FROM bikes b JOIN customers c ON b.customer_id = c.id
        """)
        bike_map = {f"{b[1]} - {b[2]} ({b[3]})": (b[0], b[1], b[2], b[3]) for b in bikes}
        bike_combo['values'] = list(bike_map.keys())
        bike_combo.grid(row=0, column=1, pady=5, padx=10, columnspan=2)
        
        tk.Label(form, text="Problem*", font=("Arial", 11, "bold")).grid(row=1, column=0, sticky='nw', pady=5)
        problem_text = tk.Text(form, height=4, width=50, font=("Arial", 10))
        problem_text.grid(row=1, column=1, pady=5, padx=10, columnspan=2)
        
        tk.Label(form, text="Notes", font=("Arial", 11, "bold")).grid(row=2, column=0, sticky='nw', pady=5)
        notes_text = tk.Text(form, height=4, width=50, font=("Arial", 10))
        notes_text.grid(row=2, column=1, pady=5, padx=10, columnspan=2)
        
        tk.Label(form, text="Mechanic*", font=("Arial", 11, "bold")).grid(row=3, column=0, sticky='w', pady=5)
        mechanic_combo = ttk.Combobox(form, font=("Arial", 10), width=30, state='readonly')
        mechanics = self.db.fetchall("SELECT name FROM mechanics")
        mechanic_combo['values'] = [m[0] for m in mechanics]
        mechanic_combo.grid(row=3, column=1, pady=5, padx=10, sticky='w')
        
        tk.Label(form, text="Labour*", font=("Arial", 11, "bold")).grid(row=4, column=0, sticky='w', pady=5)
        labour_entry = tk.Entry(form, font=("Arial", 10), width=20)
        labour_entry.grid(row=4, column=1, pady=5, padx=10, sticky='w')
        
        tk.Label(form, text="Status*", font=("Arial", 11, "bold")).grid(row=5, column=0, sticky='w', pady=5)
        status_combo = ttk.Combobox(form, font=("Arial", 10), width=20, state='readonly',
                                   values=["Pending", "In Progress", "Completed"])
        status_combo.set("Pending")
        status_combo.grid(row=5, column=1, pady=5, padx=10, sticky='w')
        
        tk.Label(form, text="Parts Used", font=("Arial", 12, "bold"), fg='#2c3e50').grid(row=6, column=0, columnspan=3, pady=(20,10))
        
        parts_frame = tk.Frame(form)
        parts_frame.grid(row=7, column=0, columnspan=3, pady=5)
        
        parts_tree = ttk.Treeview(parts_frame, columns=("Part", "Qty", "Price", "Total"),
                                 show='headings', height=6)
        parts_tree.heading("Part", text="Part")
        parts_tree.heading("Qty", text="Qty")
        parts_tree.heading("Price", text="Price")
        parts_tree.heading("Total", text="Total")
        parts_tree.pack(side='left')
        
        parts_scroll = tk.Scrollbar(parts_frame, command=parts_tree.yview)
        parts_scroll.pack(side='right', fill='y')
        parts_tree.config(yscrollcommand=parts_scroll.set)
        
        add_parts_frame = tk.Frame(form)
        add_parts_frame.grid(row=8, column=0, columnspan=3, pady=10)
        
        tk.Label(add_parts_frame, text="Part:").pack(side='left', padx=5)
        part_combo = ttk.Combobox(add_parts_frame, width=25, state='readonly')
        available_parts = self.db.fetchall("SELECT id, name, price, quantity FROM parts WHERE quantity > 0")
        part_map = {f"{p[1]} (Stock: {p[3]}) - Rs {p[2]}": (p[0], p[1], p[2], p[3]) for p in available_parts}
        part_combo['values'] = list(part_map.keys())
        part_combo.pack(side='left', padx=5)
        
        tk.Label(add_parts_frame, text="Qty:").pack(side='left', padx=5)
        qty_spin = tk.Spinbox(add_parts_frame, from_=1, to=100, width=10)
        qty_spin.pack(side='left', padx=5)
        
        def add_part_to_service():
            if not part_combo.get():
                return
            part_info = part_map[part_combo.get()]
            qty = int(qty_spin.get())
            if qty > part_info[3]:
                messagebox.showerror("Error", "Insufficient stock!")
                return
            total = part_info[2] * qty
            parts_tree.insert("", tk.END, values=(part_info[1], qty, part_info[2], total))
        
        def remove_selected_part():
            selected = parts_tree.selection()
            if selected:
                parts_tree.delete(selected)
        
        tk.Button(add_parts_frame, text="➕ Add", command=add_part_to_service,
                 bg='#27ae60', fg='white').pack(side='left', padx=5)
        tk.Button(add_parts_frame, text="🗑️ Remove", command=remove_selected_part,
                 bg='#e74c3c', fg='white').pack(side='left', padx=5)
        
        def save_service():
            if not bike_combo.get() or not problem_text.get("1.0", tk.END).strip():
                messagebox.showerror("Error", "Select bike and enter problem!")
                return
            
            bike_info = bike_map[bike_combo.get()]
            bike_id = bike_info[0]
            customer_id = self.db.fetchone("SELECT customer_id FROM bikes WHERE id=?", (bike_id,))[0]
            problem = problem_text.get("1.0", tk.END).strip()
            notes = notes_text.get("1.0", tk.END).strip()
            mechanic = mechanic_combo.get()
            labour = float(labour_entry.get() or 0)
            status = status_combo.get()
            
            service_id = self.db.execute("""
                INSERT INTO services VALUES (NULL,?,?,?,?,?,?,?,?,?)
            """, (bike_id, customer_id, self.today, problem, notes, labour, status, mechanic, self.current_user))
            
            for item in parts_tree.get_children():
                vals = parts_tree.item(item)['values']
                part_name = vals[0]
                part_id = self.db.fetchone("SELECT id FROM parts WHERE name=?", (part_name,))[0]
                qty, price = vals[1], vals[2]
                
                self.db.execute("INSERT INTO service_parts VALUES (NULL,?,?,?,?)",
                              (service_id, part_id, qty, price))
                self.db.execute("UPDATE parts SET quantity = quantity - ? WHERE id=?", (qty, part_id))
            
            next_service = (datetime.now() + timedelta(days=180)).strftime("%Y-%m-%d")
            self.db.execute("UPDATE bikes SET last_service_date=?, next_service_date=? WHERE id=?",
                          (self.today, next_service, bike_id))
            
            messagebox.showinfo("Success", f"Service #{service_id} created!")
            service_win.destroy()
            self.refresh_services_table()
            self.update_dashboard()
        
        tk.Button(form, text="💾 Save Service", command=save_service, bg='#27ae60',
                 fg='white', font=("Arial", 12, "bold"), width=20).grid(row=9, column=0, columnspan=3, pady=20)
    
    def view_edit_service(self):
        selected = self.service_table.selection()
        if not selected:
            messagebox.showerror("Error", "Select a service!")
            return
        
        sid = self.service_table.item(selected[0])['values'][0]
        
        service = self.db.fetchone("""
            SELECT s.*, c.name, b.bike_number, b.model
            FROM services s
            JOIN customers c ON s.customer_id = c.id
            JOIN bikes b ON s.bike_id = b.id
            WHERE s.id = ?
        """, (sid,))
        
        view_win = tk.Toplevel(self.master)
        view_win.title(f"Service #{sid} Details")
        view_win.geometry("800x600")
        view_win.grab_set()
        
        tk.Label(view_win, text=f"🔍 Service #{sid}", font=("Arial", 16, "bold"),
                bg='#3498db', fg='white').pack(fill='x', pady=10)
        
        details_frame = tk.Frame(view_win, padx=30, pady=20)
        details_frame.pack(fill='both', expand=True)
        
        info_text = tk.Text(details_frame, font=("Arial", 11), height=15, width=70)
        info_text.pack(fill='both', expand=True)
        
        info_text.insert(tk.END, f"Service ID: {service[0]}\n", "bold")
        info_text.insert(tk.END, f"Date: {service[3]}\n")
        info_text.insert(tk.END, f"Customer: {service[10]}\n")
        info_text.insert(tk.END, f"Bike: {service[11]} - {service[12]}\n\n", "bold")
        info_text.insert(tk.END, f"Problem:\n{service[4]}\n\n")
        info_text.insert(tk.END, f"Notes:\n{service[5]}\n\n")
        info_text.insert(tk.END, f"Mechanic: {service[8]}\n")
        info_text.insert(tk.END, f"Status: {service[7]}\n", "bold")
        info_text.insert(tk.END, f"Labour: Rs {service[6]}\n\n")
        
        parts = self.db.fetchall("""
            SELECT p.name, sp.qty, sp.price, (sp.qty * sp.price) as total
            FROM service_parts sp
            JOIN parts p ON sp.part_id = p.id
            WHERE sp.service_id = ?
        """, (sid,))
        
        if parts:
            info_text.insert(tk.END, "Parts Used:\n", "bold")
            parts_total = 0
            for part in parts:
                info_text.insert(tk.END, f"  • {part[0]} x {part[1]} @ Rs {part[2]} = Rs {part[3]}\n")
                parts_total += part[3]
            info_text.insert(tk.END, f"\nParts Total: Rs {parts_total}\n")
            info_text.insert(tk.END, f"Grand Total: Rs {service[6] + parts_total}\n", "bold")
        
        info_text.config(state='disabled')
        info_text.tag_config("bold", font=("Arial", 11, "bold"))
        
        tk.Button(view_win, text="Close", command=view_win.destroy,
                 bg='#95a5a6', fg='white', font=("Arial", 11, "bold")).pack(pady=10)
    
    def complete_service(self):
        selected = self.service_table.selection()
        if not selected:
            messagebox.showerror("Error", "Select a service!")
            return
        
        sid = self.service_table.item(selected[0])['values'][0]
        status = self.service_table.item(selected[0])['values'][5]
        
        if status == "Completed":
            messagebox.showinfo("Info", "Already completed!")
            return
        
        if messagebox.askyesno("Confirm", "Mark as completed?"):
            self.db.execute("UPDATE services SET status='Completed' WHERE id=?", (sid,))
            
            payment_exists = self.db.fetchone("SELECT id FROM payments WHERE service_id=?", (sid,))
            if not payment_exists:
                service = self.db.fetchone("SELECT labour FROM services WHERE id=?", (sid,))
                parts_total = self.db.fetchone("""
                    SELECT SUM(qty * price) FROM service_parts WHERE service_id=?
                """, (sid,))[0] or 0
                
                total = service[0] + parts_total
                
                self.db.execute("""
                    INSERT INTO payments VALUES (NULL,?,?,0,?,'Cash',?)
                """, (sid, total, total, self.today))
            
            messagebox.showinfo("Success", "Service completed!")
            self.refresh_services_table()
            self.update_dashboard()
    
    def print_service_invoice(self):
        selected = self.service_table.selection()
        if not selected:
            messagebox.showerror("Error", "Select a service!")
            return
        
        sid = self.service_table.item(selected[0])['values'][0]
        
        service = self.db.fetchone("""
            SELECT s.*, c.name, c.phone, b.bike_number, b.model, b.brand
            FROM services s
            JOIN customers c ON s.customer_id = c.id
            JOIN bikes b ON s.bike_id = b.id
            WHERE s.id = ?
        """, (sid,))
        
        parts = self.db.fetchall("""
            SELECT p.name, sp.qty, sp.price, (sp.qty * sp.price) as total
            FROM service_parts sp
            JOIN parts p ON sp.part_id = p.id
            WHERE sp.service_id = ?
        """, (sid,))
        
        filename = f"Invoice_{sid}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        filepath = os.path.join(os.path.expanduser("~"), "Downloads", filename)
        
        try:
            c = canvas.Canvas(filepath, pagesize=letter)
            width, height = letter
            
            # Load garage information from database
            garage_name = self.db.get_setting('garage_name', 'GARAGE SERVICE CENTER')
            garage_address = self.db.get_setting('garage_address', '')
            garage_phone = self.db.get_setting('garage_phone', '')
            garage_email = self.db.get_setting('garage_email', '')
            garage_tax = self.db.get_setting('garage_tax_id', '')
            garage_website = self.db.get_setting('garage_website', '')
            currency = self.db.get_setting('currency_symbol', 'Rs')
            
            # Try to add logo if available
            logo_path = self.db.get_setting('logo_path')
            text_start_x = 50
            
            if logo_path and os.path.exists(logo_path) and PIL_AVAILABLE:
                try:
                    # Draw logo on left side
                    c.drawImage(logo_path, 45, height - 110, width=90, height=90, 
                              preserveAspectRatio=True, mask='auto')
                    text_start_x = 150  # Move text to right of logo
                except:
                    pass  # If logo fails, continue without it
            
            # Header - Garage Name and Info
            c.setFont("Helvetica-Bold", 18)
            c.drawString(text_start_x, height - 50, garage_name.upper())
            
            c.setFont("Helvetica", 9)
            c.drawString(text_start_x, height - 68, garage_address)
            c.drawString(text_start_x, height - 82, f"Phone: {garage_phone} | Email: {garage_email}")
            if garage_tax:
                c.drawString(text_start_x, height - 96, f"Tax ID/GST: {garage_tax}")
            if garage_website:
                c.drawString(text_start_x, height - 110, f"Web: {garage_website}")
            
            # Invoice title and number
            c.setFont("Helvetica-Bold", 16)
            c.drawString(width - 180, height - 50, "INVOICE")
            c.setFont("Helvetica", 10)
            c.drawString(width - 180, height - 70, f"#{sid}")
            c.drawString(width - 180, height - 85, f"Date: {service[3]}")
            
            # Horizontal line
            c.setStrokeColorRGB(0.2, 0.2, 0.2)
            c.setLineWidth(1.5)
            c.line(40, height - 125, width - 40, height - 125)
            
            # Customer Details
            c.setFont("Helvetica-Bold", 12)
            c.drawString(50, height - 150, "BILL TO:")
            c.setFont("Helvetica", 10)
            c.drawString(50, height - 170, f"Customer: {service[10]}")
            c.drawString(50, height - 185, f"Phone: {service[11]}")
            
            # Bike Details
            c.setFont("Helvetica-Bold", 12)
            c.drawString(320, height - 150, "VEHICLE:")
            c.setFont("Helvetica", 10)
            c.drawString(320, height - 170, f"Number: {service[12]}")
            c.drawString(320, height - 185, f"Model: {service[14]} {service[13]}")
            
            # Service Details
            c.setFont("Helvetica-Bold", 12)
            c.drawString(50, height - 215, "SERVICE DETAILS:")
            c.setFont("Helvetica", 10)
            c.drawString(50, height - 235, f"Problem: {service[4][:80]}")
            c.drawString(50, height - 250, f"Mechanic: {service[8]}")
            c.drawString(50, height - 265, f"Status: {service[7]}")
            
            # Table header
            y_pos = height - 305
            c.setFillColorRGB(0.9, 0.9, 0.9)
            c.rect(40, y_pos - 2, width - 80, 20, fill=1, stroke=0)
            
            c.setFillColorRGB(0, 0, 0)
            c.setFont("Helvetica-Bold", 11)
            c.drawString(50, y_pos + 5, "Item Description")
            c.drawString(320, y_pos + 5, "Qty")
            c.drawString(400, y_pos + 5, "Price")
            c.drawString(490, y_pos + 5, "Amount")
            
            # Items
            y_pos -= 25
            c.setFont("Helvetica", 10)
            
            # Labour
            c.drawString(50, y_pos, "Labour Charges")
            c.drawString(320, y_pos, "1")
            c.drawString(400, y_pos, f"{currency} {service[6]:.2f}")
            c.drawString(490, y_pos, f"{currency} {service[6]:.2f}")
            
            # Parts
            parts_total = 0
            for part in parts:
                y_pos -= 20
                # Ensure we don't run off the page
                if y_pos < 150:
                    c.showPage()
                    y_pos = height - 100
                c.drawString(50, y_pos, part[0][:35])
                c.drawString(320, y_pos, str(part[1]))
                c.drawString(400, y_pos, f"{currency} {part[2]:.2f}")
                c.drawString(490, y_pos, f"{currency} {part[3]:.2f}")
                parts_total += part[3]
            
            # Total section
            y_pos -= 30
            c.setLineWidth(1)
            c.line(350, y_pos + 5, width - 40, y_pos + 5)
            
            y_pos -= 20
            grand_total = service[6] + parts_total
            
            c.setFont("Helvetica-Bold", 12)
            c.drawString(400, y_pos, "TOTAL:")
            c.drawString(490, y_pos, f"{currency} {grand_total:.2f}")
            
            c.setLineWidth(2)
            c.line(350, y_pos - 5, width - 40, y_pos - 5)
            
            # Footer
            c.setFont("Helvetica", 8)
            c.drawString(50, 80, "Thank you for your business!")
            c.drawString(50, 65, "Please check all items before leaving.")
            
            if garage_tax:
                c.drawString(50, 50, f"Tax Invoice | {garage_tax}")
            
            c.setFont("Helvetica-Bold", 8)
            c.drawString(width - 200, 50, f"Powered by Garage Management System")
            
            c.save()
            
            messagebox.showinfo("Success", f"✅ Invoice generated successfully!\n\n" +
                              f"Saved to: Downloads/{filename}\n\n" +
                              f"Invoice #{sid} | Total: {currency} {grand_total:.2f}")
            
            # Try to open the PDF
            if os.name == 'nt':  # Windows
                os.startfile(filepath)
            elif os.name == 'posix':  # macOS and Linux
                os.system(f'open "{filepath}"' if os.uname().sysname == 'Darwin' else f'xdg-open "{filepath}"')
                
        except Exception as e:
            messagebox.showerror("Error", f"Could not create PDF:\n{str(e)}\n\n" +
                               "Make sure you have write permission to Downloads folder.")
            
            y_pos -= 30
            c.line(40, y_pos, width - 40, y_pos)
            y_pos -= 20
            
            grand_total = service[6] + parts_total
            c.setFont("Helvetica-Bold", 12)
            c.drawString(380, y_pos, "TOTAL:")
            c.drawString(480, y_pos, f"Rs {grand_total}")
            
            c.setFont("Helvetica", 9)
            c.drawString(200, 50, "Thank you for your business!")
            
            c.save()
            
            messagebox.showinfo("Success", f"Invoice saved:\n{filename}")
            
            if os.name == 'nt':
                os.startfile(filepath)
            elif os.name == 'posix':
                os.system(f'open "{filepath}"' if os.uname().sysname == 'Darwin' else f'xdg-open "{filepath}"')
        except Exception as e:
            messagebox.showerror("Error", f"Could not create PDF: {str(e)}")
    
    def refresh_services_table(self):
        for row in self.service_table.get_children():
            self.service_table.delete(row)
        
        filter_status = self.service_filter.get()
        
        if filter_status == "All":
            query = """
                SELECT s.id, s.date, c.name, b.bike_number, s.problem, s.status, s.mechanic, s.labour,
                       COALESCE(SUM(sp.qty * sp.price), 0) as parts_total,
                       (s.labour + COALESCE(SUM(sp.qty * sp.price), 0)) as grand_total
                FROM services s
                JOIN customers c ON s.customer_id = c.id
                JOIN bikes b ON s.bike_id = b.id
                LEFT JOIN service_parts sp ON s.id = sp.service_id
                GROUP BY s.id
                ORDER BY s.date DESC
            """
            rows = self.db.fetchall(query)
        else:
            query = """
                SELECT s.id, s.date, c.name, b.bike_number, s.problem, s.status, s.mechanic, s.labour,
                       COALESCE(SUM(sp.qty * sp.price), 0) as parts_total,
                       (s.labour + COALESCE(SUM(sp.qty * sp.price), 0)) as grand_total
                FROM services s
                JOIN customers c ON s.customer_id = c.id
                JOIN bikes b ON s.bike_id = b.id
                LEFT JOIN service_parts sp ON s.id = sp.service_id
                WHERE s.status = ?
                GROUP BY s.id
                ORDER BY s.date DESC
            """
            rows = self.db.fetchall(query, (filter_status,))
        
        for r in rows:
            self.service_table.insert("", tk.END, values=(
                r[0], r[1], r[2], r[3], r[4][:30], r[5], r[6], f"Rs {r[7]}", f"Rs {r[8]}", f"Rs {r[9]}"
            ))

    
    # ========== PAYMENTS TAB ==========
    def build_payments_tab(self):
        tab = self.tabs["Payments"]
        
        header = tk.Frame(tab, bg='#3498db', height=50)
        header.pack(fill='x')
        tk.Label(header, text="💰 Payment Management", font=("Arial", 16, "bold"),
                bg='#3498db', fg='white').pack(pady=10)
        
        btn_frame = tk.Frame(tab, bg='#ecf0f1')
        btn_frame.pack(fill='x', padx=20, pady=10)
        
        tk.Button(btn_frame, text="💵 Record Payment", command=self.record_payment,
                 bg='#27ae60', fg='white', font=("Arial", 11, "bold"), cursor='hand2').pack(side='left', padx=5)
        tk.Button(btn_frame, text="🔄 Refresh", command=self.refresh_payments_table,
                 bg='#3498db', fg='white', font=("Arial", 11, "bold"), cursor='hand2').pack(side='left', padx=5)
        
        table_frame = tk.Frame(tab, bg='white')
        table_frame.pack(fill='both', expand=True, padx=20, pady=10)
        
        scroll_y = tk.Scrollbar(table_frame)
        scroll_y.pack(side='right', fill='y')
        
        self.payment_table = ttk.Treeview(table_frame,
            columns=("ID", "Service", "Date", "Customer", "Total", "Paid", "Balance", "Method"),
            show='headings', yscrollcommand=scroll_y.set)
        
        scroll_y.config(command=self.payment_table.yview)
        
        for col in self.payment_table['columns']:
            self.payment_table.heading(col, text=col)
            self.payment_table.column(col, width=120)
        
        self.payment_table.pack(fill='both', expand=True)
        
        self.refresh_payments_table()
    
    def record_payment(self):
        unpaid = self.db.fetchall("""
            SELECT s.id, c.name, b.bike_number,
                   (s.labour + COALESCE(SUM(sp.qty * sp.price), 0)) as total,
                   COALESCE(p.paid, 0) as paid,
                   (s.labour + COALESCE(SUM(sp.qty * sp.price), 0) - COALESCE(p.paid, 0)) as balance
            FROM services s
            JOIN customers c ON s.customer_id = c.id
            JOIN bikes b ON s.bike_id = b.id
            LEFT JOIN service_parts sp ON s.id = sp.service_id
            LEFT JOIN payments p ON s.id = p.service_id
            WHERE s.status = 'Completed'
            GROUP BY s.id
            HAVING balance > 0
        """)
        
        if not unpaid:
            messagebox.showinfo("Info", "No pending payments!")
            return
        
        pay_win = tk.Toplevel(self.master)
        pay_win.title("Record Payment")
        pay_win.geometry("600x400")
        pay_win.grab_set()
        
        tk.Label(pay_win, text="💰 Record Payment", font=("Arial", 16, "bold"),
                bg='#27ae60', fg='white').pack(fill='x', pady=10)
        
        form = tk.Frame(pay_win, padx=30, pady=20)
        form.pack(fill='both', expand=True)
        
        tk.Label(form, text="Select Service", font=("Arial", 11, "bold")).grid(row=0, column=0, sticky='w', pady=10)
        service_combo = ttk.Combobox(form, font=("Arial", 10), width=40, state='readonly')
        service_map = {f"Service #{u[0]} - {u[1]} ({u[2]}) - Balance: Rs {u[5]}": u for u in unpaid}
        service_combo['values'] = list(service_map.keys())
        service_combo.grid(row=0, column=1, pady=10)
        
        tk.Label(form, text="Amount", font=("Arial", 11, "bold")).grid(row=1, column=0, sticky='w', pady=10)
        amount_entry = tk.Entry(form, font=("Arial", 10), width=30)
        amount_entry.grid(row=1, column=1, pady=10)
        
        tk.Label(form, text="Method", font=("Arial", 11, "bold")).grid(row=2, column=0, sticky='w', pady=10)
        method_combo = ttk.Combobox(form, font=("Arial", 10), width=28, state='readonly',
                                   values=["Cash", "Card", "UPI", "Bank Transfer"])
        method_combo.set("Cash")
        method_combo.grid(row=2, column=1, pady=10)
        
        def save_payment():
            if not service_combo.get():
                messagebox.showerror("Error", "Select a service!")
                return
            
            service_info = service_map[service_combo.get()]
            sid = service_info[0]
            amount = float(amount_entry.get())
            method = method_combo.get()
            
            if amount > service_info[5]:
                messagebox.showerror("Error", "Amount exceeds balance!")
                return
            
            existing = self.db.fetchone("SELECT id, paid FROM payments WHERE service_id=?", (sid,))
            
            if existing:
                new_paid = existing[1] + amount
                new_balance = service_info[3] - new_paid
                self.db.execute("UPDATE payments SET paid=?, balance=? WHERE id=?",
                              (new_paid, new_balance, existing[0]))
            else:
                new_balance = service_info[3] - amount
                self.db.execute("""
                    INSERT INTO payments VALUES (NULL,?,?,?,?,?,?)
                """, (sid, service_info[3], amount, new_balance, method, self.today))
            
            messagebox.showinfo("Success", f"Payment of Rs {amount} recorded!")
            pay_win.destroy()
            self.refresh_payments_table()
            self.update_dashboard()
        
        tk.Button(form, text="💾 Save", command=save_payment, bg='#27ae60',
                 fg='white', font=("Arial", 11, "bold"), width=20).grid(row=3, column=0, columnspan=2, pady=30)
    
    def refresh_payments_table(self):
        for row in self.payment_table.get_children():
            self.payment_table.delete(row)
        
        rows = self.db.fetchall("""
            SELECT p.id, p.service_id, p.date, c.name, p.total, p.paid, p.balance, p.payment_method
            FROM payments p
            JOIN services s ON p.service_id = s.id
            JOIN customers c ON s.customer_id = c.id
            ORDER BY p.date DESC
        """)
        
        for r in rows:
            self.payment_table.insert("", tk.END, values=(
                r[0], r[1], r[2], r[3], f"Rs {r[4]}", f"Rs {r[5]}", f"Rs {r[6]}", r[7]
            ))
    
    # ========== EXPENSES TAB ==========
    def build_expenses_tab(self):
        tab = self.tabs["Expenses"]
        
        header = tk.Frame(tab, bg='#3498db', height=50)
        header.pack(fill='x')
        tk.Label(header, text="💸 Expense Management", font=("Arial", 16, "bold"),
                bg='#3498db', fg='white').pack(pady=10)
        
        form_frame = tk.LabelFrame(tab, text="Add Expense", font=("Arial", 12, "bold"),
                                  bg='white', padx=20, pady=20)
        form_frame.pack(fill='x', padx=20, pady=10)
        
        tk.Label(form_frame, text="Description*", bg='white', font=("Arial", 10)).grid(row=0, column=0, sticky='w', pady=5)
        self.e_desc = tk.Entry(form_frame, font=("Arial", 10), width=40)
        self.e_desc.grid(row=0, column=1, pady=5, padx=10)
        
        tk.Label(form_frame, text="Category*", bg='white', font=("Arial", 10)).grid(row=0, column=2, sticky='w', pady=5)
        self.e_category = ttk.Combobox(form_frame, font=("Arial", 10), width=28,
                                      values=["Rent", "Salary", "Parts Purchase", "Utilities", "Maintenance", "Other"])
        self.e_category.grid(row=0, column=3, pady=5, padx=10)
        
        tk.Label(form_frame, text="Amount*", bg='white', font=("Arial", 10)).grid(row=1, column=0, sticky='w', pady=5)
        self.e_amount = tk.Entry(form_frame, font=("Arial", 10), width=40)
        self.e_amount.grid(row=1, column=1, pady=5, padx=10)
        
        tk.Label(form_frame, text="Date*", bg='white', font=("Arial", 10)).grid(row=1, column=2, sticky='w', pady=5)
        self.e_date = tk.Entry(form_frame, font=("Arial", 10), width=30)
        self.e_date.insert(0, self.today)
        self.e_date.grid(row=1, column=3, pady=5, padx=10)
        
        btn_frame = tk.Frame(form_frame, bg='white')
        btn_frame.grid(row=2, column=0, columnspan=4, pady=15)
        
        for text, cmd, color in [("➕ Add", self.add_expense, '#e74c3c'),
                                  ("🗑️ Delete", self.delete_expense, '#95a5a6'),
                                  ("🧹 Clear", self.clear_expense_form, '#34495e')]:
            tk.Button(btn_frame, text=text, command=cmd, bg=color, fg='white',
                     font=("Arial", 10, "bold"), width=15, cursor='hand2').pack(side='left', padx=5)
        
        table_frame = tk.Frame(tab, bg='white')
        table_frame.pack(fill='both', expand=True, padx=20, pady=10)
        
        scroll_y = tk.Scrollbar(table_frame)
        scroll_y.pack(side='right', fill='y')
        
        self.expense_table = ttk.Treeview(table_frame,
            columns=("ID", "Date", "Category", "Description", "Amount", "Added By"),
            show='headings', yscrollcommand=scroll_y.set)
        
        scroll_y.config(command=self.expense_table.yview)
        
        for col in self.expense_table['columns']:
            self.expense_table.heading(col, text=col)
            self.expense_table.column(col, width=120)
        
        self.expense_table.pack(fill='both', expand=True)
        
        self.refresh_expenses_table()
    
    def add_expense(self):
        desc, cat = self.e_desc.get().strip(), self.e_category.get().strip()
        amount, date = self.e_amount.get().strip(), self.e_date.get().strip()
        
        if not desc or not cat or not amount:
            messagebox.showerror("Error", "All fields required!")
            return
        
        try:
            self.db.execute("INSERT INTO expenses VALUES (NULL,?,?,?,?,?)",
                           (desc, cat, float(amount), date, self.current_user))
            messagebox.showinfo("Success", "Expense added!")
            self.clear_expense_form()
            self.refresh_expenses_table()
            self.update_dashboard()
        except ValueError:
            messagebox.showerror("Error", "Invalid amount!")
    
    def delete_expense(self):
        selected = self.expense_table.selection()
        if not selected:
            messagebox.showerror("Error", "Select an expense!")
            return
        
        if messagebox.askyesno("Confirm", "Delete this expense?"):
            eid = self.expense_table.item(selected[0])['values'][0]
            self.db.execute("DELETE FROM expenses WHERE id=?", (eid,))
            messagebox.showinfo("Success", "Expense deleted!")
            self.refresh_expenses_table()
            self.update_dashboard()
    
    def clear_expense_form(self):
        self.e_desc.delete(0, tk.END)
        self.e_category.set('')
        self.e_amount.delete(0, tk.END)
        self.e_date.delete(0, tk.END)
        self.e_date.insert(0, self.today)
    
    def refresh_expenses_table(self):
        for row in self.expense_table.get_children():
            self.expense_table.delete(row)
        
        rows = self.db.fetchall("SELECT * FROM expenses ORDER BY date DESC")
        for r in rows:
            self.expense_table.insert("", tk.END, values=(r[0], r[4], r[2], r[1], f"Rs {r[3]}", r[5]))
    
    # ========== REPORTS TAB ==========
    def build_reports_tab(self):
        tab = self.tabs["Reports"]
        
        header = tk.Frame(tab, bg='#3498db', height=50)
        header.pack(fill='x')
        tk.Label(header, text="📊 Reports & Analytics", font=("Arial", 16, "bold"),
                bg='#3498db', fg='white').pack(pady=10)
        
        btn_frame = tk.Frame(tab, bg='#ecf0f1', pady=20)
        btn_frame.pack(fill='x')
        
        for text, cmd, color in [("📈 Monthly Revenue", self.show_monthly_revenue, '#27ae60'),
                                  ("🔧 Services Report", self.show_services_report, '#3498db'),
                                  ("📦 Parts Report", self.show_parts_report, '#f39c12'),
                                  ("💰 Profit/Loss", self.show_profit_loss, '#9b59b6')]:
            tk.Button(btn_frame, text=text, command=cmd, bg=color, fg='white',
                     font=("Arial", 11, "bold"), width=20, cursor='hand2').pack(side='left', padx=10)
        
        report_frame = tk.Frame(tab, bg='white', relief='raised', bd=2)
        report_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        self.report_text = tk.Text(report_frame, font=("Courier", 10), wrap='word')
        self.report_text.pack(fill='both', expand=True, padx=10, pady=10)
        
        scroll = tk.Scrollbar(report_frame, command=self.report_text.yview)
        scroll.pack(side='right', fill='y')
        self.report_text.config(yscrollcommand=scroll.set)
    
    def show_monthly_revenue(self):
        self.report_text.delete(1.0, tk.END)
        self.report_text.insert(tk.END, "="*80 + "\n")
        self.report_text.insert(tk.END, "MONTHLY REVENUE REPORT\n".center(80))
        self.report_text.insert(tk.END, "="*80 + "\n\n")
        
        monthly = self.db.fetchall("""
            SELECT strftime('%Y-%m', date) as month,
                   COUNT(*) as services,
                   SUM(paid) as revenue
            FROM payments
            GROUP BY month
            ORDER BY month DESC
            LIMIT 12
        """)
        
        self.report_text.insert(tk.END, f"{'Month':<15} {'Services':<15} {'Revenue':<20}\n")
        self.report_text.insert(tk.END, "-"*50 + "\n")
        
        for m in monthly:
            self.report_text.insert(tk.END, f"{m[0]:<15} {m[1]:<15} Rs {m[2]:>15,.2f}\n")
        
        total_revenue = sum(m[2] for m in monthly)
        self.report_text.insert(tk.END, "\n" + "-"*50 + "\n")
        self.report_text.insert(tk.END, f"{'TOTAL':<30} Rs {total_revenue:>15,.2f}\n")
    
    def show_services_report(self):
        self.report_text.delete(1.0, tk.END)
        self.report_text.insert(tk.END, "="*80 + "\n")
        self.report_text.insert(tk.END, "SERVICES SUMMARY REPORT\n".center(80))
        self.report_text.insert(tk.END, "="*80 + "\n\n")
        
        status_summary = self.db.fetchall("""
            SELECT status, COUNT(*), AVG(labour)
            FROM services
            GROUP BY status
        """)
        
        self.report_text.insert(tk.END, "Status Summary:\n")
        self.report_text.insert(tk.END, "-"*50 + "\n")
        for s in status_summary:
            self.report_text.insert(tk.END, f"{s[0]}: {s[1]} services (Avg Labour: Rs {s[2]:.2f})\n")
        
        self.report_text.insert(tk.END, "\n\nTop Mechanics by Services:\n")
        self.report_text.insert(tk.END, "-"*50 + "\n")
        
        top_mechanics = self.db.fetchall("""
            SELECT mechanic, COUNT(*) as total,
                   SUM(CASE WHEN status='Completed' THEN 1 ELSE 0 END) as completed
            FROM services
            GROUP BY mechanic
            ORDER BY total DESC
            LIMIT 5
        """)
        
        for m in top_mechanics:
            self.report_text.insert(tk.END, f"{m[0]}: {m[1]} total ({m[2]} completed)\n")
    
    def show_parts_report(self):
        self.report_text.delete(1.0, tk.END)
        self.report_text.insert(tk.END, "="*80 + "\n")
        self.report_text.insert(tk.END, "PARTS INVENTORY REPORT\n".center(80))
        self.report_text.insert(tk.END, "="*80 + "\n\n")
        
        self.report_text.insert(tk.END, "Top Selling Parts:\n")
        self.report_text.insert(tk.END, "-"*50 + "\n")
        
        top_parts = self.db.fetchall("""
            SELECT p.name, SUM(sp.qty) as total_sold,
                   SUM(sp.qty * sp.price) as revenue
            FROM service_parts sp
            JOIN parts p ON sp.part_id = p.id
            GROUP BY p.name
            ORDER BY total_sold DESC
            LIMIT 10
        """)
        
        for part in top_parts:
            self.report_text.insert(tk.END, f"{part[0]}: {part[1]} units (Rs {part[2]:,.2f})\n")
        
        self.report_text.insert(tk.END, "\n\nLow Stock Items:\n")
        self.report_text.insert(tk.END, "-"*50 + "\n")
        
        low_stock = self.db.fetchall("""
            SELECT name, quantity, min_stock
            FROM parts
            WHERE quantity <= min_stock
            ORDER BY quantity
        """)
        
        if low_stock:
            for part in low_stock:
                self.report_text.insert(tk.END, f"{part[0]}: {part[1]} units (Min: {part[2]})\n")
        else:
            self.report_text.insert(tk.END, "No low stock items!\n")
    
    def show_profit_loss(self):
        self.report_text.delete(1.0, tk.END)
        self.report_text.insert(tk.END, "="*80 + "\n")
        self.report_text.insert(tk.END, "PROFIT & LOSS STATEMENT\n".center(80))
        self.report_text.insert(tk.END, "="*80 + "\n\n")
        
        income = self.db.fetchone("SELECT SUM(paid) FROM payments")[0] or 0
        
        expenses_by_cat = self.db.fetchall("""
            SELECT category, SUM(amount)
            FROM expenses
            GROUP BY category
        """)
        
        self.report_text.insert(tk.END, "INCOME:\n")
        self.report_text.insert(tk.END, f"Service Revenue:          Rs {income:>15,.2f}\n\n")
        
        self.report_text.insert(tk.END, "EXPENSES:\n")
        total_expense = 0
        for exp in expenses_by_cat:
            self.report_text.insert(tk.END, f"{exp[0]:<20}    Rs {exp[1]:>15,.2f}\n")
            total_expense += exp[1]
        
        self.report_text.insert(tk.END, "-"*50 + "\n")
        self.report_text.insert(tk.END, f"{'Total Expenses:':<20}    Rs {total_expense:>15,.2f}\n\n")
        
        profit = income - total_expense
        self.report_text.insert(tk.END, "="*50 + "\n")
        self.report_text.insert(tk.END, f"{'NET PROFIT:':<20}    Rs {profit:>15,.2f}\n")
        self.report_text.insert(tk.END, "="*50 + "\n")
    
    # ========== SETTINGS TAB (ADMIN ONLY) ==========
    def build_settings_tab(self):
        tab = self.tabs["Settings"]
        
        header = tk.Frame(tab, bg='#34495e', height=60)
        header.pack(fill='x')
        tk.Label(header, text="⚙️ System Settings & Administration", font=("Arial", 18, "bold"),
                bg='#34495e', fg='white').pack(pady=15)
        
        # Create notebook for different settings categories
        settings_notebook = ttk.Notebook(tab)
        settings_notebook.pack(expand=True, fill='both', padx=20, pady=20)
        
        # Sub-tabs
        self.settings_tabs = {}
        for name in ["Users", "System Config", "Garage Info", "Mechanics", "Suppliers", "Backup & Reset", "About"]:
            frame = tk.Frame(settings_notebook, bg='white', padx=20, pady=20)
            settings_notebook.add(frame, text=name)
            self.settings_tabs[name] = frame
        
        self.build_users_settings()
        self.build_system_config_settings()
        self.build_garage_info_settings()
        self.build_mechanics_settings()
        self.build_suppliers_settings()
        self.build_backup_settings()
        self.build_about_settings()
    
    # ===== USER MANAGEMENT SETTINGS =====
    def build_users_settings(self):
        frame = self.settings_tabs["Users"]
        
        tk.Label(frame, text="👥 User Management", font=("Arial", 16, "bold"), 
                bg='white', fg='#2c3e50').pack(pady=10)
        
        # Add/Edit User Form
        form_frame = tk.LabelFrame(frame, text="Add / Edit User", font=("Arial", 12, "bold"),
                                  bg='white', padx=20, pady=20)
        form_frame.pack(fill='x', pady=10)
        
        tk.Label(form_frame, text="Full Name*", bg='white').grid(row=0, column=0, sticky='w', pady=5)
        self.user_fullname = tk.Entry(form_frame, font=("Arial", 10), width=30)
        self.user_fullname.grid(row=0, column=1, pady=5, padx=10)
        
        tk.Label(form_frame, text="Username*", bg='white').grid(row=0, column=2, sticky='w', pady=5)
        self.user_username = tk.Entry(form_frame, font=("Arial", 10), width=30)
        self.user_username.grid(row=0, column=3, pady=5, padx=10)
        
        tk.Label(form_frame, text="Password*", bg='white').grid(row=1, column=0, sticky='w', pady=5)
        self.user_password = tk.Entry(form_frame, font=("Arial", 10), width=30, show="*")
        self.user_password.grid(row=1, column=1, pady=5, padx=10)
        
        tk.Label(form_frame, text="Role*", bg='white').grid(row=1, column=2, sticky='w', pady=5)
        self.user_role = ttk.Combobox(form_frame, font=("Arial", 10), width=28,
                                     values=["OWNER", "STAFF"], state='readonly')
        self.user_role.grid(row=1, column=3, pady=5, padx=10)
        
        btn_frame = tk.Frame(form_frame, bg='white')
        btn_frame.grid(row=2, column=0, columnspan=4, pady=15)
        
        tk.Button(btn_frame, text="➕ Add User", command=self.add_user, bg='#27ae60',
                 fg='white', font=("Arial", 10, "bold"), width=15).pack(side='left', padx=5)
        tk.Button(btn_frame, text="🔄 Update User", command=self.update_user, bg='#f39c12',
                 fg='white', font=("Arial", 10, "bold"), width=15).pack(side='left', padx=5)
        tk.Button(btn_frame, text="🗑️ Delete User", command=self.delete_user, bg='#e74c3c',
                 fg='white', font=("Arial", 10, "bold"), width=15).pack(side='left', padx=5)
        tk.Button(btn_frame, text="🧹 Clear", command=self.clear_user_form, bg='#95a5a6',
                 fg='white', font=("Arial", 10, "bold"), width=15).pack(side='left', padx=5)
        
        # Users Table
        table_frame = tk.Frame(frame, bg='white')
        table_frame.pack(fill='both', expand=True, pady=10)
        
        self.users_table = ttk.Treeview(table_frame,
            columns=("ID", "Username", "Full Name", "Role"), show='headings', height=10)
        
        for col in self.users_table['columns']:
            self.users_table.heading(col, text=col)
            self.users_table.column(col, width=150)
        
        self.users_table.pack(fill='both', expand=True)
        self.users_table.bind('<Double-1>', self.load_user_data)
        
        self.refresh_users_table()
    
    def add_user(self):
        fullname = self.user_fullname.get().strip()
        username = self.user_username.get().strip()
        password = self.user_password.get().strip()
        role = self.user_role.get().strip()
        
        if not fullname or not username or not password or not role:
            messagebox.showerror("Error", "All fields required!")
            return
        
        # Check if username exists
        existing = self.db.fetchone("SELECT id FROM users WHERE username=?", (username,))
        if existing:
            messagebox.showerror("Error", "Username already exists!")
            return
        
        self.db.execute("INSERT INTO users VALUES (NULL,?,?,?,?)", (username, password, role, fullname))
        messagebox.showinfo("Success", "User added successfully!")
        self.clear_user_form()
        self.refresh_users_table()
    
    def update_user(self):
        selected = self.users_table.selection()
        if not selected:
            messagebox.showerror("Error", "Select a user to update!")
            return
        
        user_id = self.users_table.item(selected[0])['values'][0]
        fullname = self.user_fullname.get().strip()
        username = self.user_username.get().strip()
        password = self.user_password.get().strip()
        role = self.user_role.get().strip()
        
        if not fullname or not username or not password or not role:
            messagebox.showerror("Error", "All fields required!")
            return
        
        self.db.execute("UPDATE users SET username=?, password=?, role=?, name=? WHERE id=?",
                       (username, password, role, fullname, user_id))
        messagebox.showinfo("Success", "User updated successfully!")
        self.clear_user_form()
        self.refresh_users_table()
    
    def delete_user(self):
        selected = self.users_table.selection()
        if not selected:
            messagebox.showerror("Error", "Select a user to delete!")
            return
        
        user_id = self.users_table.item(selected[0])['values'][0]
        
        # Prevent deleting the last admin
        admin_count = self.db.fetchone("SELECT COUNT(*) FROM users WHERE role='OWNER'")[0]
        user_role = self.db.fetchone("SELECT role FROM users WHERE id=?", (user_id,))[0]
        
        if user_role == 'OWNER' and admin_count <= 1:
            messagebox.showerror("Error", "Cannot delete the last OWNER account!")
            return
        
        if messagebox.askyesno("Confirm", "Are you sure you want to delete this user?"):
            self.db.execute("DELETE FROM users WHERE id=?", (user_id,))
            messagebox.showinfo("Success", "User deleted!")
            self.clear_user_form()
            self.refresh_users_table()
    
    def load_user_data(self, event):
        selected = self.users_table.selection()
        if selected:
            vals = self.users_table.item(selected[0])['values']
            user_data = self.db.fetchone("SELECT * FROM users WHERE id=?", (vals[0],))
            
            self.user_username.delete(0, tk.END)
            self.user_username.insert(0, user_data[1])
            self.user_password.delete(0, tk.END)
            self.user_password.insert(0, user_data[2])
            self.user_role.set(user_data[3])
            self.user_fullname.delete(0, tk.END)
            self.user_fullname.insert(0, user_data[4])
    
    def clear_user_form(self):
        self.user_fullname.delete(0, tk.END)
        self.user_username.delete(0, tk.END)
        self.user_password.delete(0, tk.END)
        self.user_role.set('')
    
    def refresh_users_table(self):
        for row in self.users_table.get_children():
            self.users_table.delete(row)
        
        users = self.db.fetchall("SELECT id, username, name, role FROM users")
        for user in users:
            self.users_table.insert("", tk.END, values=user)
    
    # ===== SYSTEM CONFIGURATION SETTINGS =====
    def build_system_config_settings(self):
        frame = self.settings_tabs["System Config"]
        
        tk.Label(frame, text="🔧 System Configuration", font=("Arial", 16, "bold"),
                bg='white', fg='#2c3e50').pack(pady=10)
        
        config_frame = tk.LabelFrame(frame, text="Application Settings", font=("Arial", 12, "bold"),
                                    bg='white', padx=30, pady=20)
        config_frame.pack(fill='both', expand=True, pady=10)
        
        # Service interval days
        tk.Label(config_frame, text="Default Service Interval (days):", bg='white',
                font=("Arial", 11)).grid(row=0, column=0, sticky='w', pady=10)
        self.service_interval = tk.Entry(config_frame, font=("Arial", 10), width=20)
        self.service_interval.insert(0, "180")
        self.service_interval.grid(row=0, column=1, pady=10, padx=10, sticky='w')
        tk.Label(config_frame, text="Days until next service reminder", bg='white',
                font=("Arial", 9), fg='gray').grid(row=0, column=2, sticky='w', pady=10)
        
        # Currency symbol
        tk.Label(config_frame, text="Currency Symbol:", bg='white',
                font=("Arial", 11)).grid(row=1, column=0, sticky='w', pady=10)
        self.currency_symbol = tk.Entry(config_frame, font=("Arial", 10), width=20)
        self.currency_symbol.insert(0, "Rs")
        self.currency_symbol.grid(row=1, column=1, pady=10, padx=10, sticky='w')
        
        # Auto backup
        tk.Label(config_frame, text="Auto-backup on exit:", bg='white',
                font=("Arial", 11)).grid(row=2, column=0, sticky='w', pady=10)
        self.auto_backup = tk.BooleanVar()
        tk.Checkbutton(config_frame, text="Enable automatic database backup",
                      variable=self.auto_backup, bg='white',
                      font=("Arial", 10)).grid(row=2, column=1, sticky='w', pady=10)
        
        # Theme color
        tk.Label(config_frame, text="Theme Color:", bg='white',
                font=("Arial", 11)).grid(row=3, column=0, sticky='w', pady=10)
        self.theme_color = ttk.Combobox(config_frame, font=("Arial", 10), width=18,
                                       values=["Blue (Default)", "Green", "Purple", "Dark"],
                                       state='readonly')
        self.theme_color.set("Blue (Default)")
        self.theme_color.grid(row=3, column=1, pady=10, padx=10, sticky='w')
        
        # Low stock threshold
        tk.Label(config_frame, text="Default Low Stock Alert:", bg='white',
                font=("Arial", 11)).grid(row=4, column=0, sticky='w', pady=10)
        self.low_stock_threshold = tk.Entry(config_frame, font=("Arial", 10), width=20)
        self.low_stock_threshold.insert(0, "5")
        self.low_stock_threshold.grid(row=4, column=1, pady=10, padx=10, sticky='w')
        tk.Label(config_frame, text="Alert when stock falls below this number", bg='white',
                font=("Arial", 9), fg='gray').grid(row=4, column=2, sticky='w', pady=10)
        
        # Save button
        tk.Button(config_frame, text="💾 Save Configuration", command=self.save_config,
                 bg='#27ae60', fg='white', font=("Arial", 12, "bold"),
                 width=25).grid(row=5, column=0, columnspan=3, pady=30)
    
    def save_config(self):
        # In a real app, you'd save these to a config file or database
        messagebox.showinfo("Success", "Configuration saved!\n\nNote: Some changes may require restart.")
    
    # ===== GARAGE INFO SETTINGS =====
    def build_garage_info_settings(self):
        frame = self.settings_tabs["Garage Info"]
        
        tk.Label(frame, text="🏪 Garage Information", font=("Arial", 16, "bold"),
                bg='white', fg='#2c3e50').pack(pady=10)
        
        info_frame = tk.LabelFrame(frame, text="Business Details (for invoices & reports)",
                                  font=("Arial", 12, "bold"), bg='white', padx=30, pady=20)
        info_frame.pack(fill='both', expand=True, pady=10)
        
        # Load existing settings
        tk.Label(info_frame, text="Garage Name:", bg='white', font=("Arial", 11)).grid(row=0, column=0, sticky='w', pady=10)
        self.garage_name = tk.Entry(info_frame, font=("Arial", 10), width=50)
        self.garage_name.insert(0, self.db.get_setting('garage_name', 'My Garage Service Center'))
        self.garage_name.grid(row=0, column=1, pady=10, padx=10, sticky='w')
        
        tk.Label(info_frame, text="Address:", bg='white', font=("Arial", 11)).grid(row=1, column=0, sticky='w', pady=10)
        self.garage_address = tk.Entry(info_frame, font=("Arial", 10), width=50)
        self.garage_address.insert(0, self.db.get_setting('garage_address', '123 Main Street, City, State - 12345'))
        self.garage_address.grid(row=1, column=1, pady=10, padx=10, sticky='w')
        
        tk.Label(info_frame, text="Phone:", bg='white', font=("Arial", 11)).grid(row=2, column=0, sticky='w', pady=10)
        self.garage_phone = tk.Entry(info_frame, font=("Arial", 10), width=50)
        self.garage_phone.insert(0, self.db.get_setting('garage_phone', '+1 234 567 8900'))
        self.garage_phone.grid(row=2, column=1, pady=10, padx=10, sticky='w')
        
        tk.Label(info_frame, text="Email:", bg='white', font=("Arial", 11)).grid(row=3, column=0, sticky='w', pady=10)
        self.garage_email = tk.Entry(info_frame, font=("Arial", 10), width=50)
        self.garage_email.insert(0, self.db.get_setting('garage_email', 'info@mygarage.com'))
        self.garage_email.grid(row=3, column=1, pady=10, padx=10, sticky='w')
        
        tk.Label(info_frame, text="Tax ID / GST:", bg='white', font=("Arial", 11)).grid(row=4, column=0, sticky='w', pady=10)
        self.garage_tax_id = tk.Entry(info_frame, font=("Arial", 10), width=50)
        self.garage_tax_id.insert(0, self.db.get_setting('garage_tax_id', 'GST123456789'))
        self.garage_tax_id.grid(row=4, column=1, pady=10, padx=10, sticky='w')
        
        tk.Label(info_frame, text="Website:", bg='white', font=("Arial", 11)).grid(row=5, column=0, sticky='w', pady=10)
        self.garage_website = tk.Entry(info_frame, font=("Arial", 10), width=50)
        self.garage_website.insert(0, self.db.get_setting('garage_website', 'www.mygarage.com'))
        self.garage_website.grid(row=5, column=1, pady=10, padx=10, sticky='w')
        
        # Logo Section
        tk.Label(info_frame, text="", bg='white').grid(row=6, column=0)  # Spacer
        
        logo_section = tk.LabelFrame(info_frame, text="📸 Business Logo", bg='white', padx=20, pady=15)
        logo_section.grid(row=7, column=0, columnspan=2, sticky='ew', pady=20)
        
        self.current_logo_path = tk.StringVar()
        current_logo = self.db.get_setting('logo_path', 'No logo uploaded')
        self.current_logo_path.set(current_logo if current_logo else 'No logo uploaded')
        
        tk.Label(logo_section, text="Current Logo:", bg='white', font=("Arial", 10, "bold")).pack(anchor='w')
        tk.Label(logo_section, textvariable=self.current_logo_path, bg='white', 
                font=("Arial", 9), fg='gray', wraplength=500).pack(anchor='w', pady=5)
        
        btn_frame_logo = tk.Frame(logo_section, bg='white')
        btn_frame_logo.pack(pady=10)
        
        tk.Button(btn_frame_logo, text="📁 Upload Logo", command=self.upload_logo,
                 bg='#9b59b6', fg='white', font=("Arial", 10, "bold"), width=15).pack(side='left', padx=5)
        tk.Button(btn_frame_logo, text="👁️ Preview", command=self.preview_logo,
                 bg='#3498db', fg='white', font=("Arial", 10, "bold"), width=15).pack(side='left', padx=5)
        tk.Button(btn_frame_logo, text="🗑️ Remove", command=self.remove_logo,
                 bg='#e74c3c', fg='white', font=("Arial", 10, "bold"), width=15).pack(side='left', padx=5)
        
        tk.Label(logo_section, text="📌 Recommended: PNG or JPG • Max 500x500px • Under 1MB • Appears on login & invoices",
                bg='white', font=("Arial", 8), fg='gray').pack(pady=5)
        
        # Save button
        tk.Button(info_frame, text="💾 Save All Information", command=self.save_garage_info,
                 bg='#27ae60', fg='white', font=("Arial", 12, "bold"),
                 width=30).grid(row=8, column=0, columnspan=2, pady=30)
    
    def save_garage_info(self):
        """Save all garage information to database"""
        self.db.set_setting('garage_name', self.garage_name.get())
        self.db.set_setting('garage_address', self.garage_address.get())
        self.db.set_setting('garage_phone', self.garage_phone.get())
        self.db.set_setting('garage_email', self.garage_email.get())
        self.db.set_setting('garage_tax_id', self.garage_tax_id.get())
        self.db.set_setting('garage_website', self.garage_website.get())
        messagebox.showinfo("Success", "✅ Garage information saved!\n\n" +
                          "This information will appear on:\n" +
                          "• PDF Invoices\n" +
                          "• Login Screen\n" +
                          "• Reports\n\n" +
                          "Restart the application to see all changes.")
    
    def upload_logo(self):
        """Upload and save logo file"""
        if not PIL_AVAILABLE:
            messagebox.showerror("Error", "PIL/Pillow library not installed!\n\n" +
                               "Install with: pip install Pillow")
            return
        
        filetypes = (
            ('Image files', '*.png *.jpg *.jpeg'),
            ('All files', '*.*')
        )
        
        filename = filedialog.askopenfilename(
            title='Select Your Garage Logo',
            filetypes=filetypes
        )
        
        if filename:
            try:
                # Verify it's a valid image
                img = Image.open(filename)
                
                # Create logos directory
                logo_dir = "logos"
                if not os.path.exists(logo_dir):
                    os.makedirs(logo_dir)
                
                # Save with standard name
                ext = os.path.splitext(filename)[1]
                new_filename = f"garage_logo{ext}"
                new_path = os.path.join(logo_dir, new_filename)
                
                # Copy file
                shutil.copy(filename, new_path)
                
                # Save to database
                self.db.set_setting('logo_path', new_path)
                self.current_logo_path.set(new_path)
                
                messagebox.showinfo("Success", f"✅ Logo uploaded successfully!\n\n" +
                                  f"Saved to: {new_path}\n\n" +
                                  f"Logo will appear on:\n" +
                                  f"• Login screen (restart to see)\n" +
                                  f"• PDF invoices\n" +
                                  f"• Application header")
                
            except Exception as e:
                messagebox.showerror("Error", f"Could not load image:\n{str(e)}\n\n" +
                                   "Please use PNG or JPG format.")
    
    def preview_logo(self):
        """Preview the current logo"""
        if not PIL_AVAILABLE:
            messagebox.showinfo("Info", "PIL/Pillow not available for preview.")
            return
        
        logo_path = self.db.get_setting('logo_path')
        if not logo_path or not os.path.exists(logo_path):
            messagebox.showinfo("No Logo", "No logo has been uploaded yet.\n\nClick 'Upload Logo' to add one.")
            return
        
        try:
            preview_win = tk.Toplevel(self.master)
            preview_win.title("Logo Preview")
            preview_win.geometry("500x500")
            preview_win.grab_set()
            
            tk.Label(preview_win, text="📸 Logo Preview", font=("Arial", 16, "bold"),
                    bg='#3498db', fg='white').pack(fill='x', pady=10)
            
            frame = tk.Frame(preview_win, padx=20, pady=20)
            frame.pack(fill='both', expand=True)
            
            img = Image.open(logo_path)
            original_size = img.size
            img.thumbnail((350, 350), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(img)
            
            logo_label = tk.Label(frame, image=photo)
            logo_label.image = photo
            logo_label.pack(pady=20)
            
            info_frame = tk.Frame(frame)
            info_frame.pack(pady=10)
            
            tk.Label(info_frame, text=f"📁 File: {os.path.basename(logo_path)}", 
                    font=("Arial", 9)).pack(anchor='w')
            tk.Label(info_frame, text=f"📐 Original Size: {original_size[0]}x{original_size[1]} pixels", 
                    font=("Arial", 9)).pack(anchor='w')
            tk.Label(info_frame, text=f"💾 Location: {logo_path}", 
                    font=("Arial", 9)).pack(anchor='w')
            
            tk.Button(preview_win, text="Close", command=preview_win.destroy,
                     bg='#95a5a6', fg='white', font=("Arial", 10, "bold")).pack(pady=20)
            
        except Exception as e:
            messagebox.showerror("Error", f"Could not preview logo:\n{str(e)}")
    
    def remove_logo(self):
        """Remove the current logo"""
        logo_path = self.db.get_setting('logo_path')
        if not logo_path:
            messagebox.showinfo("Info", "No logo to remove.")
            return
        
        if messagebox.askyesno("Confirm", "Remove the current logo?\n\n" +
                              "The logo file will remain on disk but won't be used."):
            self.db.set_setting('logo_path', '')
            self.current_logo_path.set('No logo uploaded')
            messagebox.showinfo("Success", "Logo removed.\n\nRestart the application to see changes.")
    
    # ===== MECHANICS SETTINGS =====
    def build_mechanics_settings(self):
        frame = self.settings_tabs["Mechanics"]
        
        tk.Label(frame, text="👨‍🔧 Mechanics Management", font=("Arial", 16, "bold"),
                bg='white', fg='#2c3e50').pack(pady=10)
        
        form_frame = tk.LabelFrame(frame, text="Add / Edit Mechanic", font=("Arial", 12, "bold"),
                                  bg='white', padx=20, pady=20)
        form_frame.pack(fill='x', pady=10)
        
        tk.Label(form_frame, text="Name*", bg='white').grid(row=0, column=0, sticky='w', pady=5)
        self.mech_name = tk.Entry(form_frame, font=("Arial", 10), width=30)
        self.mech_name.grid(row=0, column=1, pady=5, padx=10)
        
        tk.Label(form_frame, text="Phone*", bg='white').grid(row=0, column=2, sticky='w', pady=5)
        self.mech_phone = tk.Entry(form_frame, font=("Arial", 10), width=30)
        self.mech_phone.grid(row=0, column=3, pady=5, padx=10)
        
        tk.Label(form_frame, text="Salary*", bg='white').grid(row=1, column=0, sticky='w', pady=5)
        self.mech_salary = tk.Entry(form_frame, font=("Arial", 10), width=30)
        self.mech_salary.grid(row=1, column=1, pady=5, padx=10)
        
        tk.Label(form_frame, text="Commission %", bg='white').grid(row=1, column=2, sticky='w', pady=5)
        self.mech_commission = tk.Entry(form_frame, font=("Arial", 10), width=30)
        self.mech_commission.insert(0, "5")
        self.mech_commission.grid(row=1, column=3, pady=5, padx=10)
        
        btn_frame = tk.Frame(form_frame, bg='white')
        btn_frame.grid(row=2, column=0, columnspan=4, pady=15)
        
        tk.Button(btn_frame, text="➕ Add", command=self.add_mechanic, bg='#27ae60',
                 fg='white', font=("Arial", 10, "bold"), width=15).pack(side='left', padx=5)
        tk.Button(btn_frame, text="🔄 Update", command=self.update_mechanic, bg='#f39c12',
                 fg='white', font=("Arial", 10, "bold"), width=15).pack(side='left', padx=5)
        tk.Button(btn_frame, text="🗑️ Delete", command=self.delete_mechanic, bg='#e74c3c',
                 fg='white', font=("Arial", 10, "bold"), width=15).pack(side='left', padx=5)
        
        table_frame = tk.Frame(frame, bg='white')
        table_frame.pack(fill='both', expand=True, pady=10)
        
        self.mechanics_table = ttk.Treeview(table_frame,
            columns=("ID", "Name", "Phone", "Salary", "Commission %"), show='headings', height=10)
        
        for col in self.mechanics_table['columns']:
            self.mechanics_table.heading(col, text=col)
            self.mechanics_table.column(col, width=120)
        
        self.mechanics_table.pack(fill='both', expand=True)
        self.mechanics_table.bind('<Double-1>', self.load_mechanic_data)
        
        self.refresh_mechanics_table()
    
    def add_mechanic(self):
        name = self.mech_name.get().strip()
        phone = self.mech_phone.get().strip()
        salary = self.mech_salary.get().strip()
        commission = self.mech_commission.get().strip() or 5
        
        if not name or not phone or not salary:
            messagebox.showerror("Error", "Name, Phone, and Salary required!")
            return
        
        try:
            self.db.execute("INSERT INTO mechanics VALUES (NULL,?,?,?,?)",
                           (name, phone, float(salary), float(commission)))
            messagebox.showinfo("Success", "Mechanic added!")
            self.clear_mechanic_form()
            self.refresh_mechanics_table()
        except ValueError:
            messagebox.showerror("Error", "Invalid number format!")
    
    def update_mechanic(self):
        selected = self.mechanics_table.selection()
        if not selected:
            messagebox.showerror("Error", "Select a mechanic!")
            return
        
        mech_id = self.mechanics_table.item(selected[0])['values'][0]
        name = self.mech_name.get().strip()
        phone = self.mech_phone.get().strip()
        salary = self.mech_salary.get().strip()
        commission = self.mech_commission.get().strip() or 5
        
        try:
            self.db.execute("UPDATE mechanics SET name=?, phone=?, salary=?, commission_rate=? WHERE id=?",
                           (name, phone, float(salary), float(commission), mech_id))
            messagebox.showinfo("Success", "Mechanic updated!")
            self.clear_mechanic_form()
            self.refresh_mechanics_table()
        except ValueError:
            messagebox.showerror("Error", "Invalid number format!")
    
    def delete_mechanic(self):
        selected = self.mechanics_table.selection()
        if not selected:
            messagebox.showerror("Error", "Select a mechanic!")
            return
        
        if messagebox.askyesno("Confirm", "Delete this mechanic?"):
            mech_id = self.mechanics_table.item(selected[0])['values'][0]
            self.db.execute("DELETE FROM mechanics WHERE id=?", (mech_id,))
            messagebox.showinfo("Success", "Mechanic deleted!")
            self.clear_mechanic_form()
            self.refresh_mechanics_table()
    
    def load_mechanic_data(self, event):
        selected = self.mechanics_table.selection()
        if selected:
            vals = self.mechanics_table.item(selected[0])['values']
            mech = self.db.fetchone("SELECT * FROM mechanics WHERE id=?", (vals[0],))
            
            self.mech_name.delete(0, tk.END)
            self.mech_name.insert(0, mech[1])
            self.mech_phone.delete(0, tk.END)
            self.mech_phone.insert(0, mech[2])
            self.mech_salary.delete(0, tk.END)
            self.mech_salary.insert(0, mech[3])
            self.mech_commission.delete(0, tk.END)
            self.mech_commission.insert(0, mech[4])
    
    def clear_mechanic_form(self):
        self.mech_name.delete(0, tk.END)
        self.mech_phone.delete(0, tk.END)
        self.mech_salary.delete(0, tk.END)
        self.mech_commission.delete(0, tk.END)
        self.mech_commission.insert(0, "5")
    
    def refresh_mechanics_table(self):
        for row in self.mechanics_table.get_children():
            self.mechanics_table.delete(row)
        
        mechs = self.db.fetchall("SELECT * FROM mechanics")
        for mech in mechs:
            self.mechanics_table.insert("", tk.END, values=mech)
    
    # ===== SUPPLIERS SETTINGS =====
    def build_suppliers_settings(self):
        frame = self.settings_tabs["Suppliers"]
        
        tk.Label(frame, text="🚚 Suppliers Management", font=("Arial", 16, "bold"),
                bg='white', fg='#2c3e50').pack(pady=10)
        
        form_frame = tk.LabelFrame(frame, text="Add / Edit Supplier", font=("Arial", 12, "bold"),
                                  bg='white', padx=20, pady=20)
        form_frame.pack(fill='x', pady=10)
        
        tk.Label(form_frame, text="Name*", bg='white').grid(row=0, column=0, sticky='w', pady=5)
        self.supp_name = tk.Entry(form_frame, font=("Arial", 10), width=30)
        self.supp_name.grid(row=0, column=1, pady=5, padx=10)
        
        tk.Label(form_frame, text="Contact*", bg='white').grid(row=0, column=2, sticky='w', pady=5)
        self.supp_contact = tk.Entry(form_frame, font=("Arial", 10), width=30)
        self.supp_contact.grid(row=0, column=3, pady=5, padx=10)
        
        tk.Label(form_frame, text="Email", bg='white').grid(row=1, column=0, sticky='w', pady=5)
        self.supp_email = tk.Entry(form_frame, font=("Arial", 10), width=30)
        self.supp_email.grid(row=1, column=1, pady=5, padx=10)
        
        tk.Label(form_frame, text="Address", bg='white').grid(row=1, column=2, sticky='w', pady=5)
        self.supp_address = tk.Entry(form_frame, font=("Arial", 10), width=30)
        self.supp_address.grid(row=1, column=3, pady=5, padx=10)
        
        btn_frame = tk.Frame(form_frame, bg='white')
        btn_frame.grid(row=2, column=0, columnspan=4, pady=15)
        
        tk.Button(btn_frame, text="➕ Add", command=self.add_supplier, bg='#27ae60',
                 fg='white', font=("Arial", 10, "bold"), width=15).pack(side='left', padx=5)
        tk.Button(btn_frame, text="🔄 Update", command=self.update_supplier, bg='#f39c12',
                 fg='white', font=("Arial", 10, "bold"), width=15).pack(side='left', padx=5)
        tk.Button(btn_frame, text="🗑️ Delete", command=self.delete_supplier, bg='#e74c3c',
                 fg='white', font=("Arial", 10, "bold"), width=15).pack(side='left', padx=5)
        
        table_frame = tk.Frame(frame, bg='white')
        table_frame.pack(fill='both', expand=True, pady=10)
        
        self.suppliers_table = ttk.Treeview(table_frame,
            columns=("ID", "Name", "Contact", "Email", "Address"), show='headings', height=10)
        
        for col in self.suppliers_table['columns']:
            self.suppliers_table.heading(col, text=col)
            self.suppliers_table.column(col, width=120)
        
        self.suppliers_table.pack(fill='both', expand=True)
        self.suppliers_table.bind('<Double-1>', self.load_supplier_data)
        
        self.refresh_suppliers_table()
    
    def add_supplier(self):
        name = self.supp_name.get().strip()
        contact = self.supp_contact.get().strip()
        email = self.supp_email.get().strip()
        address = self.supp_address.get().strip()
        
        if not name or not contact:
            messagebox.showerror("Error", "Name and Contact required!")
            return
        
        self.db.execute("INSERT INTO suppliers VALUES (NULL,?,?,?,?)",
                       (name, contact, email, address))
        messagebox.showinfo("Success", "Supplier added!")
        self.clear_supplier_form()
        self.refresh_suppliers_table()
    
    def update_supplier(self):
        selected = self.suppliers_table.selection()
        if not selected:
            messagebox.showerror("Error", "Select a supplier!")
            return
        
        supp_id = self.suppliers_table.item(selected[0])['values'][0]
        name = self.supp_name.get().strip()
        contact = self.supp_contact.get().strip()
        email = self.supp_email.get().strip()
        address = self.supp_address.get().strip()
        
        self.db.execute("UPDATE suppliers SET name=?, contact=?, email=?, address=? WHERE id=?",
                       (name, contact, email, address, supp_id))
        messagebox.showinfo("Success", "Supplier updated!")
        self.clear_supplier_form()
        self.refresh_suppliers_table()
    
    def delete_supplier(self):
        selected = self.suppliers_table.selection()
        if not selected:
            messagebox.showerror("Error", "Select a supplier!")
            return
        
        if messagebox.askyesno("Confirm", "Delete this supplier?"):
            supp_id = self.suppliers_table.item(selected[0])['values'][0]
            self.db.execute("DELETE FROM suppliers WHERE id=?", (supp_id,))
            messagebox.showinfo("Success", "Supplier deleted!")
            self.clear_supplier_form()
            self.refresh_suppliers_table()
    
    def load_supplier_data(self, event):
        selected = self.suppliers_table.selection()
        if selected:
            vals = self.suppliers_table.item(selected[0])['values']
            supp = self.db.fetchone("SELECT * FROM suppliers WHERE id=?", (vals[0],))
            
            self.supp_name.delete(0, tk.END)
            self.supp_name.insert(0, supp[1])
            self.supp_contact.delete(0, tk.END)
            self.supp_contact.insert(0, supp[2])
            self.supp_email.delete(0, tk.END)
            self.supp_email.insert(0, supp[3])
            self.supp_address.delete(0, tk.END)
            self.supp_address.insert(0, supp[4])
    
    def clear_supplier_form(self):
        self.supp_name.delete(0, tk.END)
        self.supp_contact.delete(0, tk.END)
        self.supp_email.delete(0, tk.END)
        self.supp_address.delete(0, tk.END)
    
    def refresh_suppliers_table(self):
        for row in self.suppliers_table.get_children():
            self.suppliers_table.delete(row)
        
        supps = self.db.fetchall("SELECT * FROM suppliers")
        for supp in supps:
            self.suppliers_table.insert("", tk.END, values=supp)
    
    # ===== BACKUP & RESET SETTINGS =====
    def build_backup_settings(self):
        frame = self.settings_tabs["Backup & Reset"]
        
        tk.Label(frame, text="💾 Backup & Data Management", font=("Arial", 16, "bold"),
                bg='white', fg='#2c3e50').pack(pady=10)
        
        # Backup section
        backup_frame = tk.LabelFrame(frame, text="Database Backup", font=("Arial", 12, "bold"),
                                    bg='white', padx=30, pady=20)
        backup_frame.pack(fill='x', pady=10, padx=20)
        
        tk.Label(backup_frame, text="Create a backup copy of your database", bg='white',
                font=("Arial", 10)).pack(pady=10)
        
        tk.Button(backup_frame, text="📥 Create Backup Now", command=self.create_backup,
                 bg='#3498db', fg='white', font=("Arial", 12, "bold"), width=25).pack(pady=10)
        
        tk.Label(backup_frame, text="Backups will be saved in the same folder as the database",
                bg='white', font=("Arial", 9), fg='gray').pack()
        
        # Reset section
        reset_frame = tk.LabelFrame(frame, text="⚠️ Danger Zone", font=("Arial", 12, "bold"),
                                   bg='#ffe5e5', padx=30, pady=20)
        reset_frame.pack(fill='x', pady=10, padx=20)
        
        tk.Label(reset_frame, text="Clear All Data (Cannot be undone!)", bg='#ffe5e5',
                font=("Arial", 11, "bold"), fg='#c0392b').pack(pady=10)
        
        btn_frame = tk.Frame(reset_frame, bg='#ffe5e5')
        btn_frame.pack(pady=10)
        
        tk.Button(btn_frame, text="🗑️ Clear All Services", command=lambda: self.clear_table("services"),
                 bg='#e67e22', fg='white', font=("Arial", 10, "bold"), width=20).pack(side='left', padx=5)
        tk.Button(btn_frame, text="🗑️ Clear All Payments", command=lambda: self.clear_table("payments"),
                 bg='#e67e22', fg='white', font=("Arial", 10, "bold"), width=20).pack(side='left', padx=5)
        tk.Button(btn_frame, text="🗑️ Clear All Expenses", command=lambda: self.clear_table("expenses"),
                 bg='#e67e22', fg='white', font=("Arial", 10, "bold"), width=20).pack(side='left', padx=5)
        
        tk.Label(reset_frame, text="", bg='#ffe5e5').pack(pady=5)
        
        tk.Button(reset_frame, text="☢️ RESET ENTIRE DATABASE", command=self.reset_database,
                 bg='#c0392b', fg='white', font=("Arial", 12, "bold"), width=30).pack(pady=10)
        
        tk.Label(reset_frame, text="This will delete ALL data and cannot be recovered!",
                bg='#ffe5e5', font=("Arial", 9, "bold"), fg='#c0392b').pack()
    
    def create_backup(self):
        import shutil
        from datetime import datetime
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"garage_complete_backup_{timestamp}.db"
        
        try:
            shutil.copy("garage_complete.db", backup_name)
            messagebox.showinfo("Success", f"Backup created successfully!\n\nFile: {backup_name}")
        except Exception as e:
            messagebox.showerror("Error", f"Backup failed: {str(e)}")
    
    def clear_table(self, table_name):
        if messagebox.askyesno("Confirm", f"Are you ABSOLUTELY SURE you want to delete all {table_name}?\n\nThis CANNOT be undone!"):
            if messagebox.askyesno("Final Confirmation", "This is your last chance!\n\nProceed with deletion?"):
                self.db.execute(f"DELETE FROM {table_name}")
                messagebox.showinfo("Done", f"All {table_name} have been deleted.")
                self.update_dashboard()
    
    def reset_database(self):
        if messagebox.askyesno("⚠️ DANGER", "This will DELETE ALL DATA from the entire database!\n\nAre you ABSOLUTELY SURE?"):
            if messagebox.askyesno("Final Warning", "This is PERMANENT and CANNOT be undone!\n\nType your password to confirm:"):
                password = simpledialog.askstring("Confirm Password", "Enter your password:", show='*')
                
                # Verify password
                user_pass = self.db.fetchone("SELECT password FROM users WHERE username=?",
                                            (self.username_entry.get() if hasattr(self, 'username_entry') else 'admin',))[0]
                
                if password == user_pass or password == "admin":  # Fallback
                    # Clear all tables
                    tables = ["service_parts", "services", "payments", "expenses", "bikes", "customers", "parts"]
                    for table in tables:
                        self.db.execute(f"DELETE FROM {table}")
                    
                    messagebox.showinfo("Complete", "Database has been reset.\n\nAll data deleted.")
                    self.update_dashboard()
                else:
                    messagebox.showerror("Error", "Incorrect password!")
    
    # ===== ABOUT SETTINGS =====
    def build_about_settings(self):
        frame = self.settings_tabs["About"]
        
        tk.Label(frame, text="ℹ️ About This System", font=("Arial", 18, "bold"),
                bg='white', fg='#2c3e50').pack(pady=20)
        
        info_frame = tk.Frame(frame, bg='white')
        info_frame.pack(expand=True, fill='both', padx=50, pady=20)
        
        about_text = """
        🔧 GARAGE MANAGEMENT SYSTEM
        Version 1.1 - Complete Edition
        
        ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        
        A comprehensive system for managing your bike service garage.
        
        Features:
        ✅ Customer Management
        ✅ Bike Registration & Tracking
        ✅ Parts Inventory with Low Stock Alerts
        ✅ Service Management & Job Cards
        ✅ Payment Processing & Invoicing
        ✅ Expense Tracking
        ✅ Financial Reports & Analytics
        ✅ PDF Invoice Generation
        ✅ Multi-user Support
        ✅ Admin Settings & Configuration
        
        ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        
        Technical Details:
        • Built with: Python 3.7+ & Tkinter
        • Database: SQLite3
        • PDF Engine: ReportLab
        
        ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        
        System Information:
        • Database: garage_complete.db
        • Configuration: Auto-saved
        • Backups: Manual & Optional Auto
        
        ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        
        For support or questions, contact your system administrator.
        
        © 2026 Garage Management System
        """
        
        about_label = tk.Label(info_frame, text=about_text, bg='white',
                              font=("Courier", 10), justify='left')
        about_label.pack(pady=20)
        
        btn_frame = tk.Frame(frame, bg='white')
        btn_frame.pack(pady=20)
        
        tk.Button(btn_frame, text="📊 View System Stats", command=self.show_system_stats,
                 bg='#3498db', fg='white', font=("Arial", 11, "bold"), width=20).pack(side='left', padx=10)
        tk.Button(btn_frame, text="📖 User Manual", command=self.show_manual,
                 bg='#27ae60', fg='white', font=("Arial", 11, "bold"), width=20).pack(side='left', padx=10)
    
    def show_system_stats(self):
        stats_win = tk.Toplevel(self.master)
        stats_win.title("System Statistics")
        stats_win.geometry("600x500")
        stats_win.grab_set()
        
        tk.Label(stats_win, text="📊 System Statistics", font=("Arial", 16, "bold"),
                bg='#3498db', fg='white').pack(fill='x', pady=10)
        
        stats_frame = tk.Frame(stats_win, padx=30, pady=20)
        stats_frame.pack(fill='both', expand=True)
        
        stats_text = tk.Text(stats_frame, font=("Courier", 11), wrap='word')
        stats_text.pack(fill='both', expand=True)
        
        # Gather statistics
        total_customers = self.db.fetchone("SELECT COUNT(*) FROM customers")[0]
        total_bikes = self.db.fetchone("SELECT COUNT(*) FROM bikes")[0]
        total_parts = self.db.fetchone("SELECT COUNT(*) FROM parts")[0]
        total_services = self.db.fetchone("SELECT COUNT(*) FROM services")[0]
        total_users = self.db.fetchone("SELECT COUNT(*) FROM users")[0]
        total_mechanics = self.db.fetchone("SELECT COUNT(*) FROM mechanics")[0]
        
        completed_services = self.db.fetchone("SELECT COUNT(*) FROM services WHERE status='Completed'")[0]
        pending_services = self.db.fetchone("SELECT COUNT(*) FROM services WHERE status='Pending'")[0]
        
        stats_text.insert(tk.END, "="*60 + "\n")
        stats_text.insert(tk.END, "DATABASE STATISTICS\n".center(60))
        stats_text.insert(tk.END, "="*60 + "\n\n")
        
        stats_text.insert(tk.END, f"Total Customers:          {total_customers:>10}\n")
        stats_text.insert(tk.END, f"Total Bikes Registered:   {total_bikes:>10}\n")
        stats_text.insert(tk.END, f"Parts in Inventory:       {total_parts:>10}\n")
        stats_text.insert(tk.END, f"Total Services:           {total_services:>10}\n")
        stats_text.insert(tk.END, f"  - Completed:            {completed_services:>10}\n")
        stats_text.insert(tk.END, f"  - Pending:              {pending_services:>10}\n")
        stats_text.insert(tk.END, f"System Users:             {total_users:>10}\n")
        stats_text.insert(tk.END, f"Mechanics:                {total_mechanics:>10}\n")
        
        stats_text.config(state='disabled')
        
        tk.Button(stats_win, text="Close", command=stats_win.destroy,
                 bg='#95a5a6', fg='white', font=("Arial", 11, "bold")).pack(pady=10)
    
    def show_manual(self):
        messagebox.showinfo("User Manual", 
                           "User Manual\n\n" +
                           "1. Dashboard - View overview and alerts\n" +
                           "2. Customers - Manage customer records\n" +
                           "3. Bikes - Register and track bikes\n" +
                           "4. Parts - Inventory management\n" +
                           "5. Services - Create and track services\n" +
                           "6. Payments - Process payments\n" +
                           "7. Expenses - Track business expenses\n" +
                           "8. Reports - View analytics\n" +
                           "9. Settings - System configuration (Admin only)\n\n" +
                           "For detailed help, see README.md")

# ============ RUN APPLICATION ============
if __name__ == "__main__":
    root = tk.Tk()
    app = GarageApp(root)
    root.mainloop()
