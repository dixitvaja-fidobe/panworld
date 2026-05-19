{
    'name': 'Panworld Smart Buttons',
    'version': '1.0',
    'category': 'Customization',
    'summary': 'Smart buttons to view lines in list views for Invoices, Sales, Purchase, and Pickings',
    'author': 'Fidobe Solutions LLC',
    'depends': ['account', 'sale_management', 'purchase', 'stock', 'panworld_account', 'panworld_sale', 'panworld_purchase', 'panworld_stock'],
    'data': [
        'views/account_move_views.xml',
        'views/sale_order_views.xml',
        'views/purchase_order_views.xml',
        'views/stock_picking_views.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
