{
    'name': 'Timesheet Automation via Attendance',
    'version': '1.0',
    'category': 'Human Resources/Timesheets',
    'summary': 'Automated monthly timesheet generation from native attendances with break tracking',
    'depends': ['base', 'hr', 'hr_attendance', 'hr_timesheet', 'project'],
    'data': [
        'views/hr_employee_views.xml',
        'views/hr_attendance_views.xml',
        'data/cron.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
