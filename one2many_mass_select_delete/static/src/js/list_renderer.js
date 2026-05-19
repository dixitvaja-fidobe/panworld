/** @odoo-module */
import { patch } from "@web/core/utils/patch";
import { X2ManyField } from "@web/views/fields/x2many/x2many_field";
import { ListRenderer } from "@web/views/list/list_renderer";
import { StaticList } from "@web/model/relational_model/static_list";
import { useService } from "@web/core/utils/hooks";
import { _t } from "@web/core/l10n/translation";
import { ConfirmationDialog } from "@web/core/confirmation_dialog/confirmation_dialog";

console.log(">>> [DEBUG] one2many_mass_delete: Initializing Global Patches...");

/**
 * FIX: 'TypeError: list.toggleSelection is not a function'
 * Odoo 19's StaticList (used in X2Many) lacks selection management methods
 * because standard X2Many lists don't have checkboxes.
 * We patch StaticList to support these methods safely.
 */
patch(StaticList.prototype, {
    get selection() {
        // Return records that have the 'selected' flag set
        return this.records.filter((record) => record.selected);
    },

    toggleSelection() {
        // Toggles selection for all records on the current page
        const allSelected = this.selection.length === this.records.length;
        this.records.forEach((record) => {
            record._toggleSelection(!allSelected);
        });
    }
});

// 1. Logic Patch for X2ManyField to enable the selectors and mass delete buttons
patch(X2ManyField.prototype, {
    setup() {
        super.setup(...arguments);
        this.dialog = useService("dialog");
        this.notification = useService("notification");
    },

    get rendererProps() {
        const props = super.rendererProps;
        // Aggressively enable checkboxes for list view when not readonly
        if (this.props.viewMode === 'list' && !this.props.readonly) {
            props.allowSelectors = true;
            if (!props.activeActions) props.activeActions = {};
            props.activeActions.delete = true;
        }
        return props;
    },

    get hasSelected() {
        return this.list.selection && this.list.selection.length > 0;
    },

    async deleteSelected() {
        const selected = this.list.selection;
        if (!selected || !selected.length) {
            return this.notification.add(_t("No records selected"), { type: "warning" });
        }

        this.dialog.add(ConfirmationDialog, {
            title: _t("Delete Selected Entries?"),
            body: _t("Are you sure you want to delete the selected entries? The unselected ones will be kept."),
            confirm: async () => {
                const toDelete = [...selected];
                for (const rec of toDelete) {
                    await this.list.delete(rec);
                }
            },
        });
    },

    async deleteUnselected() {
        const allRecords = this.list.records;
        const selectedIds = new Set(this.list.selection.map(r => r.id));
        const unselected = allRecords.filter(r => !selectedIds.has(r.id));

        if (!unselected.length) {
            return this.notification.add(_t("No unselected records"), { type: "warning" });
        }

        this.dialog.add(ConfirmationDialog, {
            title: _t("Keep Selected Entries?"),
            body: _t("Are you sure you want to delete all unselected entries? Only the selected ones will be kept."),
            confirm: async () => {
                const toDelete = [...unselected];
                for (const rec of toDelete) {
                    await this.list.delete(rec);
                }
            },
        });
    }
});
