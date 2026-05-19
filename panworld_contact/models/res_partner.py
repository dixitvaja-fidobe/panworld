# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) Fidobe Solutions LLC.
#
#    For Module Support : dev3@fidobe.com
#
##############################################################################
from odoo import fields, models, api

class ResPartner(models.Model):
    _inherit = "res.partner"

    acc_no = fields.Char(string="Acc Number", readonly=True, copy=False)
    division_type_id = fields.Many2one('division.type', string="Division Type")
    purchase_account_number = fields.Char(
        string="Purchase Account Number",
        company_dependent=True,
        help="Purchase Account Number")

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            # Use company_type check as fallback if is_company is missing (common in UI)
            if vals.get('is_company') or vals.get('company_type') == 'company':
                vals['acc_no'] = self.env['ir.sequence'].next_by_code('panworld.contact.acc_no') or 'New'
        
        return super(ResPartner, self).create(vals_list)

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        args = args or []
        domain = []
        if name:
            domain = ['|', ('acc_no', operator, name), ('name', operator, name)]
        acc_no_recs = self.search([('acc_no', operator, name)] + args, limit=limit)
        res = super(ResPartner, self).name_search(name, args, operator, limit)
        if acc_no_recs:
            # Map existing results to IDs for quick lookup
            existing_ids = {r[0] for r in res}
            # Usually exact matches or specific field matches are good to be at top.
            new_res = []
            for rec in acc_no_recs:
                if rec.id not in existing_ids:
                    new_res.append((rec.id, rec.display_name))
                    existing_ids.add(rec.id)
            # If we want acc_no matches first:
            res = new_res + res
        return res[:limit]
