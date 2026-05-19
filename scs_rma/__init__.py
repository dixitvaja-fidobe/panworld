# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) Fidobe Solutions LLC.
#
#    For Module Support : dev3@fidobe.com
#
#############################################################################
from . import models
from . import wizard


def pre_init_hook(env):
    warehouse = env.ref("stock.stock_warehouse_comp_rule")
    location = env.ref("stock.stock_location_comp_rule")
    picking = env.ref("stock.stock_location_comp_rule")
    warehouse.domain_force = []
    location.domain_force = []
    picking.domain_force = []

