# FS Sale Project Tracking

## Overview
Comprehensive tracking system that links Sales Orders to Projects, Tasks, and Purchase Requisitions, providing real-time visibility of the entire sales-to-procurement workflow.

## Features

### 1. **Tracking Projects**
- Enable "Sale Order Tracking" flag on projects
- Dedicated projects for tracking sales workflows
- Smart button showing number of tracking tasks

### 2. **Sale Order Integration**
- Select tracking project on sale order
- Auto-create tracking task on order confirmation
- Link task to sale order for centralized tracking

### 3. **Task Dashboard**
- View all statuses from one place:
  - **Sale Order Status**: Draft/Sent/Sale/Done/Cancel
  - **Delivery Status**: Waiting/Ready/Partial/Done
  - **Purchase Requisition Status**: Not Created/Draft/Approved/Rejected
  - **Purchase Order Status**: Not Created/Draft/In Progress/Done
- Direct links to view related documents
- Beautiful table layout with icons and status badges

### 4. **Purchase Requisition Wizard**
- Create requisitions directly from tasks
- Review and modify sale order lines
- Select/deselect lines to include
- Adjust quantities before creating requisition
- Add notes and special instructions

### 5. **Complete Traceability**
- Link from Sale Order → Task → Requisition
- Track entire procurement chain
- Audit trail with chatter messages

## Installation

1. Ensure dependencies are installed:
   - `sale` - Sales Management
   - `project` - Project Management
   - `stock` - Inventory
   - `material_purchase_requisitions` - Purchase Requisitions

2. Install the module from Apps menu

## Configuration

### Step 1: Enable Tracking on Project
1. Go to **Project > Projects**
2. Open or create a project
3. Enable **"Sale Order Tracking"** checkbox

### Step 2: Create Sale Order with Tracking
1. Go to **Sales > Orders > Quotations**
2. Create a new quotation
3. Select a **Tracking Project** (only projects with tracking enabled appear)
4. Add products and confirm order
5. A tracking task will be auto-created in the selected project

## Usage

### View Tracking Dashboard
1. Open the tracking task from the project
2. Go to **"Sale Order Tracking"** tab
3. View real-time status of all related documents
4. Click "View" buttons to open related records

### Create Purchase Requisition
1. From the tracking task, click **"Create Purchase Requisition"**
2. Review the sale order lines in the wizard
3. **Select/Deselect** lines using the checkbox
4. **Modify quantities** as needed
5. Add notes if required
6. Click **"Create Requisition"**
7. Requisition is created and linked to the sale order

### Track Status Changes
All status fields are automatically updated when:
- Sale order state changes
- Deliveries are created/validated
- Requisitions are approved
- Purchase orders are confirmed

## Workflow Diagram

```
Sale Order (with Tracking Project)
    ↓ (on confirmation)
Tracking Task Created
    ↓ (user action via wizard)
Purchase Requisition
    ↓ (existing flow)
Purchase Orders
    ↓
Procurement Complete
```

## Status Meanings

### Sale Order Status
- **Draft**: Quotation not sent
- **Sent**: Quotation sent to customer
- **Sale**: Order confirmed
- **Done**: Order fully delivered
- **Cancel**: Order cancelled

### Delivery Status
- **No Delivery**: No delivery orders created
- **Waiting**: Delivery waiting for availability
- **Ready**: Products available, ready to ship
- **Partial (X/Y)**: Some deliveries done
- **Done**: All deliveries completed

### Requisition Status
- **Not Created**: No requisition created yet
- **Draft**: Requisition in draft state
- **Partial (X/Y)**: Some approved, some pending
- **Approved**: All requisitions approved
- **Rejected**: At least one rejected

### Purchase Order Status
- **Not Created**: No POs created from requisition
- **Draft**: POs in draft state
- **In Progress (X/Y)**: Some confirmed/done
- **Done**: All POs completed

## Technical Details

### Models Extended
- `project.project` - Added `sale_tracking` field
- `sale.order` - Added `tracking_project_id` and auto-task creation
- `project.task` - Added tracking dashboard and requisition creation
- `material.purchase.requisition` - Added `fs_sale_order_id` link

### Wizard Models
- `fs.create.requisition.wizard` - Main wizard
- `fs.create.requisition.wizard.line` - Wizard lines

## Benefits

✅ **Centralized Visibility**: All information in one place  
✅ **Process Automation**: Auto-create tasks on order confirmation  
✅ **Flexible Requisitions**: Review and modify before creating  
✅ **Complete Traceability**: Track from sale to procurement  
✅ **Status Monitoring**: Real-time updates across the chain  
✅ **Efficient Workflow**: Reduce manual data entry  

## Version
19.0.1.0.0

## Author
Fidobe Solutions LLC

## License
LGPL-3

