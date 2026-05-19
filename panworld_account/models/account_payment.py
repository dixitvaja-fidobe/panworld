from odoo import api, fields, models, _, Command
from odoo.exceptions import UserError


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    group_payment = fields.Boolean(string="Group Payment", copy=False)
    partner_ids = fields.Many2many('res.partner', string="Customers", copy=False)

    @api.onchange('group_payment')
    def _onchange_group_payment(self):
        if self.group_payment:
            self.partner_id = None
        else:
            self.partner_ids = None

    def _prepare_move_line_default_vals(self, write_off_line_vals=None, force_balance=None):
        ''' OVERRIDE ADDON METHOD TO ADD THE JOURNAL LINES FOR MULTIPLE CUSTOMERS SELECTED FOR GROUP PAYMENT
        Prepare the dictionary to create the default account.move.lines for the current payment.
        :param write_off_line_vals: Optional list of dictionaries to create a write-off account.move.line easily containing:
            * amount:       The amount to be added to the counterpart amount.
            * name:         The label to set on the line.
            * account_id:   The account on which create the write-off.
        :param force_balance: Optional balance.
        :return: A list of python dictionary to be passed to the account.move.line's 'create' method.
        '''
        self.ensure_one()
        write_off_line_vals = write_off_line_vals or []

        if not self.outstanding_account_id:
            raise UserError(_(
                "You can't create a new payment without an outstanding payments/receipts account set either on the company or the %(payment_method)s payment method in the %(journal)s journal.",
                payment_method=self.payment_method_line_id.name, journal=self.journal_id.display_name))

        # Compute amounts.
        write_off_line_vals_list = write_off_line_vals or []
        write_off_amount_currency = sum(x['amount_currency'] for x in write_off_line_vals_list)
        write_off_balance = sum(x['balance'] for x in write_off_line_vals_list)

        if self.payment_type == 'inbound':
            # Receive money.
            liquidity_amount_currency = self.amount
        elif self.payment_type == 'outbound':
            # Send money.
            liquidity_amount_currency = -self.amount
        else:
            liquidity_amount_currency = 0.0

        if not write_off_line_vals and force_balance is not None:
            sign = 1 if liquidity_amount_currency > 0 else -1
            liquidity_balance = sign * abs(force_balance)
        else:
            liquidity_balance = self.currency_id._convert(
                liquidity_amount_currency,
                self.company_id.currency_id,
                self.company_id,
                self.date,
            )

        counterpart_amount_currency = -liquidity_amount_currency - write_off_amount_currency
        counterpart_balance = -liquidity_balance - write_off_balance
        currency_id = self.currency_id.id

        # Compute a default label to set on the journal items.
        liquidity_line_name = ''.join(x[1] for x in self._get_aml_default_display_name_list() if x[1])
        counterpart_line_name = liquidity_line_name
        line_vals_list = []

        # Prepare allocation data for Group Payments
        allocation_data = []
        if self.partner_ids:
            if self.invoice_ids:
                bill_lines = self.invoice_ids.line_ids.filtered(
                    lambda l: l.account_id.account_type in ('asset_receivable', 'liability_payable')
                )
                grouped_residuals = {}
                for line in bill_lines:
                    key = (line.partner_id.id, line.account_id.id)
                    grouped_residuals[key] = grouped_residuals.get(key, 0.0) + line.amount_residual
                
                total_residual = sum(grouped_residuals.values())
                
                if not self.currency_id.is_zero(total_residual):
                    for (p_id, a_id), residual in grouped_residuals.items():
                        ratio = residual / total_residual
                        allocation_data.append({
                            'partner_id': p_id,
                            'account_id': a_id,
                            'counterpart_amount_currency': self.currency_id.round(counterpart_amount_currency * ratio),
                            'counterpart_balance': self.company_id.currency_id.round(counterpart_balance * ratio),
                            'liquidity_amount_currency': self.currency_id.round(liquidity_amount_currency * ratio),
                            'liquidity_balance': self.company_id.currency_id.round(liquidity_balance * ratio),
                        })
            
            if not allocation_data:
                partner_count = len(self.partner_ids)
                for partner in self.partner_ids:
                    allocation_data.append({
                        'partner_id': partner.id,
                        'account_id': self.destination_account_id.id,
                        'counterpart_amount_currency': self.currency_id.round(counterpart_amount_currency / partner_count),
                        'counterpart_balance': self.company_id.currency_id.round(counterpart_balance / partner_count),
                        'liquidity_amount_currency': self.currency_id.round(liquidity_amount_currency / partner_count),
                        'liquidity_balance': self.company_id.currency_id.round(liquidity_balance / partner_count),
                    })

        # -----------------------------
        # 1. Liquidity line(s) (Bank/Cash)
        # -----------------------------
        if allocation_data:
            total_liq_amt = 0.0
            total_liq_bal = 0.0
            # Group by partner to minimize lines while keeping names
            partner_liq_data = {}
            for d in allocation_data:
                p_id = d['partner_id']
                partner_liq_data.setdefault(p_id, {'amt': 0.0, 'bal': 0.0})
                partner_liq_data[p_id]['amt'] += d['liquidity_amount_currency']
                partner_liq_data[p_id]['bal'] += d['liquidity_balance']
            
            p_items = list(partner_liq_data.items())
            for index, (p_id, vals) in enumerate(p_items, start=1):
                amt, bal = vals['amt'], vals['bal']
                if index == len(p_items): # Rounding fix
                    amt = self.currency_id.round(liquidity_amount_currency - total_liq_amt)
                    bal = self.company_id.currency_id.round(liquidity_balance - total_liq_bal)
                
                line_vals_list.append({
                    'name': liquidity_line_name,
                    'date_maturity': self.date,
                    'amount_currency': amt,
                    'currency_id': currency_id,
                    'debit': bal if bal > 0.0 else 0.0,
                    'credit': -bal if bal < 0.0 else 0.0,
                    'partner_id': p_id,
                    'account_id': self.outstanding_account_id.id,
                })
                total_liq_amt += amt
                total_liq_bal += bal
        else:
            line_vals_list.append({
                'name': liquidity_line_name,
                'date_maturity': self.date,
                'amount_currency': liquidity_amount_currency,
                'currency_id': currency_id,
                'debit': liquidity_balance if liquidity_balance > 0.0 else 0.0,
                'credit': -liquidity_balance if liquidity_balance < 0.0 else 0.0,
                'partner_id': self.partner_id.id,
                'account_id': self.outstanding_account_id.id,
            })

        # -----------------------------
        # 2. Receivable / Payable lines
        # -----------------------------
        if allocation_data:
            total_allocated_amount = 0.0
            total_allocated_balance = 0.0
            for index, data in enumerate(allocation_data, start=1):
                amount_currency = data['counterpart_amount_currency']
                balance = data['counterpart_balance']

                if index == len(allocation_data): # Rounding fix
                    amount_currency = self.currency_id.round(counterpart_amount_currency - total_allocated_amount)
                    balance = self.company_id.currency_id.round(counterpart_balance - total_allocated_balance)

                line_vals_list.append({
                    'name': counterpart_line_name,
                    'date_maturity': self.date,
                    'amount_currency': amount_currency,
                    'currency_id': currency_id,
                    'debit': balance if balance > 0.0 else 0.0,
                    'credit': -balance if balance < 0.0 else 0.0,
                    'partner_id': data['partner_id'],
                    'account_id': data['account_id'],
                })
                total_allocated_amount += amount_currency
                total_allocated_balance += balance
        else:
            line_vals_list.append({
                'name': self.payment_reference or counterpart_line_name,
                'date_maturity': self.date,
                'amount_currency': counterpart_amount_currency,
                'currency_id': currency_id,
                'debit': counterpart_balance if counterpart_balance > 0.0 else 0.0,
                'credit': -counterpart_balance if counterpart_balance < 0.0 else 0.0,
                'partner_id': self.partner_id.id,
                'account_id': self.destination_account_id.id,
            })

        return line_vals_list + write_off_line_vals_list
    def _synchronize_to_moves(self, changed_fields):
        ''' OVERRIDE to handle multiple liquidity/counterpart lines.
        The default implementation expects singletons for liquidity and counterpart lines,
        which fails when group_payment is used.
        '''
        if not any(field_name in changed_fields for field_name in self._get_trigger_fields_to_synchronize()):
            return

        for pay in self:
            if pay.move_id.state == 'posted':
                continue

            liquidity_lines, counterpart_lines, writeoff_lines = pay._seek_for_lines()

            # If it's a normal payment with single lines, let super handle it
            # to maintain compatibility with other modules (like withholding).
            if len(liquidity_lines) <= 1 and len(counterpart_lines) <= 1:
                super(AccountPayment, pay)._synchronize_to_moves(changed_fields)
                continue

            # Case for multiple lines (Group Payment)
            # Preserve existing write-offs to avoid losing allocation details during sync
            write_off_line_vals = []
            if writeoff_lines:
                write_off_line_vals.append({
                    'name': writeoff_lines[0].name,
                    'account_id': writeoff_lines[0].account_id.id,
                    'partner_id': writeoff_lines[0].partner_id.id,
                    'currency_id': writeoff_lines[0].currency_id.id,
                    'amount_currency': sum(writeoff_lines.mapped('amount_currency')),
                    'balance': sum(writeoff_lines.mapped('balance')),
                })

            line_vals_list = pay._prepare_move_line_default_vals(write_off_line_vals=write_off_line_vals)

            # Handle withholding taxes if the module is installed and active
            if hasattr(pay, 'withholding_line_ids') and pay.should_withhold_tax:
                withholding_line_values_list = pay.withholding_line_ids._prepare_withholding_amls_create_values()

                # Adjust liquidity lines to account for withholding
                # We find the liquidity values in our generated list
                liq_vals = [v for v in line_vals_list if v.get('account_id') == pay.outstanding_account_id.id]
                if liq_vals:
                    # Subtract withholding from the first liquidity line balance/amount
                    for wh_vals in withholding_line_values_list:
                        bal = liq_vals[0]['debit'] - liq_vals[0]['credit'] - wh_vals['balance']
                        liq_vals[0].update({
                            'debit': bal if bal > 0.0 else 0.0,
                            'credit': -bal if bal < 0.0 else 0.0,
                            'amount_currency': liq_vals[0]['amount_currency'] - wh_vals['amount_currency'],
                        })

                # Add withholding lines back (replaces existing write-offs in the move)
                line_vals_list += withholding_line_values_list

            # Sync by using Command.update/create/delete to preserve IDs (non-destructive)
            # This is critical to maintain reconciliation status on matched lines.
            line_ids_commands = []

            # Use pools to match generated vals with existing lines
            pool_liquidity = list(liquidity_lines)
            pool_counterpart = list(counterpart_lines)
            pool_writeoff = list(writeoff_lines)

            for vals in line_vals_list:
                acc_id = vals.get('account_id')
                p_id = vals.get('partner_id')

                matched = None
                # 1. Try to match by account AND partner (most precise)
                for pool in [pool_liquidity, pool_counterpart, pool_writeoff]:
                    matches = [l for l in pool if l.account_id.id == acc_id and l.partner_id.id == p_id]
                    if matches:
                        matched = matches[0]
                        pool.remove(matched)
                        break

                # 2. If no match, try match by account only (e.g. for write-offs or if partner was changed)
                if not matched:
                    for pool in [pool_liquidity, pool_counterpart, pool_writeoff]:
                        matches = [l for l in pool if l.account_id.id == acc_id]
                        if matches:
                            matched = matches[0]
                            pool.remove(matched)
                            break

                if matched:
                    line_ids_commands.append(Command.update(matched.id, vals))
                else:
                    line_ids_commands.append(Command.create(vals))

            # Delete any lines remaining in pools that were not matched
            for l in pool_liquidity + pool_counterpart + pool_writeoff:
                line_ids_commands.append(Command.delete(l.id))

            to_write = {
                'date': pay.date,
                'partner_id': pay.partner_id.id,
                'currency_id': pay.currency_id.id,
                'partner_bank_id': pay.partner_bank_id.id,
                'line_ids': line_ids_commands,
            }
            if 'journal_id' in changed_fields:
                to_write.update({
                    'name': '/',
                    'journal_id': pay.journal_id.id
                })
            pay.move_id.with_context(skip_invoice_sync=True).write(to_write)
