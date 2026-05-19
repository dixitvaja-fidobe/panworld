{
    'name': 'Presale Tracking',
    'version': '19.0.1.0.0',
    'category': 'Sales',
    'summary': 'Track presales with vendor pricing comparison and margin analysis',
    'description': """
        Presale Tracking Module
        =======================
        
        This module allows you to:
        - Import book/product data via CSV (ISBN, Title, Qty)
        - Track vendor pricing and compare margins
        - Analyze profit margins before finalizing vendors
        - Export CSV templates for easy data entry
    """,
    'author': 'Mvorks',
    'website': 'https://www.mvorks.com',
    'depends': ['base', 'contacts', 'mail', 'sale', 'panworld_products', 'purchase', 'panworld_purchase', 'board', 'fs_sale_project_tracking', 'sale_purchase_inter_company_rules'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/sequence.xml',
        'views/presale_tracking_views.xml',
        'views/sale_order_views.xml',
        'views/product_supplierinfo_views.xml',
        'views/purchase_order_views.xml',
        'wizard/import_csv_wizard_views.xml',
        'wizard/import_vendor_pricelist_wizard_views.xml',
        'wizard/create_rfq_views.xml',
        'wizard/link_rfq_views.xml',
        'wizard/sale_order_create_rfq_wizard_views.xml',
        'views/res_company_views.xml',
        'views/res_users_views.xml',
        # 'views/vendor_pricelist_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'fs_presale_tracking/static/src/scss/presale_style.scss',
            'fs_presale_tracking/static/src/js/presale_dashboard.js',
            'fs_presale_tracking/static/src/xml/presale_dashboard.xml',
        ],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}

