import { PaymentScreen } from "@point_of_sale/app/screens/payment_screen/payment_screen";
import { patch } from "@web/core/utils/patch";
import { onMounted } from "@odoo/owl";

patch(PaymentScreen.prototype, {
    setup() {
        super.setup(...arguments);
        onMounted(() => {
            if (this.pos.config.canInvoice && !this.currentOrder.isToInvoice()) {
                this.currentOrder.setToInvoice(true);
            }
        });
    }
});
