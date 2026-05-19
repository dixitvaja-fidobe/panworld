/** @odoo-module **/

import { Component, onWillStart, onMounted, useRef, useState } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { loadBundle } from "@web/core/assets";

export class PresaleDashboard extends Component {
    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.state = useState({
            summary: {},
            status_dist: [],
            chart: {},
            tables: { customers: [], vendors: [], recent: [] }
        });
        this.chartRef = useRef("chart");

        onWillStart(async () => {
            await this.fetchData();
        });

        onMounted(async () => {
            await loadBundle("web.chartjs_lib");
            this.renderChart();
        });
    }

    async fetchData() {
        const data = await this.orm.call("presale.tracking", "get_dashboard_data", []);
        this.state.summary = data.summary;
        this.state.chart = data.chart;
        this.state.tables = data.tables;
    }

    renderChart() {
        if (!this.chartRef.el) return;

        const config = {
            type: 'line',
            data: {
                labels: this.state.chart.labels,
                datasets: [{
                    label: 'Monthly Revenue',
                    data: this.state.chart.datasets[0].data,
                    fill: true,
                    borderColor: '#3b82f6', // Bright Blue
                    backgroundColor: 'rgba(59, 130, 246, 0.2)',
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { position: 'bottom' }
                },
                scales: {
                    y: { beginAtZero: true }
                }
            }
        };

        new Chart(this.chartRef.el, config);
    }

    openPresale(id) {
        this.action.doAction({
            type: 'ir.actions.act_window',
            res_model: 'presale.tracking',
            res_id: id,
            views: [[false, 'form']],
            target: 'current'
        });
    }
}

PresaleDashboard.template = "fs_presale_tracking.PresaleDashboard";

registry.category("actions").add("presale_dashboard", PresaleDashboard);
