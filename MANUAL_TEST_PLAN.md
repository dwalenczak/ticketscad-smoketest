# TicketsCAD Manual Test Plan

This document covers test scenarios that require human judgment,
visual verification, or interaction with external services that
cannot be reliably automated.

---

## 1. Visual / UI Tests

### 1.1 Map Tile Quality
- [ ] Open a ticket from the Situation screen
- [ ] Click the Map button in the popup menu
- [ ] Verify map tiles load at correct zoom level (not blurry)
- [ ] Verify tiles load on FIRST open (no F5 needed)
- [ ] Zoom in and out — tiles should stay crisp at each zoom level
- [ ] Close and reopen the map — should load correctly again

### 1.2 Day/Night Mode
- [ ] Click "Day" button in header — verify light theme applies
- [ ] Click "Night" button — verify dark theme applies
- [ ] Navigate between pages — theme should persist

### 1.3 Responsive Layout
- [ ] Resize browser window to various widths
- [ ] Verify content adapts without horizontal scrollbars
- [ ] Test at 1024x768, 1280x800, 1920x1080

### 1.4 Print Layout
- [ ] From a ticket, click Print
- [ ] Verify print preview shows all ticket data
- [ ] Verify map prints correctly

---

## 2. User Level Access Tests

### 2.1 Admin User
- [ ] Login as admin (password: testing)
- [ ] Verify ALL tabs visible: Situation, New, Units, Fac's, Search, Reports, Config, Help, Log, Full scr, Personnel, Links, Board, Mobile
- [ ] Verify can access Config page
- [ ] Verify can create/edit/close tickets
- [ ] Verify can create/edit units
- [ ] Verify can manage personnel

### 2.2 Guest User
- [ ] Login as guest (password: guest)
- [ ] Verify ONLY these tabs: Situation, New, Units, Fac's, Search, Help, Full scr
- [ ] Verify NO access to: Reports, Config, Log, Personnel, Links, Board, Mobile, Msgs
- [ ] Verify can view tickets but NOT modify sensitive settings

### 2.3 Unit Level User
- [ ] Create a unit-level user via Config > User Administration
- [ ] Login as that user
- [ ] Verify redirected to Mobile view (not main frameset)
- [ ] Verify can update own unit status
- [ ] Verify cannot access admin functions

### 2.4 Facility Level User
- [ ] Create a facility-level user
- [ ] Login as that user
- [ ] Verify redirected to Facility Board
- [ ] Verify can see incidents near their facility
- [ ] Verify cannot access admin functions

### 2.5 Member Level User
- [ ] Create a member-level user
- [ ] Login — verify session is created then immediately destroyed (logout redirect)
- [ ] This is by design for the MDB (Member Database) access

### 2.6 Service User (Portal)
- [ ] Create a service-level user
- [ ] Login — verify redirected to Portal view
- [ ] Verify can submit service requests
- [ ] Verify cannot access main CAD interface

---

## 3. Full Workflow Tests

### 3.1 Create and Dispatch Workflow
1. [ ] Login as admin
2. [ ] Click "New" tab to create a ticket
3. [ ] Fill in: Nature, Priority, Location, City, State
4. [ ] Click Submit — verify ticket is created
5. [ ] From Situation screen, click on the new ticket
6. [ ] Click "Dispatch" from popup menu
7. [ ] Verify dispatch page shows available units
8. [ ] Check the checkbox next to a unit
9. [ ] Click "Mail Dir" to dispatch
10. [ ] Verify unit status changes to dispatched
11. [ ] Go to Units tab — verify unit shows assigned to ticket
12. [ ] Close the ticket — verify unit status returns to available

### 3.2 Patient Record Workflow
1. [ ] Open an existing ticket
2. [ ] Click "+ Patient" in toolbar
3. [ ] Fill in: Patient ID, Name, DOB, Gender, Insurance
4. [ ] Click Next/Submit
5. [ ] Verify patient record is saved
6. [ ] Reopen ticket — verify patient data persists

### 3.3 Search Workflow
1. [ ] Click Search tab
2. [ ] Search by Description for "test"
3. [ ] Verify results appear
4. [ ] Change "Search In" dropdown to each option
5. [ ] Verify each search type returns results or empty message
6. [ ] Change sort order — verify results reorder

### 3.4 Report Generation
1. [ ] Click Reports tab
2. [ ] Select each report type one at a time
3. [ ] Verify each report generates without errors
4. [ ] Check that date range filtering works
5. [ ] Verify report data matches expected ticket data

