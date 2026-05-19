# -*- coding: utf-8 -*-
{
    'name': 'FS Sale Project Tracking',
    'version': '19.0.1.0.0',
    'category': 'Sales/Project',
    'summary': 'Track Sale Orders through Projects and Purchase Requisitions',
    'description': """
        Sale Project Tracking Module
        =============================
        
        Comprehensive tracking system linking Sales Orders to Projects, Tasks, 
        and Purchase Requisitions with real-time status visibility.
        
        Key Features:
        -------------
        * **Tracking Projects**: Flag projects for sale order tracking
        * **Auto Task Creation**: Automatically create tasks when SO is confirmed
        * **Purchase Requisition Wizard**: Create requisitions from tasks with line review
        * **Centralized Dashboard**: View all statuses (SO, DO, PR, PO) from task
        * **Flexible Requisition**: Select and modify quantities before creating requisition
        
        Workflow:
        ---------
        1. Enable "Sale Tracking" on project
        2. Select tracking project on sale order
        3. Confirm sale order → Task auto-created
        4. From task, create purchase requisition via wizard
        5. Review/modify SO lines in wizard
        6. Create requisition with selected lines
        7. Track all statuses from task dashboard
        
        Status Tracking:
        ----------------
        * Sale Order Status (Draft/Sent/Sale/Done/Cancel)
        * Delivery Order Status (Waiting/Ready/Done)
        * Purchase Requisition Status (Draft/Approved/Rejected)
        * Purchase Order Status (Draft/Purchase/Done)
    """,
    'author': 'Fidobe Solutions LLC',
    'website': 'www.fidobe.com',
    'depends': [
        'sale',
        'project',
        'stock',
        'purchase',
        'material_purchase_requisitions',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/project_project_views.xml',
        'views/sale_order_views.xml',
        'views/project_task_views.xml',
        'views/purchase_order_views.xml',
        'wizard/create_requisition_wizard_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}

