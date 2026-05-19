from odoo import fields, models

class ResCompany(models.Model):
    _inherit = 'res.company'

    is_presale_restricted = fields.Boolean(
        string='Is Presale Restricted',
        default=True,
        help="If checked, manual creation of Sale Orders and Purchase Orders will be restricted to the Presale Tracking flow."
    )