---

## 4. Configuration Tests

### 4.1 Call Natures / Types
- [ ] Config > Natures: Add a new nature, verify it appears in the New ticket dropdown
- [ ] Edit the nature name, verify change persists
- [ ] Delete/deactivate the nature, verify it no longer appears

### 4.2 Unit Types
- [ ] Config > Unit Types: Add a new unit type
- [ ] Create a unit with that type
- [ ] Verify unit appears with correct type on Units page

### 4.3 Organizations
- [ ] Config > Organizations: Add a new organization
- [ ] Assign a unit to that organization
- [ ] Verify organization appears in reports/filters

### 4.4 Regions
- [ ] Config > Regions: Add a new region
- [ ] Assign geographic boundaries
- [ ] Verify region appears in filters

### 4.5 Insurance Types (if applicable)
- [ ] Config > Insurance: Add insurance type
- [ ] Verify appears in patient form dropdown

---

## 5. Personnel Module Tests

### 5.1 Personnel Records
- [ ] Navigate to Personnel tab
- [ ] Create a new personnel record with: name, rank, organization
- [ ] Verify record appears in personnel list
- [ ] Edit the record — verify changes save

### 5.2 Photo ID
- [ ] Add a photo to a personnel record
- [ ] Verify photo displays on the personnel card
- [ ] Verify photo appears in printed reports

### 5.3 Equipment
- [ ] Config > Equipment Types: Add equipment types
- [ ] Assign equipment to a personnel record
- [ ] Verify equipment shows on personnel detail

### 5.4 Teams
- [ ] Config > Teams: Create a team
- [ ] Assign personnel to the team
- [ ] Verify team membership displays correctly

### 5.5 Clothing Types
- [ ] Config > Clothing: Add clothing types/sizes
- [ ] Assign to personnel records
- [ ] Verify in personnel detail view

### 5.6 Vehicles
- [ ] Config > Vehicles: Add vehicle records
- [ ] Assign vehicles to units or personnel
- [ ] Verify vehicle info appears correctly

### 5.7 Events
- [ ] Create an event (training, exercise, etc.)
- [ ] Assign personnel to the event
- [ ] Verify attendance records

---

## 6. Email / Notification Tests

### 6.1 Email Notifications
- [ ] Configure SMTP settings in Config
- [ ] Create a ticket with notification enabled
- [ ] Verify email is sent (check mail server logs)
- [ ] Test "Contact Units" email from edit toolbar
- [ ] Test "Notify" function

### 6.2 Messaging
- [ ] Enable messaging in Config
- [ ] Send a message between users
- [ ] Verify message appears in recipient's queue
- [ ] Test "Show Messages" on dispatch page

---

## 7. Security Tests (Manual)

### 7.1 Session Timeout
- [ ] Login, then wait for session expiry (configurable timeout)
- [ ] Verify next action prompts re-login
- [ ] Verify session data is cleared

### 7.2 Concurrent Sessions
- [ ] Login as same user from two browsers
- [ ] Verify behavior (should warn about duplicate session)

### 7.3 URL Manipulation
- [ ] Try accessing pages with modified ticket_id parameters
- [ ] Try accessing other users' data via URL parameters
- [ ] Verify proper authorization checks

---

## 8. Database Upgrade Test

### 8.1 Version Mismatch
1. [ ] Manually set `_version` in settings table to an older version
2. [ ] Login as admin
3. [ ] Verify redirect to install.php for upgrade
4. [ ] Run the Upgrade option
5. [ ] Verify all tables updated correctly
6. [ ] Verify login works normally afterward

### 8.2 Fresh Install
1. [ ] Drop all tables
2. [ ] Navigate to index.php
3. [ ] Verify redirect to install.php
4. [ ] Run Install/Reinstall
5. [ ] Verify all tables created
6. [ ] Login with created admin credentials

---

## Test Environment Requirements

- Windows 10/11 with XAMPP (PHP 8.0+, Apache, MariaDB)
- Edge, Chrome, or Firefox browser
- Test database with sample data (at least 1 unit, 1 facility, 5 tickets)
- SMTP server or mail log access for notification tests

## Running Automated Tests Alongside

```bash
# Run full automated suite first
python -m pytest --headless

# Then work through manual tests above
# Mark each checkbox as you complete it
```

---

*Last updated: 2026-03-15*
*This document should be updated as new features are added.*
