import { PosOrder } from "@point_of_sale/app/models/pos_order";
import { PosStore } from "@point_of_sale/app/services/pos_store";
import { patch } from "@web/core/utils/patch";

patch(PosOrder.prototype, {
    setup(vals) {
        super.setup(...arguments);
        if (typeof vals.to_invoice === "undefined" && this.config?.canInvoice) {
            this.to_invoice = true;
        }
    }
});

patch(PosStore.prototype, {
    createNewOrder(data = {}) {
        const order = super.createNewOrder(data);
        const configDefaultCustomer = this.config.default_customer_id || this.config.raw?.default_customer_id;
        
        if (configDefaultCustomer && !order.getPartner()) {
            let partner = configDefaultCustomer;
            if (Array.isArray(configDefaultCustomer)) {
                partner = this.models["res.partner"].get(configDefaultCustomer[0]);
            } else if (typeof configDefaultCustomer === 'object' && configDefaultCustomer.id) {
                partner = this.models["res.partner"].get(configDefaultCustomer.id) || configDefaultCustomer;
            } else if (typeof configDefaultCustomer === 'number') {
                partner = this.models["res.partner"].get(configDefaultCustomer);
            }
            if (partner) {
                try {
                    order.setPartner(partner);
                } catch (e) {
                    order.partner_id = partner;
                }
            }
        }
        return order;
    }
});
