# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) Fidobe Solutions LLC.
#
#    For Module Support : dev3@fidobe.com
#
#############################################################################
{
    "name": "Panworld Base",
    "version": "19.0.1.0.0",
    "summary": "Panworld Scope and Customizations",
    "author": "Jumana | Fidobe Solutions",
    "maintainer": "Fidobe Solutions LLC.",
    "website": "www.fidobe.com",
    "license": "LGPL-3",
    "data": [],
    "depends": [
        # Odoo / Enterprise Addons
        "account",
        "sale",
        "purchase",
        "stock",
        "base_import",
        # Paid Addons
        # Public Addons
        "sale_order_line_price_history",
        "account_move_name_sequence",
        "om_mass_confirm_cancel",
        "web_chatter_position",
        # Private Addons
        "panworld_contact",
        "panworld_stock",
        "panworld_products",
        "panworld_purchase",
        "panworld_sale",
        "panworld_landed_cost",
        "panworld_sale_tracker",
        "panworld_expense",
        "panworld_sr_import_partner_product",
        "panworld_import",
        "panworld_bill_lines_update",
        "panworld_sale_import",
        "panworld_kit",
        "panworld_history",
        "panworld_email_configuration",
        "panworld_user_group_email",
        "panworld_saudi_arabic_invoice",
        "panworld_report_layout",
        "panworld_payroll",
        "panworld_payroll_send_mail",
        "pos_stock_info",
        "product_control_policy",
        "custom_email_marketing",
        "custome_stock_inherite",
        "vendor_credit_limit",
        "panworld_report",
        "stock_picking_invoice_link",
        # # "web_stock_barcode_extra",
        "invoice_from_picking_inherit",
        "account_aged_report_extended",
        "account_report_extended",
        "bi_print_journal_entries",
        "bi_sale_purchase_advance_payment",
        "custom_search_multi_value",
        "eq_inventory_valuation_report",
        "eq_stock_ageing_report",
        # "list_view_sticky_header_and_column",
        # "one2many_mass_select_delete",
        # "smtp_by_user_and_company",
        # "user_password_strength",
    ],
    "data": [
        "views/res_company_views.xml",
        "views/res_users_views.xml"
    ],
    "installable": True,
    "auto_install": False,
    "application": False
}
