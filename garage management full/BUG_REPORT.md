# Bug Report - Garage Management System

## Issues Found During Code Audit

### 1. Bare Except Clauses (3 instances)
**Location:** Lines 126, 141, 1598
**Issue:** Using bare `except:` clauses catches ALL exceptions including SystemExit and KeyboardInterrupt
**Severity:** Medium
**Fix:** Replace with `except Exception:` to catch only regular exceptions

### 2. Potential None Access on fetchone() Results (Multiple instances)
**Locations:** Lines 79, 97, 102, 361-383, 828, 1024, 1449, 2687, 2850-2851, 3625-3633
**Issue:** Directly accessing `[0]` on fetchone() result without checking if it's None
**Severity:** High - Can cause AttributeError crashes
**Fix:** Add None checks before accessing index [0]

### 3. Files Opened Without Context Manager (3 instances)
**Locations:** Lines 196, 3096, 3149
**Issue:** Using `Image.open()` without proper context management
**Severity:** Low-Medium - Resource leak potential
**Fix:** While PIL handles this internally, better to be explicit

### 4. SQL Injection Risk (2 instances)
**Locations:** Lines 3519, 3539
**Issue:** Using f-strings for table names in DELETE statements
**Severity:** Medium - Limited risk as table_name is controlled, but still bad practice
**Fix:** Validate table names against whitelist

### 5. Missing Error Handling in reset_database()
**Location:** Line 3532-3533
**Issue:** If fetchone returns None, accessing [0] will crash
**Severity:** High - Critical function can crash
**Fix:** Add None check before accessing password

## Summary
- **High Severity:** 2 issues (None access, reset_database crash)
- **Medium Severity:** 2 issues (bare except, SQL injection pattern)
- **Low Severity:** 1 issue (file handling)

## Recommended Fixes
All issues have been fixed in the updated code.
