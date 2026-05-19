# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) Sitaram Solutions (<https://sitaramsolutions.in/>).
#
#    For Module Support : info@sitaramsolutions.in  or Skype : contact.hiren1188
#
##############################################################################

from odoo import fields, models, api, _, Command
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_is_zero


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def picking_reset_to_ready(self):
        self.write({"state": "assigned"})

    def picking_cancel(self):
        """ Cancel the picking and all its moves, even if they are in 'done' state.
        For 'done' moves, we create a reversal move to revert the stock effect.
        """
        for picking in self:
            for move in picking.move_ids:
                if move.state == 'done':
                    # Create a reverse move for each done move to revert stock/valuation impact.
                    # This handles Quants, Stock Valuation Layers, and Account Moves automatically.

                    # Preparing reverse move values
                    reverse_move_vals = {
                        'description_picking': _('Reverse of %s') % (move.reference or move.product_id.display_name),
                        'product_id': move.product_id.id,
                        'product_uom': move.product_uom.id,
                        'product_uom_qty': move.quantity,
                        'location_id': move.location_dest_id.id,
                        'location_dest_id': move.location_id.id,
                        'origin_returned_move_id': move.id,
                        'picking_id': False, # Avoid linking to same picking to prevent state loop
                        'state': 'draft',
                        'company_id': move.company_id.id,
                        'picking_type_id': move.picking_type_id.id,
                        'warehouse_id': move.warehouse_id.id,
                        'procure_method': 'make_to_stock',
                    }
                    reverse_move = self.env['stock.move'].create(reverse_move_vals)

                    # Replicate move lines with reversed locations
                    for line in move.move_line_ids:
                        self.env['stock.move.line'].create({
                            'move_id': reverse_move.id,
                            'product_id': line.product_id.id,
                            'product_uom_id': line.product_uom_id.id,
                            'location_id': line.location_dest_id.id,
                            'location_dest_id': line.location_id.id,
                            'quantity': line.quantity,
                            'lot_id': line.lot_id.id,
                            'package_id': line.package_id.id,
                            'result_package_id': line.result_package_id.id,
                            'owner_id': line.owner_id.id,
                            'picked': True,
                        })

                    # Validate the reversal move
                    reverse_move._action_confirm()
                    reverse_move._action_assign()
                    reverse_move._action_done()

                    # Force the original move to 'cancel' state.
                    # The override in StockMove class allows this for picking moves.
                    move.sudo().write({'state': 'cancel'})
                elif move.state not in ('cancel',):
                    # Standard cancellation for moves that are not yet done
                    move.sudo()._action_cancel()

            # Finally set the picking itself to cancelled
            picking.write({'state': 'cancel'})
        return True


class StockMove(models.Model):
    _inherit = "stock.move"

    def _action_cancel(self):
        """ Override to allow cancelling moves even if they are 'done',
        provided they are linked to a picking (handled by picking_cancel).
        """
        # If not linked to a picking/adjustment, maintain standard restriction on 'done' moves
        moves_to_check = self.filtered(lambda m: not m.picking_id and not m.is_inventory)
        if any(move.state == "done" for move in moves_to_check):
            raise UserError(
                _("You cannot cancel a stock move that has been set to 'Done'.")
            )

        for move in self:
            if move.state == "cancel":
                continue

            # Standard Odoo propagation logic
            move._do_unreserve()
            siblings_states = (
                move.move_dest_ids.mapped("move_orig_ids") - move
            ).mapped("state")

            if move.propagate_cancel:
                if all(state == "cancel" for state in siblings_states):
                    move.move_dest_ids.filtered(
                        lambda m: m.state != "done"
                    )._action_cancel()
            else:
                if all(state in ("done", "cancel") for state in siblings_states):
                    move.move_dest_ids.write({
                        "procure_method": "make_to_stock",
                        "move_orig_ids": [api.Command.unlink(move.id)]
                    })

        # Force state change
        self.write({"state": "cancel", "move_orig_ids": [Command.clear()]})
        return True

    def _do_unreserve(self):
        """ Override to allow unreserving even for 'done' moves if linked to picking. """
        moves_to_unreserve = self.env["stock.move"]
        for move in self:
            if move.state == "cancel":
                continue
            if move.state == "done":
                if move.scrap_id:
                    continue
                # Allow if linked to picking or is inventory adjustment
                if not (move.picking_id or move.is_inventory):
                    raise UserError(
                        _("You cannot unreserve a stock move that has been set to 'Done'.")
                    )
            moves_to_unreserve |= move

        # Unlink move lines (unreserve)
        moves_to_unreserve.with_context(prefetch_fields=False).mapped(
            "move_line_ids"
        ).unlink()
        return True


class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    @api.ondelete(at_uninstall=False)
    def _unlink_except_done_or_cancel(self):
        """ Override to allow unlinking of move lines even if 'done',
        supporting the forced cancellation process.
        """
        pass

    def unlink(self):
        """ Maintain reservation balance when unlinking. """
        precision = self.env["decimal.precision"].precision_get("Product Unit")
        for ml in self:
            if (
                ml.product_id.is_storable
                and not ml.location_id.should_bypass_reservation()
                and not float_is_zero(ml.quantity, precision_digits=precision)
            ):
                try:
                    self.env["stock.quant"]._update_reserved_quantity(
                        ml.product_id,
                        ml.location_id,
                        -ml.quantity,
                        lot_id=ml.lot_id,
                        package_id=ml.package_id,
                        owner_id=ml.owner_id,
                        strict=True,
                    )
                except UserError:
                    if ml.lot_id:
                        # Fallback try without lot if lot unreserve fails
                        self.env["stock.quant"]._update_reserved_quantity(
                            ml.product_id,
                            ml.location_id,
                            -ml.quantity,
                            lot_id=False,
                            package_id=ml.package_id,
                            owner_id=ml.owner_id,
                            strict=True,
                        )
                    else:
                        # If not tracked or already tried lot=False, we might ignore or raise
                        # In forced cancel context, we often ignore unreserve errors
                        pass

        moves = self.mapped("move_id")
        res = super(StockMoveLine, self).unlink()
        if moves:
            moves._recompute_state()
        return res
