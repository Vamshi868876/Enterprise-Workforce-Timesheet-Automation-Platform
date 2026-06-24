from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import date

class EmployeeMonthlyTimesheetLine(models.Model):
    _name = 'employee.monthly.timesheet.line'
    _description = 'Monthly Timesheet Line'
    _order = 'date asc'

    timesheet_id = fields.Many2one('employee.monthly.timesheet', string='Timesheet Reference', required=True, ondelete='cascade')
    date = fields.Date(string='Date', required=True)
    project_id = fields.Many2one('project.project', string='Project')
    task_id = fields.Many2one('project.task', string='Task', domain="[('project_id', '=', project_id)]")
    description = fields.Char(string='Work Description')
    hours = fields.Float(string='Hours Worked', default=0.0)

    @api.constrains('date', 'timesheet_id')
    def _check_date(self):
        for line in self:
            if line.date and line.timesheet_id:
                # Check if future date
                if line.date > date.today():
                    raise ValidationError(_("You cannot enter timesheets for future dates. (Date: %s)") % line.date)
                
                # Check if date belongs to the timesheet's month and year
                if line.date.month != int(line.timesheet_id.month) or line.date.year != line.timesheet_id.year:
                    raise ValidationError(_("The date %s does not belong to the timesheet's month and year.") % line.date)

    @api.constrains('hours')
    def _check_hours(self):
        for line in self:
            if line.hours < 0:
                raise ValidationError(_("Hours worked cannot be negative."))
            if line.hours > 24:
                raise ValidationError(_("Hours worked cannot exceed 24 hours per day. (Date: %s)") % line.date)
