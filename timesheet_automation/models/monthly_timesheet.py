from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
import calendar
from datetime import date, datetime

class EmployeeMonthlyTimesheet(models.Model):
    _name = 'employee.monthly.timesheet'
    _description = 'Monthly Timesheet'
    _order = 'year desc, month desc'

    name = fields.Char(string='Name', compute='_compute_name', store=True)
    employee_id = fields.Many2one('hr.employee', string='Employee', required=True, default=lambda self: self.env.user.employee_id)
    department_id = fields.Many2one('hr.department', string='Department', related='employee_id.department_id', store=True)
    month = fields.Selection([
        ('1', 'January'), ('2', 'February'), ('3', 'March'),
        ('4', 'April'), ('5', 'May'), ('6', 'June'),
        ('7', 'July'), ('8', 'August'), ('9', 'September'),
        ('10', 'October'), ('11', 'November'), ('12', 'December')
    ], string='Month', required=True, default=lambda self: str(date.today().month))
    year = fields.Integer(string='Year', required=True, default=lambda self: date.today().year)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('submitted', 'Waiting Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected')
    ], string='Status', default='draft', tracking=True)
    
    line_ids = fields.One2many('employee.monthly.timesheet.line', 'timesheet_id', string='Timesheet Lines')
    total_hours = fields.Float(string='Total Hours', compute='_compute_total_hours', store=True)

    _sql_constraints = [
        ('unique_employee_month_year', 'UNIQUE(employee_id, month, year)', 'A timesheet for this month and year already exists for this employee!')
    ]

    @api.depends('employee_id', 'month', 'year')
    def _compute_name(self):
        for record in self:
            if record.employee_id and record.month and record.year:
                month_name = dict(self._fields['month'].selection).get(record.month)
                record.name = f"{record.employee_id.name} - {month_name} {record.year}"
            else:
                record.name = 'New'

    @api.depends('line_ids.hours')
    def _compute_total_hours(self):
        for record in self:
            record.total_hours = sum(line.hours for line in record.line_ids)

    def action_generate_days(self):
        for record in self:
            if record.state != 'draft':
                raise UserError(_('You can only generate days in draft state.'))
            
            # Clear existing lines first
            record.line_ids.unlink()

            month = int(record.month)
            year = record.year
            num_days = calendar.monthrange(year, month)[1]

            lines_to_create = []
            for day in range(1, num_days + 1):
                lines_to_create.append((0, 0, {
                    'date': date(year, month, day),
                    'hours': 0.0,
                }))
            
            record.write({'line_ids': lines_to_create})

    def action_submit(self):
        for record in self:
            if not record.line_ids:
                raise UserError(_('Please generate days and enter timesheet hours before submitting.'))
            record.state = 'submitted'

    def action_approve(self):
        analytic_line_obj = self.env['account.analytic.line']
        for record in self:
            for line in record.line_ids:
                if line.hours > 0:
                    if not line.project_id:
                        raise UserError(_('Project is required for lines with hours > 0 (Date: %s).') % line.date)
                    
                    # Create standard Odoo timesheet record
                    analytic_line_obj.create({
                        'name': line.description or '/',
                        'project_id': line.project_id.id,
                        'task_id': line.task_id.id if line.task_id else False,
                        'date': line.date,
                        'unit_amount': line.hours,
                        'employee_id': record.employee_id.id,
                        'company_id': record.employee_id.company_id.id or self.env.company.id,
                    })
            record.state = 'approved'

    def action_reject(self):
        for record in self:
            record.state = 'rejected'
            
    def action_set_to_draft(self):
        for record in self:
            record.state = 'draft'
