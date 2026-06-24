from odoo import models, fields, api
from dateutil.relativedelta import relativedelta
from datetime import date, datetime, timedelta
import logging

_logger = logging.getLogger(__name__)

class HrAttendance(models.Model):
    _inherit = 'hr.attendance'

    break_start = fields.Datetime(string="Break Start")
    break_end = fields.Datetime(string="Break End")
    is_timesheet_processed = fields.Boolean(string="Timesheet Processed", default=False, readonly=True, help="Checked automatically when this record is added to a monthly timesheet.")

    is_break_started = fields.Boolean(string="Take Break")
    is_break_ended = fields.Boolean(string="Back from Break")

    @api.onchange('is_break_started')
    def _onchange_is_break_started(self):
        if self.is_break_started and not self.break_start:
            self.break_start = fields.Datetime.now()

    @api.onchange('is_break_ended')
    def _onchange_is_break_ended(self):
        if self.is_break_ended and not self.break_end:
            self.break_end = fields.Datetime.now()

    @api.depends('check_in', 'check_out', 'break_start', 'break_end')
    def _compute_worked_hours(self):
        for attendance in self:
            if attendance.check_out and attendance.check_in:
                delta = attendance.check_out - attendance.check_in
                break_delta = timedelta()
                
                # Subtract break time if valid break fields exist
                if attendance.break_start and attendance.break_end and attendance.break_end > attendance.break_start:
                    break_delta = attendance.break_end - attendance.break_start
                
                total_seconds = delta.total_seconds() - break_delta.total_seconds()
                attendance.worked_hours = max(0.0, total_seconds / 3600.0)
            else:
                attendance.worked_hours = False

    @api.model
    def _cron_sync_monthly_attendance(self):
        """
        Runs on the 1st of every month to gather previous month's attendances 
        and generate exactly ONE account.analytic.line (timesheet) per employee.
        """
        today = date.today()
        # Find the first and last day of the previous month
        first_day_prev_month = (today.replace(day=1) - relativedelta(months=1))
        last_day_prev_month = today.replace(day=1) - relativedelta(days=1)

        # Get unprocessed attendances from the previous month
        attendances = self.search([
            ('check_in', '>=', datetime.combine(first_day_prev_month, datetime.min.time())),
            ('check_in', '<=', datetime.combine(last_day_prev_month, datetime.max.time())),
            ('is_timesheet_processed', '=', False),
            ('check_out', '!=', False)
        ])

        if not attendances:
            _logger.info("No unprocessed attendances found for the previous month.")
            return

        # Group by employee
        grouped_attendances = {}
        for att in attendances:
            emp = att.employee_id
            if emp not in grouped_attendances:
                grouped_attendances[emp] = self.env['hr.attendance']
            grouped_attendances[emp] |= att

        analytic_line_obj = self.env['account.analytic.line']

        for employee, att_records in grouped_attendances.items():
            if not employee.default_project_id:
                _logger.warning(f"Employee {employee.name} has no Default Project set. Skipping timesheet creation.")
                continue

            total_hours = sum(att_records.mapped('worked_hours'))
            
            if total_hours > 0:
                description = f"Attendance from {first_day_prev_month.strftime('%Y-%m-%d')} to {last_day_prev_month.strftime('%Y-%m-%d')}"
                
                analytic_line_obj.create({
                    'name': description,
                    'project_id': employee.default_project_id.id,
                    'date': last_day_prev_month,
                    'unit_amount': total_hours,
                    'employee_id': employee.id,
                    'company_id': employee.company_id.id or self.env.company.id,
                })

                # Mark as processed
                att_records.write({'is_timesheet_processed': True})
                _logger.info(f"Created timesheet for {employee.name} with {total_hours} hours.")
