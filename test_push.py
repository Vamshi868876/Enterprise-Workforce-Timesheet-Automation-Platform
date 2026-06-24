from odoo_client import push_timesheet_to_odoo

try:
    res = push_timesheet_to_odoo(1, 1, False, [{'date': '2026-06-01', 'hours': '8'}])
    print("Success:", res)
except Exception as e:
    print("Error:", e)
