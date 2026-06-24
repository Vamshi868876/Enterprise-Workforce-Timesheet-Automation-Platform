# Odoo Timesheet Automation Architecture

## About The Project

This project provides a robust, fully-automated Attendance and Timesheet synchronization system built for the Odoo ERP environment. It eliminates the need for manual timesheet entries by capturing real-time employee attendance events (Check-in, Take Break, Back from Break, Check-out) and utilizing a background synchronization daemon to calculate real worked hours and automatically generate locked Analytic Timesheets.

## Key Topics & Technologies
- **Odoo XML-RPC API**: Seamless integration with Odoo's backend to execute automated record updates.
- **Background Daemon Processing**: A continuous Python loop script (`attendance_sync_daemon.py`) that synchronizes and batches data every 24 hours (or via `--run-now` flag).
- **Time Calculations**: Accurate tracking of exact break durations, subtracting them from total shift time to determine pure worked hours.
- **Flask REST API**: Backend server interface (`app.py`) providing lightweight endpoints for external integrations.
- **Environment Security**: Usage of `.env` configuration for safe handling of API credentials and database connection strings.

## Architecture & Workflow

1. **Employee Interface (Odoo UI / Kiosk Mode)**:
   - Employees check in/out via standard Odoo buttons or Kiosk mode to capture the exact system timestamp.
   - For breaks, custom automation UI rules capture the real-time exact system clock, preventing manual data tampering.

2. **Data Aggregation**:
   - The Attendance Sync Daemon connects to the Odoo backend using `xmlrpc.client`.
   - It fetches all raw attendance records for a given month that have not yet been marked as `x_is_timesheet_processed`.

3. **Timesheet Processing Engine**:
   - Computes Total Shift Hours (`check_out` - `check_in`).
   - Computes Total Break Hours (`x_break_end` - `x_break_start`).
   - Calculates **Net Worked Hours**.
   - Generates a consolidated `account.analytic.line` timesheet entry for the employee for that specific month, mapped to their default project.
   - Flags the raw attendance lines as processed (`x_is_timesheet_processed = True`) to ensure idempotency and prevent duplicate billing.

## How to Run

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure Environment**:
   Ensure your `.env` file is properly configured with your Odoo server URL, Database name, Username, and Password.

3. **Run the Daemon**:
   - To run a manual, immediate synchronization of all records:
     ```bash
     python attendance_sync_daemon.py --run-now
     ```
   - To run as a continuous background daemon (checks every 24 hours):
     ```bash
     python attendance_sync_daemon.py
     ```

4. **Run the API Server (Optional)**:
   ```bash
   python app.py
   ```
