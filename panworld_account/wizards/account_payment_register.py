from odoo import models, fields, api, _
from odoo.exceptions import UserError

class AccountPaymentRegister(models.TransientModel):
    _inherit = 'account.payment.register'

    @api.depends('line_ids')
    def _compute_can_group_payments(self):
        super()._compute_can_group_payments()
        for wizard in self:
            # Force can_group_payments to True if multiple lines are selected,
            # allowing cross-partner grouping.
            if len(wizard.line_ids) > 1:
                wizard.can_group_payments = True

    def _get_line_batch_key(self, line):
        res = super()._get_line_batch_key(line)
        # Remove partner-specific fields from batch key to force grouping 
        # of different partners into a single batch.
        res['partner_id'] = False
        res['partner_bank_id'] = False
        return res

    @api.model
    def _get_wizard_values_from_batch(self, batch_result):
        res = super()._get_wizard_values_from_batch(batch_result)
        # Fix for Issue: partner_id is False in batch_key to allow cross-partner grouping.
        # Restore partner and bank if the batch identifies a single partner/bank.
        if not res.get('partner_id') and batch_result.get('lines'):
            partners = batch_result['lines'].mapped('partner_id')
            if len(partners) == 1:
                res['partner_id'] = partners.id
                if not res.get('partner_bank_id'):
                    res['partner_bank_id'] = batch_result['lines'][0].move_id.partner_bank_id.id
        return res

    def _create_payment_vals_from_wizard(self, batch_result=None):
        vals = super()._create_payment_vals_from_wizard(batch_result=batch_result)
        if self.group_payment:
            # Collect all partners and invoices from the selected bills
            partners = self.line_ids.mapped('partner_id')
            invoices = self.line_ids.mapped('move_id')
            # Use the first partner as a representative for the payment header.
            # This ensures the bank line (liquidity) has a partner associated,
            # while the split logic in account.payment handles individual vendors.
            p_id = partners[0].id if partners else False
            vals.update({
                'group_payment': True,
                'partner_ids': [fields.Command.set(partners.ids)],
                'invoice_ids': [fields.Command.set(invoices.ids)],
                'partner_id': p_id,
            })
        return vals

    def action_create_payments(self):
        # Ensure all documents are posted before proceeding
        if any(state != 'posted' for state in self.line_ids.mapped('move_id.state')):
            raise UserError(_("You can only register payments for posted journal entries."))
        return super(AccountPaymentRegister, self).action_create_payments()
