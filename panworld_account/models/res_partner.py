# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) Fidobe Solutions LLC.
#
#    For Module Support : dev3@fidobe.com
#
##############################################################################
from odoo import fields, models, _


class ResPartner(models.Model):
    _inherit = "res.partner"

    journal_id = fields.Many2one('account.journal', string='Sales Journal',
        domain=[('type', '=', 'sale')], company_dependent=True)
    responsible_user = fields.Many2one('res.users', string="Responsible")
    vendor_responsible_user = fields.Many2one('res.users', string='Vendor Responsible')
    def_expense_count = fields.Integer(string="Deferred Expense Count", compute='_compute_def_expense_count')
    allow_ar_ap = fields.Boolean(string="Allow AR and AP")

    def _compute_def_expense_count(self):
        """Compute method for the partner's expenses count"""
        for partner in self:
            partner.def_expense_count = self.env['account.asset'].search_count([
                ('partner_id', '=', partner.id)
            ])

    def action_show_def_expenses(self):
        """Open the list/from view of the expenses made for the partner"""
        self.ensure_one()
        assets = self.env['account.asset'].search([
            ('partner_id', '=', self.id)
        ])
        result = {
            "type": "ir.actions.act_window",
            "res_model": "account.asset",
            "domain": [['id', 'in', assets.ids]],
            "name": _("Deferred Expenses"),
            "context": {'default_partner_id': self.id},
            'view_mode': 'tree,form',
        }
        if len(assets) == 1:
            result['view_mode'] = 'form'
            result['res_id'] = assets.id
        return result
