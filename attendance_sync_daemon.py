import xmlrpc.client
import os
import sys
import time
import logging
from datetime import date, datetime
from dateutil.relativedelta import relativedelta
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

load_dotenv()

url = os.environ.get("ODOO_URL", "http://84.247.136.24:8069")
db = os.environ.get("ODOO_DB", "mydb")
username = os.environ.get("ODOO_USERNAME", "admin")
password = os.environ.get("ODOO_PASSWORD", "79NM46eRqDv)w^q^")

def sync_timesheets(force_all=False):
    logging.info("Connecting to Odoo API...")
    common = xmlrpc.client.ServerProxy('{}/xmlrpc/2/common'.format(url))
    try:
        uid = common.authenticate(db, username, password, {})
    except Exception as e:
        logging.error(f"Failed to connect to Odoo: {e}")
        return
        
    if not uid:
        logging.error("Authentication failed. Check credentials.")
        return
    
    models = xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format(url))
    
    today = date.today()
    first_day_current_month = today.replace(day=1)
    
    domain = [
        ('check_out', '!=', False),
        ('x_is_timesheet_processed', '=', False)
    ]
    
    if force_all:
        logging.info("MANUAL OVERRIDE: Scanning ALL unprocessed attendances (including current month)...")
    else:
        logging.info(f"Scanning for unprocessed attendances strictly prior to {first_day_current_month}...")
        domain.append(('check_in', '<', first_day_current_month.strftime('%Y-%m-%d 00:00:00')))
    
    attendances = models.execute_kw(db, uid, password, 'hr.attendance', 'search_read', 
        [domain],
        {'fields': ['id', 'employee_id', 'check_in', 'check_out', 'x_break_start', 'x_break_end']}
    )
    
    if not attendances:
        logging.info("No unprocessed attendances found for previous months! Everything is up to date.")
        return

    # Group by Employee and Month
    grouped = {}
    for att in attendances:
        emp_id = att['employee_id'][0]
        emp_name = att['employee_id'][1]
        
        check_in = datetime.strptime(att['check_in'], '%Y-%m-%d %H:%M:%S')
        check_out = datetime.strptime(att['check_out'], '%Y-%m-%d %H:%M:%S')
        
        delta_sec = (check_out - check_in).total_seconds()
        
        break_sec = 0
        if att.get('x_break_start') and att.get('x_break_end'):
            b_start = datetime.strptime(att['x_break_start'], '%Y-%m-%d %H:%M:%S')
            b_end = datetime.strptime(att['x_break_end'], '%Y-%m-%d %H:%M:%S')
            if b_end > b_start:
                break_sec = (b_end - b_start).total_seconds()
                
        real_hours = max(0, (delta_sec - break_sec) / 3600.0)
        month_key = check_in.strftime('%Y-%m') # e.g. "2026-05"
        
        key = (emp_id, month_key)
        if key not in grouped:
            grouped[key] = {'emp_name': emp_name, 'total_hours': 0, 'total_break': 0, 'att_ids': []}
        
        grouped[key]['total_hours'] += real_hours
        grouped[key]['total_break'] += (break_sec / 3600.0)
        grouped[key]['att_ids'].append(att['id'])
        
    for (emp_id, month_key), data in grouped.items():
        logging.info(f"Processing {data['emp_name']} for {month_key} -> Total: {round(data['total_hours'], 2)} hours (Break: {round(data['total_break'], 2)} h)")
        
        # Fetch Employee's default project
        emp_records = models.execute_kw(db, uid, password, 'hr.employee', 'read', [[emp_id]], {'fields': ['x_default_project_id']})
        if not emp_records or not emp_records[0].get('x_default_project_id'):
            logging.warning(f"Skipping {data['emp_name']} - No Default Project assigned in Odoo!")
            continue
            
        project_id = emp_records[0]['x_default_project_id'][0]
        
        # Calculate last day of that specific month
        year, month = map(int, month_key.split('-'))
        if month == 12:
            next_month = date(year+1, 1, 1)
        else:
            next_month = date(year, month+1, 1)
        last_day = next_month - relativedelta(days=1)
        
        # Create single Timesheet record
        description = f"Attendance for {month_key} (Total Break: {round(data['total_break'], 2)} hrs)"
        models.execute_kw(db, uid, password, 'account.analytic.line', 'create', [{
            'name': description,
            'project_id': project_id,
            'date': last_day.strftime('%Y-%m-%d'),
            'unit_amount': data['total_hours'],
            'employee_id': emp_id,
        }])
        
        # Mark attendances as processed to prevent duplicates
        models.execute_kw(db, uid, password, 'hr.attendance', 'write', [data['att_ids'], {
            'x_is_timesheet_processed': True
        }])
        logging.info(f"SUCCESS: Created timesheet and locked {len(data['att_ids'])} attendances for {data['emp_name']}.")

if __name__ == "__main__":
    if '--run-now' in sys.argv:
        logging.info("Running manual sync...")
        sync_timesheets(force_all=True)
    else:
        logging.info("Background Daemon started. Checking once every 24 hours...")
        while True:
            sync_timesheets()
            time.sleep(86400) # Sleep for 24 hours
