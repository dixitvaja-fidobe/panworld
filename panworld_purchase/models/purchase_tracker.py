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
from odoo.tools import drop_view_if_exists
from datetime import datetime


class PurchaseTracker(models.Model):
    _name = 'purchase.tracker.report'
    _description = 'PurchaseTracker'
    _auto = False
    _check_company_auto = True
    _rec_name = 'po_id'

    purchase_tat_date = fields.Datetime(string="Purchase TAT Date")
    shipping_tat_date = fields.Datetime(string="Shipping TAT Date")
    purchase_tat = fields.Char(string="Purchase TAT")
    shipping_tat = fields.Char(string="Shipping TAT")
    shipping_mode_id = fields.Many2one('delivery.carrier', string="Shipping Mode")
    target_weight = fields.Float(string="Target Weight")
    shipper_grn = fields.Float(string="Shiper GRN")
    po_date = fields.Date(string="PO Date")
    po_id = fields.Many2one('purchase.order', string="PO Number",group_operator='array_agg')
    bill_date = fields.Date(string="Bill Date")
    am_id = fields.Many2one('account.move', string="Bill Number")
    tracking_details = fields.Char(string="Tracking Details")
    delivery_date = fields.Date(string="Delivery Date")
    order_status = fields.Char(string="Order Status")
    shipper_status = fields.Char(string="Shipper Status")
    awb_no = fields.Char(string="AWB No.")
    company_id = fields.Many2one('res.company', string="Company")

    # def _query(self):
    #     ship_picking_type_ids = self.env['stock.picking.type'].sudo().search([('sequence_code','=','SHIP')]).ids
    #     if ship_picking_type_ids:
    #         in_clause = f"({','.join(map(str, ship_picking_type_ids))})"
    #     else:
    #         in_clause = "(NULL)"
    #     return f"""
    #         select
    #             row_number() OVER(ORDER BY po.id ASC) as id,
    #             po.id as po_id,
    #             shipper_grn,
    #             po.date_order as po_date,
    #             po.carrier_id as shipping_mode_id,
    #             po.company_id as company_id,
    #             COALESCE(po.target_weight, 0.0) as target_weight,
    #             (case WHEN (coalesce(aml.id::boolean, false))
    #                 THEN
    #                     CASE
    #                          WHEN (am.date > so.commitment_date) THEN
    #                             'TAT Breached'
    #                          WHEN ((CURRENT_DATE - am.date) > dt.purchase_tat) THEN
    #                             'Cancelation Risk'
    #                          WHEN ((CURRENT_DATE - am.date) <= dt.purchase_tat) THEN
    #                             'On-Time'
    #                     END
    #                 ELSE
    #                     CASE
    #                         WHEN (po.date_approve > so.commitment_date) THEN
    #                                 'TAT Breached'
    #                         WHEN ((po.date_approve::date - so.customer_so_date) > dt.po_tat) THEN
    #                                 'Cancelation Risk'
    #                         WHEN ((po.date_approve::date - so.customer_so_date) <= dt.po_tat) THEN
    #                                 'On-Time'
    #                     END
    #                 END
    #             )as purchase_tat,
    #             (case WHEN (coalesce(aml.id::boolean, false))
    #                 THEN
    #                     CASE
    #                          WHEN (am.date > so.commitment_date) THEN
    #                             am.date
    #                          WHEN ((CURRENT_DATE - am.date) > dt.purchase_tat) THEN
    #                             NULL
    #                          WHEN ((CURRENT_DATE - am.date) <= dt.purchase_tat) THEN
    #                             NULL
    #                     END
    #                 ELSE
    #                     CASE
    #                         WHEN (po.date_approve > so.commitment_date) THEN
    #                             po.date_approve
    #                         WHEN ((po.date_approve::date - so.customer_so_date) > dt.po_tat) THEN
    #                             NULL
    #                         WHEN ((po.date_approve::date - so.customer_so_date) <= dt.po_tat) THEN
    #                             NULL
    #                     END
    #                 END
    #             )as purchase_tat_date,
    #             CASE
    #                 WHEN (grn_sp.scheduled_date > so.commitment_date) THEN
    #                     'TAT Breached'
    #                 WHEN ((CURRENT_DATE - grn_sp.scheduled_date::date) > dt.shipping_tat) THEN
    #                     'Cancelation Risk'
    #                 WHEN ((CURRENT_DATE - grn_sp.scheduled_date::date) <= dt.shipping_tat) THEN
    #                     'On-Time'
    #             END as shipping_tat,
    #             CASE
    #                 WHEN (grn_sp.scheduled_date > so.commitment_date) THEN
    #                     grn_sp.scheduled_date
    #                 WHEN ((CURRENT_DATE - grn_sp.scheduled_date::date) > dt.shipping_tat) THEN
    #                     NULL
    #                 WHEN ((CURRENT_DATE - grn_sp.scheduled_date::date) <= dt.shipping_tat) THEN
    #                     NULL
    #             END as shipping_tat_date,
    #             am.id as am_id,
    #             am.date as bill_date,
    #             grn_sp.date_done as delivery_date,
    #             grn_sp.carrier_tracking_ref as awb_no,
    #             shp_sp.name,
    #             shp_sp.carrier_tracking_ref as tracking_details,
    #             CASE WHEN grn_sp.state = 'done' THEN 'DELIVERED' ELSE '' END as order_status,
    #             CASE WHEN (shp_sp.state = 'done'
    #                         AND coalesce(shp_sp.shp_wh_dispatch_date::varchar, '') != '')
    #                     THEN 'SHIPPED' ELSE '' END as shipper_status
    #         from purchase_order po
    #         JOIN (
    #             select
    #                 pol.order_id as pol_po_id,
    #                 SUM(pp.weight * pol.product_qty) as shipper_grn
    #             from purchase_order_line pol
    #             JOIN product_product as pp ON pp.id = pol.product_id
    #             JOIN purchase_order po ON po.id = pol.order_id
    #             where pol.state not in  ('cancel','draft')
    #             group by pol.order_id
    #         ) as pol_shipper_grn  ON pol_shipper_grn.pol_po_id = po.id
    #         LEFT JOIN purchase_order_line pol ON pol.order_id = po.id
    #         LEFT JOIN sale_order so ON so.id = pol.related_so
    #         LEFT JOIN account_move_line as aml ON aml.purchase_line_id = pol.id
    #         LEFT JOIN account_move am ON am.id = aml.move_id
    #         LEFT JOIN stock_move sm ON sm.purchase_line_id = pol.id
    #        LEFT JOIN stock_picking grn_sp
    #             ON sm.picking_id = grn_sp.id
    #            AND grn_sp.picking_type_id NOT IN {in_clause}
    #            AND grn_sp.state = 'done'
    #
    #         LEFT JOIN stock_picking shp_sp
    #             ON sm.picking_id = shp_sp.id
    #            AND shp_sp.picking_type_id IN {in_clause}
    #            AND shp_sp.state = 'done'
    #         LEFT JOIN sale_order_line sol ON sol.id = pol.sale_line_id
    #         LEFT JOIN res_partner rp ON rp.id = po.partner_id
    #         LEFT JOIN division_type dt ON dt.id = rp.division_type_id
    #         WHERE po.state not in ('cancel','draft')
    #     """
    #
    # def init(self):
    #     drop_view_if_exists(self.env.cr, self._table)
    #     self._cr.execute(
    #         """CREATE or REPLACE VIEW %s as (%s)""" % (self._table, self._query()))
    #
    # def _trigger_purchase_and_shipping_tat_breach(self):
    #     current_date = datetime.today().replace(hour=0, minute=0, second=0, microsecond=0)
    #     # Filter purchase orders with breached TAT
    #     purchase_orders = self.search([
    #         ('purchase_tat', '=', 'TAT Breached'),
    #         ('purchase_tat_date', '>', current_date)
    #     ])
    #
    #     # Filter shipping orders with breached TAT
    #     shipping_orders = self.search([
    #         ('shipping_tat', '=', 'TAT Breached'),
    #         ('shipping_tat_date', '>', current_date)
    #     ])
    #
    #     all_purchase_orders = purchase_orders + shipping_orders  if shipping_orders else purchase_orders
    #
    #     purchase_tat_breach_temp_id = self.env.ref(
    #         'panworld_purchase.purchase_tracker_purchase_tat_breach_mail_template')
    #     shipping_tat_breach_temp_id = self.env.ref(
    #         'panworld_purchase.purchase_tracker_shipping_purchase_tat_breach_mail_template')
    #
    #     # Initialize lists to track processed orders
    #     processed_purchase_orders = set()
    #     processed_shipping_orders = set()
    #
    #     for order in all_purchase_orders:
    #         po_id = order.po_id.id
    #         if order.purchase_tat == 'TAT Breached':
    #             if po_id not in processed_purchase_orders:
    #                 vendor_responsible_user_id = order.po_id.partner_id.vendor_responsible_user
    #                 if vendor_responsible_user_id:
    #                     email_values = purchase_tat_breach_temp_id.generate_email(order.id,
    #                                                                               fields=['subject', 'body_html',
    #                                                                                       'email_from', 'email_to',
    #                                                                                       'partner_to'])
    #                     email_values['email_to'] = vendor_responsible_user_id.login
    #                     purchase_tat_breach_temp_id.send_mail(order.id, force_send=True, email_values=email_values or None)
    #                 processed_purchase_orders.add(po_id)
    #         if order.shipping_tat == 'TAT Breached':
    #             if po_id not in processed_shipping_orders:
    #                 shipping_users = order.env.ref('panworld_purchase.shipping_tat_breached_group').mapped('users')
    #                 for ship_user in shipping_users:
    #                     email_values = shipping_tat_breach_temp_id.generate_email(order.id,
    #                                                                               fields=['subject', 'body_html',
    #                                                                                       'email_from', 'email_to',
    #                                                                                       'partner_to'])
    #                     email_values['email_to'] = ship_user.email or ship_user.email_formatted
    #                     shipping_tat_breach_temp_id.send_mail(order.id, force_send=True, email_values=email_values or None)
    #                 processed_shipping_orders.add(po_id)
