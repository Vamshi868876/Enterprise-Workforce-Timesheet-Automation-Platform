from odoo import models, fields

class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    default_project_id = fields.Many2one('project.project', string="Default Project", help="Project to which attendance timesheets will be logged automatically at the end of the month.")
