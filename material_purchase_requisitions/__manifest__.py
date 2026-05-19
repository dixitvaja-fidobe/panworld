# -*- coding: utf-8 -*-

# Part of Probuse Consulting Service Pvt Ltd. See LICENSE file for full copyright and licensing details.

{
    'name': 'Product/Material Purchase Requisitions by Employees/Users',
    'version': '2.7.6',
    'price': 79.0,
    'currency': 'EUR',
    'license': 'Other proprietary',
    'summary': """This module allow your employees/users to create Purchase Requisitions. (Internal Transfer Removed - Purchase Orders Only)""",
    'description': """
    Material Purchase Requisitions - Purchase Order Only
    
    **MODIFIED VERSION**: Internal transfer/picking functionality has been removed. 
    This module now supports ONLY Purchase Order creation.
    
    This module allows Purchase requisition of employees.
Purchase_Requisition_Via_iProcurement
Purchase Requisitions
Purchase Requisition
iProcurement
Online Requisitions
Issue Enforcement
Inventory Replenishment Requisitions
Replenishment Requisitions
MRP Generated Requisitions
generated Requisitions
purchase Sales Orders
Complete Requisitions Status Visibility
Using purchase Requisitions
purchase requisitions
replenishment requisitions
employee Requisition
employee purchase Requisition
user Requisition
product Requisition
item Requisition
material Requisition
product Requisitions
material purchase Requisition
material Requisition purchase
purchase material Requisition
product purchase Requisition
item Requisitions
material Requisitions
products Requisitions
purchase Requisition Process
Approving or Denying the purchase Requisition
Denying purchase Requisition​
construction management
real estate management
construction app
Requisition
Requisitions
indent management
indent
indent request
indent order
odoo indent
* INHERIT hr.department.form.view (form)
* INHERIT hr.employee.form.view (form)
purchase.requisition search (search)
purchase.requisition.form.view (form)
purchase.requisition.view.list (list)
purchase_requisition (qweb)

Main Features:
✓ Allow your employees to Create Purchase Requisition
✓ Employees can request multiple material/items on single purchase Requisition request
✓ Multi-level Approval Workflow:
  - Store Approval
  - Purchase Approval
  - Finance Approval
  - Management Approval
✓ Email notifications to approvers at each level
✓ Purchase Requisitions will create Purchase Orders/RFQs to selected vendors
✓ Multiple purchase orders can be created from single requisition
✓ Analytic account tracking

**REMOVED Features**:
✗ Internal Picking/Transfer functionality removed
✗ Stock warehouse dispatch removed
✗ Requisition Action selection removed (only Purchase Order supported)


    """,
    'author': 'Probuse Consulting Service Pvt. Ltd.',
    'website': 'http://www.probuse.com',
    'support': 'contact@probuse.com',
    'images': ['static/description/img1.jpeg'],
    #'live_test_url': 'https://youtu.be/1AgKs7gfe4M',
    'live_test_url': 'http://probuseappdemo.com/probuse_apps/material_purchase_requisitions/304',#'https://youtu.be/byR2cM0c274',
    'category': 'Warehouse',
    'depends': [
                'stock',
                'hr',
                'purchase',
                'account',
                'base'
                ],
    'data':[
        'security/security.xml',
        'security/multi_company_security.xml',
        'security/ir.model.access.csv',
        'data/purchase_requisition_sequence.xml',
        'data/employee_purchase_approval_template.xml',
        'data/confirm_template_material_purchase.xml',
        'report/purchase_requisition_report.xml',
        'views/purchase_order_views.xml',
        'views/purchase_requisition_view.xml',
        # 'views/hr_employee_view.xml',
        # 'views/hr_department_view.xml',

        # 'views/stock_picking_view.xml', # Removed - internal transfer not supported
    ],
    'installable' : True,
    'application' : False,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
