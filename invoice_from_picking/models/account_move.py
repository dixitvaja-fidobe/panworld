# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) Fidobe Solutions LLC.
#
#    For Module Support : dev3@fidobe.com
#
##############################################################################
from odoo import fields, models, api, _
from odoo.tools import is_html_empty


class AccountMove(models.Model):
    _inherit = "account.move"

    # picking_ids = fields.Many2many("stock.picking", string="Picking References")

    @api.onchange("journal_id")
    def _onchange_journal_id(self):
        """Update taxes and account ONLY for income lines on Sales Invoices,
        and optionally update COGS lines if a COGS account is set on the journal."""
        if self.move_type != "out_invoice" or not self.journal_id:
            return

        income_account = self.journal_id.default_account_id
        cogs_account_journal = self.journal_id.cogs_account_id
        tax_id_list = income_account.tax_ids.ids if income_account else []

        # 1. Update Revenue/Income Lines (Invoice Product Lines)
        income_lines = self.invoice_line_ids.filtered(lambda l: l.display_type == 'product')
        for line in income_lines:
            line.update({
                "tax_ids": [(6, 0, tax_id_list)],
                "account_id": income_account.id,
            })

        # 2. Update existing COGS Lines (if any exist before posting)
        sign = -1 if self.move_type == "out_refund" else 1
        cogs_lines = self.line_ids.filtered(lambda l: l.display_type == 'cogs' and l.balance * sign > 0)
        for line in cogs_lines:
            if cogs_account_journal:
                line.account_id = cogs_account_journal.id
            elif line.product_id:
                accounts = line.product_id.product_tmpl_id.get_product_accounts()
                if accounts.get('expense'):
                    line.account_id = accounts['expense'].id

    def _stock_account_prepare_realtime_out_lines_vals(self):
        """Override to ensure COGS lines use the journal's COGS account
        instead of falling back to the product's expense account or journal's default income account."""
        res = super()._stock_account_prepare_realtime_out_lines_vals()
        for vals in res:
            move = self.browse(vals.get('move_id'))
            if move.journal_id.cogs_account_id and vals.get('display_type') == 'cogs':
                # Identify the expense side: balance sign matches move_type (Debit/Positive for Invoice, Credit/Negative for Refund)
                sign = -1 if move.move_type == 'out_refund' else 1
                if vals.get('amount_currency', 0) * sign > 0:
                    vals['account_id'] = move.journal_id.cogs_account_id.id
        return res





    @api.model
    def update_vendor_bill_with_picking_reference(self):
        batch_size = 2000
        vendor_bills = self.env['account.move'].sudo().with_context(prefetch_fields=False).search([
            ('move_type', '=', 'in_invoice'),
            ('state', 'in', ['draft', 'posted']),
            ('invoice_origin', '!=', False)
        ])

        total_count = 0
        for i in range(0, len(vendor_bills), batch_size):
            batch = vendor_bills[i:i + batch_size]
            self.env.cr.execute("SAVEPOINT batch_savepoint")
            try:
                for rec in batch:
                    related_pickings = self.env['stock.picking'].sudo().search([
                        ('partner_bill_id', '=', rec.id),
                        ('picking_sequence_code', 'in', ['IN_SGRN', 'IN']),
                    ])

                    if related_pickings:
                        print(f"Updating Bill {rec.id} with Pickings {related_pickings.ids}")
                        rec.write({'picking_ids': [(6, 0, related_pickings.ids)]})
                        total_count += 1

                self.env.cr.execute("RELEASE SAVEPOINT batch_savepoint")
                self.env.cache.invalidate()
                self._cr.commit()
            except Exception as e:
                self.env.cr.execute("ROLLBACK TO SAVEPOINT batch_savepoint")
                print(f"Error processing batch: {str(e)}")

        return f"Updated {total_count} vendor bills with picking references."

    @api.depends('move_type', 'partner_id', 'company_id')
    def _compute_narration(self):
        """Add  company specific - custom terms for only the Invoices"""
        use_pw_invoice_terms = self.env['ir.config_parameter'].sudo().get_param('invoice_from_picking.use_pw_invoice_terms')
        for move in self:
            if not move.is_sale_document(include_receipts=True):
                continue
            if not use_pw_invoice_terms:
                move.narration = False
            else:
                lang = move.partner_id.lang or self.env.user.lang
                if not move.company_id.terms_type == 'html':
                    # narration = pw_invoice_terms or ''
                    narration = move.company_id.with_context(lang=lang).pw_invoice_terms if not is_html_empty(
                        move.company_id.pw_invoice_terms) else ''
                else:
                    baseurl = self.env.company.get_base_url() + '/terms'
                    context = {'lang': lang}
                    narration = _('Terms & Conditions: %s', baseurl)
                    del context
                move.narration = narration or False
