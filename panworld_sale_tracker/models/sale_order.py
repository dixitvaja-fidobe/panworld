# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) Fidobe Solutions LLC.
#
#    For Module Support : dev3@fidobe.com
#
#############################################################################
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class SaleOrder(models.Model):
    _inherit = "sale.order"


    def _trigger_sale_tat_breached_so(self):
        template_id = self.env.ref('panworld_sale_tracker.sales_tracker_tat_breach_mail_template')
        ship_picking_type_ids = self.env['stock.picking.type'].sudo().search([('sequence_code', '=', 'OUT')]).ids
        for rec in self.search([('state', 'in', ['done', 'sale']), ('tat_breach', '=', True)]):
            so_picking = self.env['stock.picking'].search(
                [('picking_type_id', 'in', ship_picking_type_ids), ('sale_id', '=', rec.id)],
                order='create_date asc', limit=1)
            if so_picking and rec.commitment_date and so_picking.scheduled_date.date() > rec.commitment_date.date():
                email_values = template_id.generate_email(rec.id,
                                                          fields=['subject', 'body_html', 'email_from', 'email_to',
                                                                  'partner_to'])

                body = ('%s - become TAT breached '% (rec.name))
                email_values['subject'] = body
                email_values['body_html'] = body
                if rec.partner_id.responsible_user:
                    email_values['email_to'] = rec.partner_id.responsible_user.email
                    template_id.send_mail(rec.id, force_send=True, email_values=email_values or None)
