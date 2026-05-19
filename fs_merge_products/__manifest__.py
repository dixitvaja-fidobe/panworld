{
    'name': 'Merge Products',
    'version': '19.0.1.0.0',
    'summary': 'Merge multiple products into one (Odoo 19)',
    'description': """
        This module allows you to merge multiple products into a single product.
        It transfers all related data (inventory, sales, purchases, etc.) to the destination product.
        Optimized for Odoo 19 Enterprise.
    """,
    'author': 'Fidobe Solutions',
    'website': 'https://www.fidobe.com',
    'category': 'Inventory/Product',
    'depends': [
        'product',
        'stock',
        'sale',
        'purchase',
        'account',
        'stock_account',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/product_views.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}