# 🔧 Complete Garage Management System

A comprehensive, professional-grade garage management system built with Python and Tkinter. This system handles all aspects of running a bike service garage including customer management, inventory control, service tracking, billing, and financial reporting.

## ✨ Features

### 1. **Dashboard Overview**
- Real-time financial statistics (Income, Expenses, Profit, Pending Payments)
- Recent services activity feed
- Low stock alerts
- Interactive charts and metrics

### 2. **Customer Management**
- Add, edit, delete customer records
- Store contact details (name, phone, email, address)
- Search and filter customers
- Customer service history tracking

### 3. **Bike Management**
- Register bikes with customer association
- Track bike details (number, brand, model, year)
- Service history per bike
- Automatic next service date calculation (180 days)
- Last service date tracking

### 4. **Parts & Inventory**
- Complete parts catalog with categories
- Stock quantity tracking
- Cost price and selling price management
- Minimum stock level alerts
- Supplier information
- Profit margin calculation
- Color-coded low stock warnings
- Easy stock addition functionality

### 5. **Service Management**
- Create comprehensive service entries
- Assign mechanics to services
- Problem description and notes
- Labour charge calculation
- Parts usage tracking with automatic stock deduction
- Service status tracking (Pending/In Progress/Completed)
- Detailed service viewing
- Service filtering by status

### 6. **Payment Management**
- Record full or partial payments
- Multiple payment methods (Cash, Card, UPI, Bank Transfer)
- Outstanding balance tracking
- Payment history
- Automatic total calculation (labour + parts)

### 7. **Expense Tracking**
- Record business expenses by category
- Categories: Rent, Salary, Parts Purchase, Utilities, Maintenance, Other
- Date-wise expense tracking
- User attribution for accountability

### 8. **Professional PDF Invoicing**
- Generate printable invoices
- Itemized billing (labour + parts)
- Customer and bike details
- Professional formatting
- Auto-save to Downloads folder
- Auto-open after generation

### 9. **Reports & Analytics**
- **Monthly Revenue Report**: Track income trends over 12 months
- **Services Summary**: Status-wise breakdown, mechanic performance
- **Parts Report**: Top-selling parts, low stock alerts
- **Profit & Loss Statement**: Comprehensive financial overview

### 10. **User Management**
- Role-based access (Owner/Staff)
- Secure login system
- User activity tracking
- Default users: admin/admin, staff/staff

## 🚀 Installation

### Prerequisites
- Python 3.7 or higher
- pip (Python package manager)

### Required Libraries
```bash
pip install reportlab
```

Standard libraries (included with Python):
- tkinter
- sqlite3
- datetime
- os

### Installation Steps

1. **Download the system:**
   ```bash
   # Save garage_management_complete.py to your desired location
   ```

2. **Run the application:**
   ```bash
   python garage_management_complete.py
   ```

3. **First-time setup:**
   - The database will be created automatically on first run
   - Default users are created:
     - **Admin**: username: `admin`, password: `admin`
     - **Staff**: username: `staff`, password: `staff`
   - Sample mechanics are added to the database

## 📖 User Guide

### Getting Started

1. **Login:**
   - Use default credentials or create new users
   - Admin has full access, Staff has operational access

2. **Add Customers:**
   - Navigate to "Customers" tab
   - Fill in customer details
   - Click "Add Customer"

3. **Register Bikes:**
   - Go to "Bikes" tab
   - Select customer from dropdown
   - Enter bike details
   - Click "Add Bike"

4. **Stock Parts:**
   - Open "Parts" tab
   - Add parts with pricing and stock levels
   - Set minimum stock levels for alerts

5. **Create Services:**
   - Go to "Services" tab
   - Click "New Service"
   - Select bike, describe problem
   - Assign mechanic, set labour charge
   - Add parts used (auto-deducted from inventory)
   - Save service

6. **Process Payments:**
   - Navigate to "Payments" tab
   - Click "Record Payment"
   - Select service with pending balance
   - Enter amount and payment method
   - Save payment

