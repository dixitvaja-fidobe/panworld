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
from odoo.exceptions import UserError, ValidationError
import datetime
import logging
_logger = logging.getLogger(__name__)

class StockPicking(models.Model):
    _inherit = "stock.picking"

    @api.model_create_multi
    def create(self, vals_list):
        pickings = super(StockPicking, self).create(vals_list)
        for picking in pickings:
            if picking.purchase_id and picking.state in ('waiting', 'confirmed'):
                picking.action_assign()
                picking.move_ids.write({'picked': False})
        return pickings

    def write(self, values):
        res = super(StockPicking, self).write(values)
        if 'purchase_id' in values and values['purchase_id']:
            for picking in self:
                if picking.state in ('waiting', 'confirmed'):
                    picking.action_assign()
        # if 'partner_bill_id' in values:
        #     for record in self:
        #         quantities = record.partner_bill_id.invoice_line_ids.mapped('quantity')
        #         record.bill_quantity = sum(quantities)
        return res

    vendor_dispatch_date = fields.Date(related='partner_bill_id.invoice_date', string='Vendor Dispatch Date')
    shp_wh_dispatch_date = fields.Datetime()

    customer_sales_order = fields.Char(string='CSO Reference')
    consolidated_weight = fields.Float("Consolidated Weight")
    uae_wh_receiving_date = fields.Date(string="UAE Warehouse Receiving Date")
    is_carrier_tracking_required = fields.Boolean(
        "Is Carrier Tracking Required", help="Base on this boolean required Tracking(AWB)")
    partner_id = fields.Many2one('res.partner')
    # partner_bill_id = fields.Many2one('account.move', string='Related bill', domain="[('move_type', '=', 'in_invoice'),('partner_id','=',partner_id)]")
    # partner_bill_id = fields.Many2one('account.move', string='Related bill', domain="['|','|',('name', '=', 'Not Available1'), ('partner_id','=',partner_id), ('move_type', '=', 'in_invoice')]")
    partner_bill_id = fields.Many2one('account.move', string='Related bill', domain="[('move_type', '=', 'in_invoice'), ('partner_id', '=', partner_id)]")
    is_received_qty = fields.Boolean(string='PO Line Received Qty', compute="_compute_is_received_qty")

    # Bill Info Fields:
    doc_nb_console = fields.Char(string='Doc NB. (Console)', )
    bill_nb = fields.Char(string='Bill No.', related='partner_bill_id.ref', store=True)
    bill_date = fields.Date(string='Bill Date', related='partner_bill_id.invoice_date', store=True)
    po_currency_id = fields.Many2one('res.currency', related='purchase_id.currency_id', string='Currency')
    other_bill_charges = fields.Float(string='Other Bill Charges')
    # bill_quantity = fields.Float(string="Bill Quantity", compute='_compute_boe_no')
    bill_value = fields.Monetary(string="Total Bill Value", related='partner_bill_id.value_as_per_bill', store=True)
    currency_id = fields.Many2one('res.currency', related="company_id.currency_id", required=True, readonly=False, )
    # Shipping Info Fields:
    consolidated_weight_shipping = fields.Float(string="Consolidation Weight", compute='_compute_tracking_details')
    boe_no = fields.Char(string='BOE No.', related='partner_bill_id.boe_no', store=True)
    ship_no = fields.Char(string='Ship No.', compute='_compute_tracking_details', store=True)
    boe_date = fields.Date(string='BOE Date', compute='_compute_tracking_details')
    ready_for_scan_1 = fields.Char(string="Ready for Scan", compute='_compute_tracking_details')

    # bill_quantity = fields.Float(string='Bill Quantity', compute='_compute_quantity', store=True)

    total_bill_quantity = fields.Float(
        string='Total Bill Quantity',
        compute='_compute_total_bill_quantity',
        store=True,
    )

    def update_to_po(self):
        """Update the 'To be received qty' with the Done qty for the corresponding PO"""
        for move in self.move_ids:
            if move.product_uom_qty > 0:
                move.purchase_line_id.write({'to_be_received_qty': move.quantity})

    def action_set_quantities_to_reservation(self):
        """Update the 'To be received qty' with the Done qty for the corresponding PO"""
        res = super(StockPicking, self).action_set_quantities_to_reservation()
        for move_line in self.move_line_ids:
            if move_line.move_id.product_uom_qty > 0:
                move_line.move_id.purchase_line_id.write({'to_be_received_qty': move_line.qty_done})
        return res

    # @api.depends('partner_bill_id.invoice_line_ids.quantity')
    # def _compute_quantity(self):
    #     for record in self:
    #         quantities = record.partner_bill_id.invoice_line_ids.mapped('quantity')
    #         record.bill_quantity = sum(quantities)

    @api.onchange('consolidated_weight_shipping')
    def _onchange_consolidated_weight_shipping(self):
        lc_ids = self.env["stock.landed.cost"].search([("picking_ids", "in", self.ids)])
        for rec in lc_ids:
            rec.consolidated_weight = self.consolidated_weight_shipping

    @api.onchange('partner_bill_id', 'partner_id')
    def _onchange_partner_id(self):
        self.invoice_state = 'invoiced' if self.partner_bill_id else '2binvoiced'
        domain = [('move_type', '=', 'in_invoice')]
        if self.partner_id:
            domain += ['|', ('partner_id', '=', self.partner_id.id), ('name', '=', 'Not Available1')]
        else:
            domain += [('name', '=', 'Not Available1'), ('partner_id', '!=', False)]
        return {'domain': {'partner_bill_id': domain}}

    @api.depends('partner_bill_id.invoice_line_ids.quantity', 'purchase_id')
    def _compute_total_bill_quantity(self):
        # Filter pickings that have both a bill and a PO to avoid useless queries
        valid_recs = self.filtered(lambda r: r.partner_bill_id and r.purchase_id)
        (self - valid_recs).total_bill_quantity = 0.0
        
        if not valid_recs:
            return

        # Batch SQL query for all valid pickings
        bill_ids = valid_recs.mapped('partner_bill_id').ids
        po_ids = valid_recs.mapped('purchase_id').ids

        self.env.cr.execute(
            """
            SELECT am.id, pol.order_id, SUM(ail.quantity)
            FROM account_move_line ail
            JOIN account_move am ON am.id = ail.move_id
            JOIN purchase_order_line pol ON pol.id = ail.purchase_line_id
            WHERE am.id = ANY(%s)
              AND pol.order_id = ANY(%s)
            GROUP BY am.id, pol.order_id
            """,
            (bill_ids, po_ids)
        )

        # Create a mapping for fast O(1) lookup
        results = {(res[0], res[1]): res[2] for res in self.env.cr.fetchall()}

        for rec in valid_recs:
            rec.total_bill_quantity = results.get((rec.partner_bill_id.id, rec.purchase_id.id), 0.0)

    def _compute_is_received_qty(self):
        for rec in self:
            if rec.purchase_id:
                rec.is_received_qty = True
            elif 'purchase_ids' in rec._fields and rec.purchase_ids:
                rec.is_received_qty = True
            elif rec.picking_type_id.code == 'internal' and rec.picking_type_id.default_location_dest_id.usage == 'transit' and rec.picking_type_id.default_location_dest_id.is_shipper_location:
                rec.is_received_qty = True
            else:
                rec.is_received_qty = False

    @api.model
    def _search(self,args,offset=0,limit=None,order=None,**kwargs):
        args = args or []
        context = self.env.context or {}
        if (
            context.get("from_pw_batch")
            and context.get("purchase_order_ids")
            and context.get("purchase_order_ids")[0]
            and context.get("purchase_order_ids")[0][2]
        ):
            picking_ids = (
                self.env["purchase.order"].search(
                    [("id", "in", context.get("purchase_order_ids")[0][2])]
                )
            ).mapped("picking_ids")
            args.extend(
                [("id", "in", picking_ids.ids), ]
            )
        return super(StockPicking, self)._search(
            args,
            offset=offset,
            limit=limit,
            order=order,
        )
    
    def _check_open_pickings(self, purchase_orders):
        return bool(purchase_orders.mapped('picking_ids').filtered(lambda l: l.backorder_id and l.state not in ('done','cancel')))
    
    # Improvement for 23-July-2022 testing -> Close purchase order without doing Lock only for Main Picking(Incoming)
    # def _action_done(self):
    #     so_list = []
    #     res = super()._action_done()
    #     for rec in self:
    #         if rec.picking_type_code == 'incoming' and not rec.env.context.get('cancel_backorder') and rec.purchase_ids:
    #             if not rec._check_open_pickings(rec.purchase_ids):
    #                 rec.purchase_ids.button_done()
    #     return res
            # if rec.picking_type_code == 'incoming' and rec.picking_type_id.sequence_code != 'SHIP' and rec.state == 'done':
            #     template_id = self.env.ref('panworld_purchase.grn_picking_validation_mail_template')
            #     if template_id:
            #         email_values = template_id.generate_email(rec.id,
            #                                             fields=['subject', 'body_html', 'email_from', 'partner_to'])
            #         for move_line in rec.move_ids:
            #             if move_line.purchase_line_id.related_so.name not in so_list:
            #                 for po_line in rec.purchase_id.order_line.filtered(lambda l: l.id == move_line.purchase_line_id.id):
            #                     subject = ('%s | %s | %s | %s | %s |' % (
            #                     po_line.related_so.name, po_line.related_so.partner_id.name,
            #                     po_line.related_so.customer_sales_order, rec.name, po_line.order_id.partner_id.name))
            #                     if po_line.related_so:
            #                         email_values['email_to'] = ('%s'% po_line.related_so.partner_id.responsible_user.email)
            #                         email_values['subject'] = subject
            #                         email_values['body_html'] = (
            #                             'Please check the material received '
            #                             ' <br/> %s <br/>'%subject)
            #                         template_id.send_mail(rec.id, force_send=True, email_values=email_values or None)
            #                 so_list.append(move_line.purchase_line_id.related_so.name)

                    #TODO: code change on 28 march..
                    # for move_line in rec.move_ids:
                    #     for po_line in rec.purchase_id.order_line.filtered(lambda l: l.id == move_line.purchase_line_id.id):
                    #         subject = ('%s | %s | %s | %s | %s |' % (
                    #         po_line.related_so.name, po_line.related_so.partner_id.name,
                    #         po_line.related_so.customer_sales_order, rec.name, po_line.order_id.partner_id.name))
                    #         if po_line.related_so:
                    #             email_values['email_to'] = ('%s'% po_line.related_so.partner_id.responsible_user.email)
                    #             email_values['subject'] = subject
                    #             email_values['body_html'] = (
                    #                 'Please check the material received '
                    #                 ' <br/> %s <br/>'%subject)
                    #             template_id.send_mail(rec.id, force_send=True, email_values=email_values or None)



    # Improvement for 23-July-2022 testing -> Close purchase order without doing Lock only for Main Picking(Incoming)
    # def action_cancel(self):
    #     res = super().action_cancel()
    #     for rec in self:
    #         if rec.picking_type_code == 'incoming' and self.purchase_ids and not self._check_open_pickings(self.purchase_ids):
    #             self.purchase_ids.write({'state': 'done'})
    #     return res

    def custom_action_cancel(self):
        return {
            "name": "Cancel Reason",
            "view_mode": "form",
            "res_model": "picking.cancel.reason",
            "view_type": "form",
            "type": "ir.actions.act_window",
            "target": "new",
        }

    def action_done_qty_update(self):
        start_time = datetime.datetime.now()
        _logger.info(">>> PERFORMANCE: action_done_qty_update START for picking %s (ID: %s)", self.mapped('name'), self.ids)
        # Set all reserved qty to done (quantity field in Odoo 19)
        for picking in self:
            moves = picking.move_ids.filtered(lambda l: l.state not in ['cancel', 'done'])
            for move in moves:
                # Use to_be_received_qty if available, otherwise demand quantity
                qty_to_set = move.purchase_line_id.to_be_received_qty
                move.write({
                    'quantity': qty_to_set,
                    'picked': True
                })
            picking.message_post(body=_("Quantities have been updated based on PO lines."))
        _logger.info(">>> PERFORMANCE: action_done_qty_update TOTAL took %s for picking %s (ID: %s)", datetime.datetime.now() - start_time, self.mapped('name'), self.ids)

    def action_set_quantity(self):
        start_time = datetime.datetime.now()
        _logger.info(">>> PERFORMANCE: action_set_quantity START for picking %s (ID: %s)", self.mapped('name'), self.ids)
        """Set demand quantity to done quantity for all moves and move lines"""
        for picking in self:
            moves = picking.move_ids.filtered(lambda m: m.state not in ('done', 'cancel'))
            for move in moves:
                move.write({
                    'quantity': move.product_uom_qty,
                    'picked': True
                })
            picking.message_post(body=_("Demand quantities have been set as done."))
        _logger.info(">>> PERFORMANCE: action_set_quantity TOTAL took %s for picking %s (ID: %s)", datetime.datetime.now() - start_time, self.mapped('name'), self.ids)

    def action_reset_quantity(self):
        start_time = datetime.datetime.now()
        _logger.info(">>> PERFORMANCE: action_reset_quantity START for picking %s (ID: %s)", self.mapped('name'), self.ids)
        """Reset done quantity but set demand quantity as reserved for all moves"""
        for picking in self:
            moves = picking.move_ids.filtered(lambda m: m.state not in ('done', 'cancel'))
            for move in moves:
                move.write({
                    'quantity': move.product_uom_qty,
                    'picked': False
                })
            picking.message_post(body=_("Done quantities have been reset. Demand quantities have been set as reserved."))
        _logger.info(">>> PERFORMANCE: action_reset_quantity TOTAL took %s for picking %s (ID: %s)", datetime.datetime.now() - start_time, self.mapped('name'), self.ids)

    def action_view_grn_picking(self):
        # related_grn_picking_id = self.env['stock.picking'].search([('shipper_stock_added', '=', self.name),('picking_type_id.code','=','incoming'),('location_dest_id.usage','=','internal'),('backorder_id','=',None)],limit=1)
        related_grn_picking_id = self.env['stock.picking'].search([('shipper_stock_added', '=', self.name),('picking_type_id.code','=','incoming'),('backorder_id','=',None)],limit=1)
        if len(related_grn_picking_id) == 1:
            return {
                'type': 'ir.actions.act_window',
                'name': 'Related GRN',
                'view_mode': 'form',
                "view_type": "form",
                'res_model': 'stock.picking',
                'res_id': related_grn_picking_id.id,
                'target': 'current'
            }
        else:
            raise ValidationError('There is no Related GRN for this SHP!')

    def button_validate(self):
        res = super(StockPicking, self.with_context(bypass_presale_track_block=True)).button_validate()
        for picking in self:
            if picking.picking_type_code == 'incoming' and not picking.is_return_picking and picking.grn_tracking_number_id and not picking.grn_tracking_number_id.ship_no:
                raise ValidationError('Please fill in the Ship No for the Tracking Number: %s'
                    % picking.grn_tracking_number_id.name)
        return res

    @api.depends('location_dest_id.usage', 'location_id.usage')
    def _compute_is_dropship(self):
        """Overriden the addon method to show the shipments under Receipts itself rather than as Dropship
                --Enhancement done for V19 migration"""
        for picking in self:
            picking.is_dropship = picking.location_dest_id.usage == 'customer' and picking.location_id.usage == 'supplier'
