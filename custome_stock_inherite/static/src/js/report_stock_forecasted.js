///** @odoo-module **/
//
//import { registry } from "@web/core/registry";
//import { ReplenishReport } from "@stock/views/replenish_report/replenish_report";
//import { useService } from "@web/core/utils/hooks";
//
//const { Component } = owl;
//
//export class CustomReplenishReport extends ReplenishReport {
//    setup() {
//        super.setup();
//        this.rpc = useService("rpc");
//    }
//
//    async onClickUnreserve(ev) {
//        console.log("-------nikull..........");
//        const model = ev.currentTarget.getAttribute("model");
//        const modelId = parseInt(ev.currentTarget.getAttribute("model-id"));
//
//        await this.rpc("/web/dataset/call_kw", {
//            model,
//            method: "do_unreserve",
//            args: [[modelId]],
//            kwargs: { context: { unreserve_parent: true } },
//        });
//
//        this._reloadReport(); // inherited method from ReplenishReport
//    }
//}
//
//// Register extension into the view registry
//registry.category("views").add("custom_replenish_report", {
//    ...registry.category("views").get("replenish_report"),
//    component: CustomReplenishReport,
//});




//odoo.define('custome_stock_inherite.ReplenishReport', function (require) {
//"use strict";
//
//
//const ReplenishReport = require('stock.ReplenishReport');
//
//console.log(">>>>>>> test...........1",ReplenishReport);
//
//ReplenishReport.include({
//      _onClickUnreserve: function(ev) {
//      console.log("-------nikull..........");
//        const model = ev.target.getAttribute('model');
//        const modelId = parseInt(ev.target.getAttribute('model-id'));
//        return this._rpc( {
//            model,
//            args: [[modelId]],
//            method: 'do_unreserve',
//            context: { unreserve_parent: true },
//        }).then(() => this._reloadReport());
//    },
//})
//});
