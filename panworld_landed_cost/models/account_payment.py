from odoo import models, fields

class AccountPayment(models.Model):
    _inherit = "account.payment"

    is_landed_cost_payment = fields.Boolean("Is Landed Cost Payment", default=False)
    landed_cost_ids = fields.Many2many(
        "stock.landed.cost",
        relation="account_payment_landed_cost_rel",
        column1="payment_id",
        column2="landed_cost_id",
        string="Related Landed Costs",
        readonly=True,
        copy=False
    )

    def action_post(self):
        res = super(AccountPayment, self).action_post()
        for payment in self:
            if payment.landed_cost_ids:
                payment.landed_cost_ids.write({'is_payment_paid': True})
        return res
