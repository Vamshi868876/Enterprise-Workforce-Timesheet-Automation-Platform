import xmlrpc.client
import os

url = os.environ.get("ODOO_URL", "http://84.247.136.24:8069")
db = os.environ.get("ODOO_DB", "mydb")
username = os.environ.get("ODOO_USERNAME", "admin")
password = os.environ.get("ODOO_PASSWORD", "79NM46eRqDv)w^q^")

def get_connection():
    common = xmlrpc.client.ServerProxy('{}/xmlrpc/2/common'.format(url))
    uid = common.authenticate(db, username, password, {})
    if not uid:
        raise Exception("Authentication to Odoo failed. Please check credentials.")
    models = xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format(url))
    return uid, models

def get_employees():
    uid, models = get_connection()
    employees = models.execute_kw(db, uid, password, 'hr.employee', 'search_read', [[]], {'fields': ['id', 'name']})
    return employees

def get_projects():
    uid, models = get_connection()
    projects = models.execute_kw(db, uid, password, 'project.project', 'search_read', [[]], {'fields': ['id', 'name']})
    return projects

def push_timesheet_to_odoo(employee_id, project_id, task_id, entries):
    """
    Push a single aggregated timesheet entry to Odoo via XML-RPC.
    """
    if not entries:
        return False
        
    uid, models = get_connection()
    
    total_hours = sum(float(entry.get('hours', 0)) for entry in entries)
    
    if total_hours <= 0:
        return False
        
    dates = sorted([entry['date'] for entry in entries])
    from_date = dates[0]
    to_date = dates[-1]
    
    description = f"Timesheet from {from_date} to {to_date}"
    
    models.execute_kw(db, uid, password, 'account.analytic.line', 'create', [{
        'name': description,
        'project_id': project_id,
        'task_id': task_id if task_id else False,
        'date': to_date,
        'unit_amount': total_hours,
        'employee_id': employee_id,
    }])
    return True
