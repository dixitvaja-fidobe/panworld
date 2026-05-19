from odoo import models, fields, api, _
from odoo.tools import mail as mail_tool
try:
    from odoo.addons.mail.models import mail_thread
except ImportError:
    mail_thread = None

# Fix for Odoo 19 'dict' object has no attribute 'encode' error in mail system
original_formataddr = mail_tool.formataddr

def safe_formataddr(pair, charset='utf-8'):
    name, address = pair
    if isinstance(name, dict):
        # Pick a string from the dictionary (translations)
        name = name.get('en_US') or (next(iter(name.values())) if name else '')
    elif not isinstance(name, str) and name:
        name = str(name)
    return original_formataddr((name, address), charset)

# Apply patch globally
mail_tool.formataddr = safe_formataddr
if mail_thread and hasattr(mail_thread, 'formataddr'):
    mail_thread.formataddr = safe_formataddr

class PosOrder(models.Model):
    _inherit = 'pos.order'

    payment_count = fields.Integer(string='Payment Count', compute='_compute_payment_count')

    @api.model
    def sync_from_ui(self, orders):
        # Force the context language for the entire sync process to avoid
        # translatable fields returning dictionaries.
        if not self.env.context.get('lang'):
            self = self.with_context(lang=self.env.user.lang or 'en_US')
        return super(PosOrder, self).sync_from_ui(orders)

    def _generate_pos_order_invoice(self):
        # Force the context language to ensure translatable fields like partner name
        # are returned as strings, not dictionaries.
        if not self.env.context.get('lang'):
            self = self.with_context(lang=self.env.user.lang or 'en_US')
        return super()._generate_pos_order_invoice()

    def _compute_payment_count(self):
        for order in self:
            count = 0
            if order.account_move:
                # Find all journal items reconciled with the invoice
                reconciled_lines = order.account_move.line_ids.full_reconcile_id.reconciled_line_ids
                if not reconciled_lines:
                    reconciled_lines = order.account_move.line_ids.matched_debit_ids.debit_move_id | \
                                       order.account_move.line_ids.matched_credit_ids.credit_move_id
                # Get the moves of these lines, excluding the invoice itself
                payment_moves = reconciled_lines.move_id.filtered(lambda m: m != order.account_move)
                count = len(payment_moves)
            order.payment_count = count

    def action_view_invoice_payments(self):
        self.ensure_one()
        payment_moves = self.env['account.move']
        if self.account_move:
            reconciled_lines = self.account_move.line_ids.full_reconcile_id.reconciled_line_ids
            if not reconciled_lines:
                reconciled_lines = self.account_move.line_ids.matched_debit_ids.debit_move_id | \
                                   self.account_move.line_ids.matched_credit_ids.credit_move_id
            payment_moves = reconciled_lines.move_id.filtered(lambda m: m != self.account_move)
            
        action = self.env["ir.actions.actions"]._for_xml_id("account.action_move_out_invoice_type")
        action['name'] = _("Payment Journals")
        action['domain'] = [('id', 'in', payment_moves.ids)]
        action['context'] = {'create': False}
        action['views'] = [(False, 'list'), (False, 'form')]
        return action
