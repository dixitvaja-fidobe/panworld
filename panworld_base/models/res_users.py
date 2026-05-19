# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) Fidobe Solutions LLC.
#
#    For Module Support : dev3@fidobe.com
#
#############################################################################
from odoo import fields, models, api


class ResUsers(models.Model):
    _inherit = "res.users"

    visible_menu_ids = fields.Many2many('ir.ui.menu', string='Visible Menus')

    @api.model_create_multi
    def create(self, vals_list):
        for values in vals_list:
            if 'visible_menu_ids' in values:
                self.env.registry.clear_cache()
        return super(ResUsers, self).create(vals_list)

    def write(self, values):
        res = super(ResUsers, self).write(values)
        if 'visible_menu_ids' in values:
            self.env.registry.clear_cache()
        return res


# class IrUiMenu(models.Model):
#     _inherit = "ir.ui.menu"
#
#     @api.model
#     def _search(self, args, offset=0, limit=None, order=None,):
#         if self.env.user.visible_menu_ids:
#             args.append(('id', 'in', self.env.user.visible_menu_ids.ids))
#         return super(IrUiMenu, self)._search(args, offset=0, limit=None, order=order)
