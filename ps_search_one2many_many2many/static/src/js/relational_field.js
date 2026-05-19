/** @odoo-module **/


import { registry } from "@web/core/registry";
import { SectionAndNoteFieldOne2Many, sectionAndNoteFieldOne2Many } from "@account/components/section_and_note_fields_backend/section_and_note_fields_backend";
import { useState, onMounted, onPatched, onWillUpdateProps } from "@odoo/owl";

export class PsSearchOption extends SectionAndNoteFieldOne2Many {
    setup() {
        super.setup();
        this.rowCount = useState({
            total: 0,
            visible: 0
        });

        // Initial count after mount
        onMounted(() => {
            this.updateRowCount();
        });

        // Update count when props will change
        onWillUpdateProps((nextProps) => {
            this.onPropsUpdated(nextProps);
        });

        // Update count after DOM has been patched
        onPatched(() => {
            this.updateRowCount();
        });
    }

    /**
     * Called when props are updated
     * @param {Object} nextProps - The incoming props
     */
    onPropsUpdated(nextProps) {
        // Check if the relational data has changed
        const currentData = this.props?.record?.data?.[this.props.name];
        const nextData = nextProps?.record?.data?.[nextProps.name];

        if (currentData !== nextData) {
            // Data has changed, schedule a count update after render
            setTimeout(() => this.updateRowCount(), 0);
        }
    }


    updateRowCount() {
        let rows = document.querySelectorAll(".o_list_table tr");
        let totalRows = 0;
        let visibleRows = 0;

        rows.forEach((row, index) => {
            if (index === 0) return; // Skip header row

            // Skip section and note rows - only count actual data rows
            if (row.classList.contains('o_is_line_section') ||
                row.classList.contains('o_is_line_note') ||
                row.classList.contains('o_is_line_subsection') ||
                !row.classList.contains('o_data_row')) {
                return;
            }

            totalRows++;
            if (row.style.display !== "none") {
                visibleRows++;
            }
        });

        this.rowCount.total = totalRows;
        this.rowCount.visible = visibleRows;
    }

    onInputKeyUp(event) {
        let value = event.currentTarget.value.toLowerCase();
        let rows = document.querySelectorAll(".o_list_table tr");

        rows.forEach((row, index) => {
            if (index === 0) return;
            let text = row.textContent.toLowerCase();
            let isMatch = text.includes(value);
            row.style.display = isMatch ? "" : "none";
        });

        this.updateRowCount();
    }
}

PsSearchOption.template = "PsSearchOptionTemplate";

export const SearchOption = {
    ...sectionAndNoteFieldOne2Many,
    component: PsSearchOption,
};

registry.category("fields").add("search_section_and_note_one2many", SearchOption);
