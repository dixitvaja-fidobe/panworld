from odoo import models, api, _

class IrAttachment(models.Model):
    _inherit = 'ir.attachment'

    @api.model
    def unlink(self):
        """Add a line in the chatter to notify about the attachment deletions"""
        for attachment in self:
            if attachment.res_model == 'account.move' and attachment.res_id:
                move = self.env[attachment.res_model].browse(attachment.res_id)
                if move.exists() and hasattr(move, 'message_post'):
                    move.sudo().message_post(
                        subject=_("""Attachment Deleted"""),
                        body=_("""Name : %s""", attachment.name),
                        message_type="comment")
        return super().unlink()

    @api.model_create_multi
    def create(self, vals_list):
        """Add a line in the chatter to notify about attachment creation"""
        attachments = super().create(vals_list)
        for attachment in attachments:
            if attachment.res_model == 'account.move' and attachment.res_id:
                move = self.env[attachment.res_model].browse(attachment.res_id)
                if move and hasattr(move, 'message_post'):
                    move.sudo().message_post(
                        subject=_("Attachment Created"),
                        body=_("Name: %s") % (attachment.name,),
                        message_type="comment",
                    )
        return attachments
