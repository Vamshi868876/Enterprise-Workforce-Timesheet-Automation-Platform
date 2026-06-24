import xmlrpc.client
import os

url = os.environ.get("ODOO_URL", "http://84.247.136.24:8069")
db = os.environ.get("ODOO_DB", "mydb")
username = os.environ.get("ODOO_USERNAME", "admin")
password = os.environ.get("ODOO_PASSWORD", "79NM46eRqDv)w^q^")

common = xmlrpc.client.ServerProxy('{}/xmlrpc/2/common'.format(url))
uid = common.authenticate(db, username, password, {})
models = xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format(url))

lines = models.execute_kw(db, uid, password, 'account.analytic.line', 'search_read', 
    [[('name', 'ilike', 'Timesheet from')]], 
    {'fields': ['id', 'name', 'date', 'unit_amount', 'employee_id', 'project_id', 'account_id', 'company_id'], 'limit': 5, 'order': 'id desc'}
)

print("Recent lines:", lines)
