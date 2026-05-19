# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) Fidobe Solutions LLC.
#
#    For Module Support : dev3@fidobe.com
#
##############################################################################
from odoo import api, fields, models, Command, _
from odoo.exceptions import ValidationError, UserError
from itertools import chain


class AccountMove(models.Model):
    _inherit = 'account.move'

    related_bill_ids = fields.Many2many("account.move", "invoice_related_bill_rel",
                                        "invoice_id", "bill_id", string="Related Vendor Bills",
                                        domain="[('move_type', '=', 'in_invoice'),('company_id', '=', company_id)]",
                                        copy=False)
    out_of_scope = fields.Boolean(related="journal_id.out_of_scope")
    credit_note_ref = fields.Char(string="Related Credit/ Bill Note Ref.")

    @api.depends('invoice_line_ids')
    def _compute_total_weight(self):
        # Get total weight of all product.
        for rec in self:
            # rec.total_weight = sum(
            #     line.total_weight for line in rec.invoice_line_ids)
            rec.total_weight = sum(rec.invoice_line_ids.mapped('total_weight'))
            rec.total_landed_cost = sum(rec.invoice_line_ids.mapped('landed_cost'))

    @api.depends('total_landed_cost', 'total_dcost')
    def _compute_total_cost(self):
        # Get total cost base on (total landed cost and total dcost).
        for rec in self:
            rec.total_cost = rec.total_landed_cost + rec.total_dcost

    @api.depends('total_sales', 'total_cost')
    def _compute_gp_percentage(self):
        # Get total GP% base on (total sales and total gp)
        gp_percentage = 0.0
        for rec in self:
            if rec.total_cost:
                gp_percentage = (
                    rec.total_sales - rec.total_cost
                ) / rec.total_cost * 100.0
            rec.gp_percentage = gp_percentage

    @api.depends('amount_untaxed')
    def _compute_total_sales(self):
        # Get total sales base on untaxed amount.
        for rec in self:
            rec.total_sales = rec.amount_untaxed

    # @api.depends('invoice_line_ids')
    # def _compute_total_landed_cost(self):
    #     # Get total landed cost base on move line sum(LCO).
    #     for rec in self:
    #         rec.total_landed_cost = sum(
    #             line.landed_cost for line in rec.invoice_line_ids)

    @api.depends('invoice_line_ids')
    def _compute_total_dcost(self):
        # Get total dcost cost base on move line sum(TCO - LCO).
        for rec in self:
            # rec.total_dcost = sum(
            #     line.subtotal_cost for line in rec.invoice_line_ids
            # ) - rec.total_landed_cost
            rec.total_dcost = sum(rec.invoice_line_ids.mapped('subtotal_cost')) - rec.total_landed_cost

    def _inverse_pw_shipping_cost(self):
        pass

    @api.depends("total_weight", "carrier_id", 'total_so_weight', 'so_shipping_cost')
    def _compute_pw_shipping_cost(self):
        # Get shipping cost base on delivery method and total weight).
        pw_shipping_cost = 0.0
        for rec in self:
            if rec.total_weight > 0:
                if rec.total_so_weight and rec.so_shipping_cost > 0:
                    pw_shipping_cost = (rec.total_weight / rec.total_so_weight) * rec.so_shipping_cost
                else:
                    if rec.carrier_id.delivery_type == "fixed":
                        pw_shipping_cost = (
                            rec.carrier_id.fixed_price / rec.total_weight
                        ) * rec.total_weight
                    elif rec.carrier_id.delivery_type == "base_on_rule":
                        vals = rec.carrier_id.rate_shipment(rec)
                        pw_shipping_cost = (
                            vals["carrier_price"] / rec.total_weight
                        ) * rec.total_weight
            rec.pw_shipping_cost = pw_shipping_cost

    total_weight = fields.Float(
        compute='_compute_total_weight', string='Total Weight (in g)',
        help='Total weight of all products in sale order lines', store=True)
    total_sales = fields.Float(
        compute='_compute_total_sales', string='Total Sales',
        help='Total sales', store=True)
    total_landed_cost = fields.Float(
        compute='_compute_total_weight', string='Total Landed Cost',
        help='Total landed cost', store=True)
    total_dcost = fields.Float(
        compute='_compute_total_dcost', string='Total DCost',
        help='Total Dcost', store=True)
    total_cost = fields.Float(
        compute='_compute_total_cost', string='Total Cost',
        help='Total cost base on total landed cost and total Dcost', store=True)
    gp_percentage = fields.Float(
        compute='_compute_gp_percentage', string='GP%',
        help='GP% base on total sale and total cost', store=True)
    analytic_account_id = fields.Many2one(
        'account.analytic.account', string='Analytic Account')
    division_type_id = fields.Many2one('division.type', string='Division Type')
    carrier_id = fields.Many2one('delivery.carrier', string='Delivery Method')
    pw_shipping_cost = fields.Float(
        compute="_compute_pw_shipping_cost",
        inverse="_inverse_pw_shipping_cost",
        string="Shipping Cost",
        help="Shipping cost base on product total weight",
        store=True
    )
    total_so_weight = fields.Float(string='Total SO Weight')
    so_shipping_cost = fields.Float(string='SO Shipping Cost')
    is_shipping_service = fields.Boolean(
        string="Shipping Service", help="To filtered shipping service record.")
    master_airway_bill = fields.Char(
        string="Master Airway Bill", help="To manage master airway bill in shipping service form")
    house_airway_bill = fields.Char(
        string="House Airway Biill", help="To manage house airway biill in shipping service form")
    bill_of_lading = fields.Char(
        string="Bill of Lading", help="To manage bill of lading in shipping service form")
    shipping_mode = fields.Selection([
        ("air", "Air"),
        ("sea", "Sea")
    ], string="Shipping Mode", default="air")
    # sales_manager_id = fields.Many2one("hr.employee", string="Sales Manager", copy=False)
    sales_manager_id = fields.Many2one(
        "hr.employee",
        string="Sales Manager",
        compute="_compute_sales_manager_id",
        store=True,
        copy=False,
        readonly=False,
        precompute=True,
    )

    @api.depends('invoice_line_ids.sale_line_ids.order_id.sales_manager_id')
    def _compute_sales_manager_id(self):
        for move in self:
            # Pull sales manager from linked sale orders if available
            sale_manager = move.invoice_line_ids.sale_line_ids.order_id.sales_manager_id[:1]
            if sale_manager:
                move.sales_manager_id = sale_manager
            elif not move.sales_manager_id:
                # Ensure field is initialized but avoid overwriting existing manual entries
                move.sales_manager_id = False
    country_of_origin_id = fields.Many2one("res.country", string="Country of Origin")
    hsn = fields.Char(string="HSN")
    be_number = fields.Char(string="BE Number", compute='_compute_be_number')

    @api.depends('invoice_line_ids.be_number')
    def _compute_be_number(self):
        for ship in self:
            be_numbers = ship.line_ids.mapped('be_number')
            be_numbers = sorted(set(filter(None, be_numbers)))
            ship.be_number = ', '.join(be_numbers)

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        # Overwrite method to pass division type and analytic account base on customer.
        res = super()._onchange_partner_id()
        self.analytic_account_id = self.partner_id.analytic_account_id or False
        self.division_type_id = self.partner_id.division_type_id or False
        if self.move_type == 'out_invoice' and  self.partner_id:
            self.journal_id = self.partner_id.journal_id or False
        return res


    @api.model
    def default_get(self, fields):
        # Set default journal for shipping service and service quotation.
        res = super().default_get(fields)
        context = self.env.context or {}
        if context.get('default_is_shipping_service') or context.get(
                'default_is_service_quotation'):
            # Get journal base on name (Vendor Bills-Service) as per client requirements.
            journal = self.env['account.journal'].search([
                ('sequence_id.code', '=', 'Vendor Bills-Service'),
                ('company_id', '=', self.env.company.id)
            ], limit=1)
            if journal:
                res.update({'journal_id': journal.id})
        return res

    @api.depends('company_id', 'invoice_filter_type_domain')
    def _compute_suitable_journal_ids(self):
        context = self.env.context or {}
        for move in self:
            company_id = move.company_id.id or self.env.company.id
            domain = [('company_id', '=', company_id)]
            if context.get('default_move_type') == 'entry':
                domain = domain
            else:
                journal_type = move.invoice_filter_type_domain or 'general'
                domain.append(('type', '=', journal_type))
            move.suitable_journal_ids = self.env['account.journal'].search(domain)

    def action_post(self):
        """Change the Sequence for the 'Out of Scope' Journal invoices
           Add Sales Manager"""
        for move in self:
                #Added the temporary check for back dated entry to follow the previous seq only - 12/05/25
            if (move.name == '/' and move.move_type == 'out_invoice' and move.journal_id.out_of_scope and
                    move.invoice_date and move.invoice_date >= fields.Date.from_string('2025-04-01')):
                move.name = self.env['ir.sequence'].next_by_code('out.scope')
            # if move.move_type == 'out_invoice' and not self.sales_manager_id:
            #     raise ValidationError("Please fill in the Sales manager name")
        record = super(AccountMove, self).action_post()
        return record

    def action_update_sales_manager(self):
        """Open wizard for sales manager update"""
        view_id = self.env.ref("panworld_account.sale_manager_update_wizard_view_form")
        return {
            'name': 'Select the Sales Manager',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_id': view_id.id,
            'res_model': 'update.wiz',
            'target': 'new',
            'context': {
                'active_ids': self.ids,
            },
        }

    def action_reset_to_draft(self):
        """Bulk reset the invoices to draft state"""
        invoices = self.env['account.move'].browse(self.env.context.get('active_ids'))
        not_draft_invoices = invoices.filtered(lambda x:x.state != 'draft')
        for invoice in not_draft_invoices:
            invoice.button_draft()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'SUCCESS',
                'message': _('%s Invoice(s) reset to Draft state successfully', len(not_draft_invoices)),
                'type': 'success',
                'sticky': False,
            }
        }
    def action_update_partner_date(self):
        """Open wizard for Partner and Date update"""
        view_id = self.env.ref("panworld_account.partner_and_date_update_wizard_view_form")
        return {
            'name': 'Select the new Partner and Date',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_id': view_id.id,
            'res_model': 'update.wiz',
            'target': 'new',
            'context': {
                'active_ids': self.ids,
            },
        }

    def _generate_deferred_entries(self):
        """
        Generates the deferred entries for the invoice.
        Overridden to support specific deferred expense account from product/account config.
        """
        self.ensure_one()
        if self.state != 'posted':
            return

        deferred_type = "expense" if self.is_purchase_document() else "revenue"
        # Determine company defaults (can be empty if lines have specific accounts)
        default_deferred_account = self.company_id.deferred_expense_account_id if deferred_type == "expense" else self.company_id.deferred_revenue_account_id
        deferred_journal = self.company_id.deferred_expense_journal_id if deferred_type == "expense" else self.company_id.deferred_revenue_journal_id
        
        if not deferred_journal:
            raise UserError(_("Please set the deferred journal in the accounting settings."))
        # Note: We do NOT raise error for missing default_deferred_account here, we check per line.

        moves_vals_to_create = []
        lines_vals_to_create = []
        lines_periods = []
        
        for line in self.line_ids.filtered(lambda l: l.deferred_start_date and l.deferred_end_date):
            
            # Determine target account: Specific > Default
            target_deferred_account = line.account_id.deferred_account_id or default_deferred_account
            
            if not target_deferred_account:
                raise UserError(_("Please set the deferred accounts in the accounting settings or on the account %s.", line.account_id.display_name))

            periods = line._get_deferred_periods()
            if not periods:
                continue

            ref = _("Deferral of %s", line.move_id.name or '')

            moves_vals_to_create.append({
                'move_type': 'entry',
                'deferred_original_move_ids': [Command.set(line.move_id.ids)],
                'journal_id': deferred_journal.id,
                'company_id': self.company_id.id,
                'partner_id': line.partner_id.id,
                'auto_post': 'at_date',
                'ref': ref,
                'name': False,
                'date': line.move_id.date,
            })
            lines_vals_to_create.append([
                self.env['account.move.line']._get_deferred_lines_values(account.id, coeff * line.balance, ref, line.analytic_distribution, line)
                for (account, coeff) in [(line.account_id, -1), (target_deferred_account, 1)]
            ])
            lines_periods.append((line, periods))

        # create the deferred moves
        moves_fully_deferred = self.create(moves_vals_to_create)
        # We write the lines after creation, to make sure the `deferred_original_move_ids` is set.
        # This way we can avoid adding taxes for deferred moves.
        for move_fully_deferred, lines_vals in zip(moves_fully_deferred, lines_vals_to_create):
            for line_vals in lines_vals:
                # This will link the moves to the lines. Instead of move.write('line_ids': lines_ids)
                line_vals['move_id'] = move_fully_deferred.id
        self.env['account.move.line'].create(list(chain(*lines_vals_to_create)))

        deferral_moves_vals = []
        deferral_moves_line_vals = []
        # Create the deferred entries for the periods [deferred_start_date, deferred_end_date]
        for (line, periods), move_vals in zip(lines_periods, moves_vals_to_create):
            
            # Re-determine target account for this loop
            target_deferred_account = line.account_id.deferred_account_id or default_deferred_account

            remaining_balance = line.balance
            for period_index, period in enumerate(periods):
                # For the last deferral move the balance is forced to remaining balance to avoid rounding errors
                force_balance = remaining_balance if period_index == len(periods) - 1 else None
                deferred_amounts = self._get_deferred_amounts_by_line(line, [period], deferred_type)[0]
                balance = deferred_amounts[period] if force_balance is None else force_balance
                remaining_balance -= line.currency_id.round(balance)
                deferral_moves_vals.append({**move_vals, 'date': period[1]})
                deferral_moves_line_vals.append([
                    {
                        **self.env['account.move.line']._get_deferred_lines_values(account.id, coeff * balance, move_vals['ref'], line.analytic_distribution, line),
                        'partner_id': line.partner_id.id,
                        'product_id': line.product_id.id,
                    }
                    for (account, coeff) in [(deferred_amounts['account_id'], 1), (target_deferred_account, -1)]
                ])

        deferral_moves = self.create(deferral_moves_vals)
        for deferral_move, lines_vals in zip(deferral_moves, deferral_moves_line_vals):
            for line_vals in lines_vals:
                # This will link the moves to the lines. Instead of move.write('line_ids': lines_ids)
                line_vals['move_id'] = deferral_move.id
        self.env['account.move.line'].create(list(chain(*deferral_moves_line_vals)))

        to_unlink = deferral_moves.filtered(lambda move: move.currency_id.is_zero(move.amount_total))
        for move_fully_deferred in moves_fully_deferred:
            # If, after calculation, we have 2 deferral entries in the same month, it means that
            # they simply cancel out each other, so there is no point in creating them.
            deferred_move_ids = move_fully_deferred + deferral_moves
            cancelling_moves = deferred_move_ids.filtered(lambda move:
                move_fully_deferred.date.replace(day=1) == move.date.replace(day=1)
                and move.amount_total == move_fully_deferred.amount_total
            )
            if len(cancelling_moves) == 2:
                to_unlink |= cancelling_moves
                continue

        to_unlink.unlink()
        (moves_fully_deferred + deferral_moves - to_unlink)._post(soft=True)