7. **Track Expenses:**
   - Open "Expenses" tab
   - Add business expenses with category
   - Track spending by type

8. **Generate Reports:**
   - Visit "Reports" tab
   - Click desired report type
   - View comprehensive analytics

9. **Print Invoices:**
   - In "Services" tab, select a service
   - Click "Print Invoice"
   - PDF is auto-generated and saved to Downloads

### Tips for Best Use

- **Regular Stock Updates**: Use "Add Stock" button in Parts tab when inventory arrives
- **Complete Services**: Mark services as "Completed" before recording payments
- **Low Stock Monitoring**: Check dashboard alerts regularly
- **Monthly Reports**: Review Monthly Revenue report at month-end
- **Backup Database**: Regularly backup the `garage_complete.db` file

## 🗂️ Database Structure

The system uses SQLite with 10 tables:

1. **users** - User accounts and roles
2. **customers** - Customer information
3. **bikes** - Bike registrations
4. **parts** - Parts inventory
5. **services** - Service records
6. **service_parts** - Parts used in services
7. **payments** - Payment records
8. **expenses** - Business expenses
9. **suppliers** - Supplier information
10. **mechanics** - Mechanic details

## 🎨 UI Features

- **Modern Design**: Clean, professional interface with color-coded sections
- **Responsive Layout**: Adapts to window resizing
- **Intuitive Navigation**: Tab-based navigation for different modules
- **Visual Feedback**: Color-coded alerts (red for low stock, status indicators)
- **Double-click Loading**: Double-click table rows to load data for editing
- **Tooltips & Validation**: Clear error messages and input validation

## 🔒 Security Features

- Password-protected login
- Role-based access control
- User activity tracking (who added what)
- Secure database storage

## 📊 Business Intelligence

The system tracks:
- Revenue trends over time
- Mechanic performance metrics
- Most popular services
- Best-selling parts
- Expense patterns by category
- Profit margins
- Outstanding payments

## 🛠️ Customization

### Adding New Mechanics
```python
# In the database:
INSERT INTO mechanics VALUES (NULL, 'Name', 'Phone', Salary, Commission%)
```

### Adding New Users
```python
# In the database:
INSERT INTO users VALUES (NULL, 'username', 'password', 'ROLE', 'Full Name')
```

### Modifying Categories
Edit the values in the combobox definitions:
- Parts categories: Line ~XXX
- Expense categories: Line ~XXX

## 🐛 Troubleshooting

**Issue**: "No module named 'reportlab'"
- **Solution**: Install reportlab: `pip install reportlab`

**Issue**: Database locked error
- **Solution**: Close all other instances of the application

**Issue**: PDF not opening automatically
- **Solution**: Check Downloads folder manually, verify PDF reader installed

**Issue**: Window too small
- **Solution**: Application auto-maximizes; if not, manually maximize window

## 📈 Roadmap / Future Enhancements

Possible future additions:
- SMS/Email reminders for service due dates
- Barcode scanning for parts
- Multi-branch support
- Cloud backup integration
- Mobile app version
- Online appointment booking
- Customer portal
- Detailed mechanic commission reports
- Parts supplier auto-ordering
- WhatsApp integration for customer updates

## 💼 License

This software is provided as-is for educational and commercial use.

## 🤝 Support

For issues, questions, or feature requests:
- Review this README thoroughly
- Check database file permissions
- Verify Python and library versions
- Test with default data first

## 📝 Version History

**v1.0.0** (Current)
- Complete garage management system
- All core features implemented
- PDF invoice generation
- Comprehensive reporting
- Low stock alerts
- Multi-user support

---

### Default Login Credentials

**Owner Access:**
- Username: `admin`
- Password: `admin`

**Staff Access:**
- Username: `staff`
- Password: `staff`

**⚠️ IMPORTANT**: Change default passwords after first login!

---

**Built with ❤️ by OPH**
