# -*- coding: utf-8 -*-
{
    "name": "Panworld Stock Excel Report",
    "summary": "Generate current stock report for all locations and warehouses in Excel format.",
    "version": "19.0.1.0.0",
    "category": "Inventory/Reporting",
    "license": "LGPL-3",
    "author": "Antigravity",
    "depends": ["stock", "report_xlsx"],
    "data": [
        "security/ir.model.access.csv",
        "wizard/stock_excel_report_wizard_view.xml",
        "report/report_actions.xml",
    ],
    "installable": True,
    "application": False,
}
