# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) Fidobe Solutions LLC.
#
#    For Module Support : dev3@fidobe.com
#
#############################################################################
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class MrpBom(models.Model):
    _inherit = 'mrp.bom'

    is_mrp_manager = fields.Boolean(compute='_compute_is_mrp_manager')
    def _compute_is_mrp_manager(self):
        for record in self:
            record.is_mrp_manager = self.env.user.has_group('mrp.group_mrp_manager')

    def default_get(self, fields):
        res = super().default_get(fields)
        res['company_id'] = False
        res['type'] = 'phantom'
        return res

    # def calculate_percentage(self):
    #     total_per = 1
    #     bom_line = len(self.bom_line_ids)
    #     empty_line = self.env['mrp.bom.line']
    #     for line in self.bom_line_ids:
    #         if line.percentage:
    #             total_per -= line.percentage
    #             bom_line -= 1
    #         else:
    #             empty_line |= line
    #     if bom_line:
    #         empty_line.write({"percentage": total_per/bom_line})
    #
    # def check_percentage(self):
    #     for bom in self:
    #         total_pr = sum(bom.bom_line_ids.mapped('percentage'))
    #         if total_pr > 1:
    #             raise UserError(_("Total percentage should not be more then 100%"))
    #
    # @api.model
    # def create(self, vals):
    #     res = super(MrpBom, self).create(vals)
    #     if res.type == "phantom":
    #         res.check_percentage()
    #     return res
    #
    # def write(self, vals):
    #     res = super(MrpBom, self).write(vals)
    #     for bom in self.filtered(lambda b: b.type == 'phantom'):
    #         bom.check_percentage()
    #     return res
