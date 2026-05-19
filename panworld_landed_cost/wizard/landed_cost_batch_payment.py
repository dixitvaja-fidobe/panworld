# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError

class LandedCostBatchPayment(models.TransientModel):
    _name = 'landed.cost.batch.payment'
    _description = 'Landed Cost Batch Payment Wizard'

    partner_id = fields.Many2one('res.partner', string='Vendor', required=True, readonly=True)
    journal_id = fields.Many2one('account.journal', string='Journal', required=True, domain=[('type', 'in', ('bank', 'cash'))])
    amount = fields.Monetary(string='Payment Amount', required=True)
    currency_id = fields.Many2one('res.currency', string='Currency', required=True, default=lambda self: self.env.company.currency_id)
    payment_date = fields.Date(string='Payment Date', required=True, default=fields.Date.context_today)
    communication = fields.Char(string='Memo')
    landed_cost_ids = fields.Many2many('stock.landed.cost', string='Landed Costs')
    payment_method_line_id = fields.Many2one('account.payment.method.line', string='Payment Method',
        domain="[('payment_type', '=', 'outbound'), ('journal_id', '=', journal_id)]")

    @api.model
    def default_get(self, fields_list):
        res = super(LandedCostBatchPayment, self).default_get(fields_list)
        context = self.env.context
        if context.get('active_model') == 'stock.landed.cost' and context.get('active_ids'):
            landed_costs = self.env['stock.landed.cost'].browse(context['active_ids'])
            if not landed_costs:
                return res
            
            # Check state
            if any(lc.state != 'done' for lc in landed_costs):
                raise UserError(_("You can only create payments for Posted Landed Costs."))

            # Check if any LC already has a payment
            already_paid = landed_costs.filtered(lambda lc: lc.payment_ids)
            if already_paid:
                names = ', '.join(already_paid.mapped('name'))
                raise UserError(_("The following Landed Costs already have a payment linked: %s. \nEvery Landed Cost can have only a single payment.", names))

            # Check if all LCs have the same partner
            partners = landed_costs.mapped('partner_id')
            if len(partners) > 1:
                raise UserError(_("All selected Landed Costs must belong to the same Vendor."))
            if not partners:
                 raise UserError(_("Selected Landed Costs must have a Vendor assigned."))
            
            res['partner_id'] = partners.id
            res['landed_cost_ids'] = [(6, 0, landed_costs.ids)]
            
            # Sum amounts
            total_amount = sum(lc.amount_total for lc in landed_costs)
            res['amount'] = total_amount
            
            # Memo
            res['communication'] = ', '.join(landed_costs.mapped('name'))
        return res

    def action_create_payment(self):
        self.ensure_one()
        payment_vals = {
            'date': self.payment_date,
            'amount': self.amount,
            'payment_type': 'outbound',
            'partner_type': 'supplier',
            'memo': self.communication,
            'journal_id': self.journal_id.id,
            'currency_id': self.currency_id.id,
            'partner_id': self.partner_id.id,
            'payment_method_line_id': self.payment_method_line_id.id,
            'landed_cost_ids': [(6, 0, self.landed_cost_ids.ids)],
            'is_landed_cost_payment': True,
        }
        
        payment = self.env['account.payment'].create(payment_vals)
        # payment.action_post()
        
        # Explicitly link if M2M doesn't auto-update immediately in cache
        for cost in self.landed_cost_ids:
            cost.payment_ids = [(4, payment.id)]
        
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'account.payment',
            'res_id': payment.id,
            'view_mode': 'form',
            'target': 'current',
        }
