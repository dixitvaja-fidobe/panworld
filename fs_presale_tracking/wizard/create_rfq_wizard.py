from odoo import api, fields, models, _

class PresaleCreateRFQWizard(models.TransientModel):
    _name = 'presale.create.rfq.wizard'
    _description = 'Preview Purchase RFQs'

    presale_tracking_id = fields.Many2one('presale.tracking', required=True)
    summary_ids = fields.One2many('presale.create.rfq.summary', 'wizard_id', string='Planned RFQs')

    def action_confirm_rfq_creation(self):
        self.ensure_one()
        # Call the actual creation logic on the main object
        return self.presale_tracking_id._create_purchase_rfqs_from_grouping()

class PresaleCreateRFQSummary(models.TransientModel):
    _name = 'presale.create.rfq.summary'
    _description = 'Preview Purchase RFQ Summary Line'
    _rec_name = 'vendor_id'

    wizard_id = fields.Many2one('presale.create.rfq.wizard', ondelete='cascade')
    vendor_id = fields.Many2one('res.partner', string='Vendor')
    sourcing_vendor_id = fields.Many2one('res.partner', string='Sourcing Vendor')
    currency_id = fields.Many2one('res.currency', string='Currency')
    line_count = fields.Integer(string='Line Count')
    total_qty = fields.Integer(string='Total Qty')
    amount_total = fields.Float(string='Total Amount')
