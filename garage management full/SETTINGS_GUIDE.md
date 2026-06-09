# ⚙️ Settings Tab - Admin Guide

## Overview

The **Settings Tab** is an exclusive admin-only feature that provides comprehensive system configuration and management capabilities. Only users with the **OWNER** role can access this tab.

---

## 🔒 Access Control

### Who Can See Settings?
- **OWNER Role**: ✅ Full access to all settings
- **STAFF Role**: ❌ No access (tab is hidden)

### How to Access
1. Login with an OWNER account (default: `admin` / `admin`)
2. The "Settings" tab will appear in the main menu
3. Click on Settings to access all configuration options

---

## 📋 Settings Categories

The Settings tab contains 7 sub-sections:

### 1. 👥 **Users**
Manage system user accounts.

**Features:**
- Add new users (OWNER or STAFF role)
- Edit existing users
- Delete users (with protection for last admin)
- View all users in a table
- Change usernames and passwords

**Use Cases:**
- Add new employees to the system
- Change staff passwords
- Promote staff to admin
- Remove terminated employees

**Security:**
- Cannot delete the last OWNER account
- Double-click table rows to edit
- All changes take effect immediately

---

### 2. 🔧 **System Config**
Configure application-wide settings.

**Settings Available:**

| Setting | Default | Description |
|---------|---------|-------------|
| Service Interval | 180 days | Days until next service reminder |
| Currency Symbol | Rs | Symbol shown on invoices |
| Auto-backup on Exit | Disabled | Automatic database backup |
| Theme Color | Blue | UI color scheme |
| Low Stock Alert | 5 units | Minimum stock before alert |

**Features:**
- Change service reminder intervals
- Customize currency for your region
- Enable/disable auto-backup
- Choose application theme
- Set inventory alert thresholds

**Important:**
- Some changes may require restart
- Settings are saved to database
- Affects all users system-wide

---

### 3. 🏪 **Garage Info**
Your business information for invoices and reports.

**Information Fields:**
- **Garage Name**: Your business name
- **Address**: Full business address
- **Phone**: Contact number
- **Email**: Business email
- **Tax ID / GST**: Tax registration number
- **Website**: Your website URL

**Usage:**
- This information appears on printed invoices
- Used in PDF invoice generation
- Shows on official documents
- Important for legal compliance

**Example Invoice Header:**
```
MY GARAGE SERVICE CENTER
123 Main Street, City, State - 12345
Phone: +1 234 567 8900 | Email: info@mygarage.com
GST: GST123456789
```

---

### 4. 👨‍🔧 **Mechanics**
Manage mechanic profiles.

**Features:**
- Add mechanics with name, phone, salary
- Set commission rates (percentage)
- Update mechanic information
- Delete mechanics
- View all mechanics in table

**Data Tracked:**
- Full name
- Contact phone number
- Monthly salary
- Commission percentage (for performance bonuses)

**Integration:**
- Mechanics appear in service assignment dropdown
- Used for service reports
- Tracks mechanic performance
- Calculates commission (future feature)

---

### 5. 🚚 **Suppliers**
Manage parts suppliers.

**Features:**
- Add supplier contacts
- Store contact information
- Track supplier addresses
- Email addresses for communication

**Data Fields:**
- Supplier name
- Contact phone
- Email address
- Physical address

**Usage:**
- Track where parts are purchased
- Quick access to supplier contacts
- Reorder management
- Supplier performance tracking

---

### 6. 💾 **Backup & Reset**
Data management and danger zone.

#### Backup Section
**Create Backup:**
- Manually create database backup
- Saves with timestamp
- Stored in same folder as database
- Format: `garage_complete_backup_YYYYMMDD_HHMMSS.db`

**When to Backup:**
- Before major changes
- End of month/year
- Before system updates
- Regular weekly/monthly schedule

#### Danger Zone ⚠️
**Individual Table Clearing:**
- Clear All Services
- Clear All Payments
- Clear All Expenses

**Complete Reset:**
- ☢️ RESET ENTIRE DATABASE
- Deletes ALL data
- Requires password confirmation
- **CANNOT BE UNDONE**

**Safety Features:**
- Multiple confirmation dialogs
- Password verification required
- Clear warnings
- Recommended to backup first

---

### 7. ℹ️ **About**
System information and statistics.

**Displays:**
- Version number
- Feature list
- Technical details
- System information
- Copyright info

**Actions Available:**
- **View System Stats**: Database statistics
  - Total customers
  - Total bikes
  - Services (completed/pending)
  - Parts count
  - User count
  
- **User Manual**: Quick reference guide

---

## 🎯 Common Admin Tasks

### Adding a New Employee
1. Go to Settings → Users
2. Fill in: Full Name, Username, Password
3. Select Role: STAFF (for regular employee) or OWNER (for admin)
4. Click "Add User"
5. New user can now login!

### Changing Your Garage Name
1. Go to Settings → Garage Info
2. Update "Garage Name" field
3. Update other fields as needed
4. Click "Save Garage Information"
5. New name will appear on invoices

### Creating a Backup
1. Go to Settings → Backup & Reset
2. Click "Create Backup Now"
3. Confirmation message shows filename
4. File saved in application folder
5. Store backup in safe location

### Adding a Mechanic
1. Go to Settings → Mechanics
2. Enter Name and Phone (required)
3. Enter Salary and Commission %
4. Click "Add"
5. Mechanic appears in service assignment dropdown

### Customizing Service Interval
1. Go to Settings → System Config
2. Change "Default Service Interval" days
3. Click "Save Configuration"
4. New bikes will use new interval

---

## 🔐 Security Best Practices

### Password Management
- ✅ Change default passwords immediately
- ✅ Use strong passwords (8+ characters)
- ✅ Don't share admin credentials
- ✅ Regularly update passwords
- ❌ Don't use "password123"

### User Management
- ✅ Only give OWNER role to trusted individuals
- ✅ Use STAFF role for regular employees
- ✅ Remove users when employees leave
- ✅ Audit users list periodically
- ❌ Don't create unnecessary admin accounts

### Backup Strategy
- ✅ Backup before major changes
- ✅ Keep multiple backup copies
- ✅ Store backups off-site (cloud/USB)
- ✅ Test backups periodically
- ✅ Automate weekly backups

---

## ⚡ Quick Reference

### Daily Tasks
- Monitor dashboard alerts
- Check low stock warnings
- Review pending services

### Weekly Tasks
- Create database backup
- Review user accounts
- Check mechanic assignments

### Monthly Tasks
- Review all settings
- Update garage information if changed
- Clean up old/test data
- Generate reports

### As Needed
- Add new users
- Update supplier contacts
- Add new mechanics
- Change system configuration

---

## 🆘 Troubleshooting

### Can't See Settings Tab
- **Solution**: Login with OWNER account, not STAFF

### Changes Not Saving
- **Solution**: Check file permissions, restart application

### Forgot Admin Password
- **Solution**: Edit database directly or create new admin user via SQLite

### Backup Failed
- **Solution**: Check disk space, verify write permissions

### Can't Delete User
- **Solution**: Can't delete last OWNER account (by design)

---

## 📝 Notes

- All settings changes are saved immediately to database
- Some changes may require application restart
- Settings affect all users system-wide
- STAFF users cannot see or change settings
- Keep track of changes for audit purposes

---

**Remember**: With great power comes great responsibility! LOVE OPH
Settings changes affect the entire system. Always backup before major changes.
