/** @odoo-module **/

import { _t } from "@web/core/l10n/translation";
import { patch } from "@web/core/utils/patch";
import { url } from "@web/core/utils/urls";
import { session } from "@web/session";
import LineComponent from '@stock_barcode/components/line';
import MainComponent from '@stock_barcode/components/main';

// Patch LineComponent to add manual quantity change functionality
patch(LineComponent.prototype, {
    addQuantityChange(ev) {
        const input = ev.target;
        const qty = input ? input.value : null;
        if (qty !== null && qty !== "") {
            const parsedQty = parseFloat(qty);
            if (!isNaN(parsedQty)) {
                this.env.model.updateLineQty(this.line.virtual_id, parsedQty);
            }
        }
    }
});

// Patch MainComponent to add save button and total scan counter
patch(MainComponent.prototype, {
    async saveProductPage() {
        if (!this._editedLineParams) {
            await this.env.model.save();
        }
    },

    get totalScan() {
        let done_qty = 0;
        let qty_demand = 0;

        // Use currentState.lines to get all lines of the picking, even if on other pages
        const lines = this.env.model.currentState ? this.env.model.currentState.lines : [];
        const seenMoveIds = new Set();

        lines.forEach((line) => {
            const qty = this.env.model.getQtyDone(line);
            done_qty += (typeof qty === 'number' && !isNaN(qty)) ? qty : 0;

            // Use product_uom_qty for demand, assuming one demand per move
            // Deduplicate by move_id to avoid summing the same demand multiple times 
            // if a move is split into multiple lines (e.g. multiple lots)
            if (line.move_id) {
                // move_id can be an ID (int) or Array [id, name] depending on load param
                // In barcode context it is usually just ID from read(load=False)
                const moveId = Array.isArray(line.move_id) ? line.move_id[0] : line.move_id;

                if (!seenMoveIds.has(moveId)) {
                    qty_demand += line.product_uom_qty || 0;
                    seenMoveIds.add(moveId);
                }
            } else {
                // Fallback for lines without move (should be rare in picking)
                qty_demand += line.product_uom_qty || 0;
            }
        });

        // Rounding to avoid floating point issues
        qty_demand = Math.round(qty_demand * 100) / 100;
        done_qty = Math.round(done_qty * 100) / 100;

        return done_qty + "/" + qty_demand;
    },

    // Override playSound to add custom audio notification
    playSound(ev) {
        super.playSound(ev);

        if (!this.config.play_sound || this.state.uiBlocked) {
            return;
        }

        // Play custom ting sound
        if (typeof Audio !== "undefined") {
            const audio = new Audio();
            const ext = audio.canPlayType("audio/ogg; codecs=vorbis") ? ".ogg" : ".mp3";
            audio.src = url("/web_stock_barcode_extra/static/src/audio/ting" + ext);
            audio.play().catch((error) => {
                console.warn("Could not play custom audio:", error);
            });
        }
    }
});
