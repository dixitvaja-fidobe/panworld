# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) Sitaram Solutions (<https://sitaramsolutions.in/>).
#
#    For Module Support : info@sitaramsolutions.in  or Skype : contact.hiren1188
#
##############################################################################

{
    'name': "Stock Picking Cancel",
    'version': "19.0.1.0.0",
    'summary': "This module used to Cancel Incoming and Outgoing Shipment/picking",
    'category': 'Warehouse',
    'description': """
    cancel stock picking
    cancel incoming shipment
    cancel outgoing shipment
    cancel internal shipment
    cancel stock
    cancel delivery
    cancel shipment
    revert shipment
    revert delivery
    """,
    'author': "Sitaram",
    'website': "http://www.sitaramsolutions.in",
    'depends': ['base','stock'],
    'data': [
        'views/inherited_stock_picking.xml'
    ],
    'live_test_url':'https://youtu.be/LIeYgUzo5DE',
    'images': ['static/description/banner.png'],
    "price": 10,
    "currency": 'EUR',
    'demo': [],
    "license": "OPL-1",
    'installable': True,
    'auto_install': False,
}
