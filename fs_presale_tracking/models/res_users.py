from odoo import api, models, fields

class ResUsers(models.Model):
    _inherit = 'res.users'

    sample_so_company_ids = fields.Many2many(
        'res.company',
        'res_users_sample_so_company_rel',
        'user_id',
        'company_id',
        string='Allowed Companies for Sample SOs',
        help='Companies in which this user is allowed to create Sample Sale Orders.'
    )

    is_sample_so_user = fields.Boolean(compute='_compute_is_sample_so_user')

    def _compute_is_sample_so_user(self):
        sample_so_group = self.env.ref('fs_presale_tracking.group_sample_so_user', raise_if_not_found=False)
        for user in self:
            user.is_sample_so_user = sample_so_group in user.group_ids if sample_so_group else False
