/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { AccountReport } from "@account_reports/components/account_report/account_report";
import { useService } from "@web/core/utils/hooks";

// Save a reference to the original setup
const OriginalSetup = AccountReport.prototype.setup;

patch(AccountReport.prototype, {
    setup() {
        // Call the original setup if it exists
        if (OriginalSetup) {
            OriginalSetup.apply(this, arguments);
        }
        // Add our ORM service
        this.orm = useService("orm");
    },

    async unfold(line) {
        this.odoo_context.is_load_more = false;
        const lineId = line.dataset.id;

        line.classList.toggle("folded");
        this.report_options.unfolded_lines.push(lineId);

        const childLines = this.el.querySelectorAll(
            `tr[data-parent-id="${CSS.escape(String(lineId))}"]`
        );

        if (childLines.length > 0) {
            childLines.forEach(el => {
                el.querySelectorAll(".js_account_report_line_footnote")
                    .forEach(f => f.classList.remove("folded"));
                el.style.display = "";
            });
            const icon = line.querySelector(".o_account_reports_caret_icon .fa-caret-right");
            if (icon) icon.classList.replace("fa-caret-right", "fa-caret-down");
            line.dataset.unfolded = "True";
            this._add_line_classes();
            return true;
        } else {
            const result = await this.orm.call(
                this.report_model,
                "get_html",
                [this.financial_id, this.report_options, lineId],
                { context: this.odoo_context }
            );

            line.parentElement.outerHTML = result;
            this._add_line_classes();

            const displayedTable = this.el.querySelector(
                ".o_account_reports_table:not(#table_header_clone)"
            );
            displayedTable.querySelectorAll(".js_account_report_foldable").forEach(row => {
                if (!row.dataset.unfolded) {
                    this.fold(row);
                }
            });
        }
    },

    async load_more(ev) {
        const td = ev.target.closest("td");
        this.odoo_context.is_load_more = true;

        const id = td.dataset.id;
        const offset = parseInt(td.dataset.offset || 0);
        const progress = parseInt(td.dataset.progress || 0);
        const remaining = parseInt(td.dataset.remaining || 0);

        const options = {
            ...this.report_options,
            lines_offset: offset,
            lines_progress: progress,
            lines_remaining: remaining,
        };

        const result = await this.orm.call(
            this.report_model,
            "get_html",
            [this.financial_id, options, id],
            { context: this.odoo_context }
        );

        const tr = td.closest(".o_account_reports_load_more");
        tr.insertAdjacentHTML("afterend", result);
        tr.remove();
        this._add_line_classes();
    }
});
