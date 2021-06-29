# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.
from odoo import models, fields, osv, api
from odoo.exceptions import Warning
from collections import namedtuple

from dateutil.relativedelta import relativedelta
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT
from odoo.tools.float_utils import float_is_zero, float_compare

class stock_picking(models.Model):
    _inherit = 'stock.picking'

    product_description = fields.Char(related="pack_operation_ids.product_description", string="Description")


    

    def _prepare_pack_ops(self, quants, forced_qties):
        """ Prepare pack_operations, returns a list of dict to give at create """
        # TDE CLEANME: oh dear ...
        valid_quants = quants.filtered(lambda quant: quant.qty > 0)
        _Mapping = namedtuple('Mapping', ('product', 'package', 'owner', 'location', 'location_dst_id'))

        all_products = valid_quants.mapped('product_id') | self.env['product.product'].browse(
            p.id for p in forced_qties.keys()) | self.move_lines.mapped('product_id')
        computed_putaway_locations = dict(
            (product, self.location_dest_id.get_putaway_strategy(product) or self.location_dest_id.id) for product in
            all_products)

        product_to_uom = dict((product.id, product.uom_id) for product in all_products)
        picking_moves = self.move_lines.filtered(lambda move: move.state not in ('done', 'cancel'))
        for move in picking_moves:
            # If we encounter an UoM that is smaller than the default UoM or the one already chosen, use the new one instead.
            if move.product_uom != product_to_uom[move.product_id.id] and move.product_uom.factor > product_to_uom[
                move.product_id.id].factor:
                product_to_uom[move.product_id.id] = move.product_uom
        if len(picking_moves.mapped('location_id')) > 1:
            raise UserError(_('The source location must be the same for all the moves of the picking.'))
        if len(picking_moves.mapped('location_dest_id')) > 1:
            raise UserError(_('The destination location must be the same for all the moves of the picking.'))

        pack_operation_values = []
        # find the packages we can move as a whole, create pack operations and mark related quants as done
        top_lvl_packages = valid_quants._get_top_level_packages(computed_putaway_locations)
        for pack in top_lvl_packages:
            pack_quants = pack.get_content()
            pack_operation_values.append({
                'picking_id': self.id,
                'package_id': pack.id,
                'product_qty': 1.0,
                'location_id': pack.location_id.id,
                'location_dest_id': computed_putaway_locations[pack_quants[0].product_id],
                'owner_id': pack.owner_id.id,
            })
            valid_quants -= pack_quants

        # Go through all remaining reserved quants and group by product, package, owner, source location and dest location
        # Lots will go into pack operation lot object
        qtys_grouped = {}
        lots_grouped = {}
        for quant in valid_quants:
            key = _Mapping(quant.product_id, quant.package_id, quant.owner_id, quant.location_id,
                           computed_putaway_locations[quant.product_id])
            qtys_grouped.setdefault(key, 0.0)
            qtys_grouped[key] += quant.qty
            if quant.product_id.tracking != 'none' and quant.lot_id:
                lots_grouped.setdefault(key, dict()).setdefault(quant.lot_id.id, 0.0)
                lots_grouped[key][quant.lot_id.id] += quant.qty
        # Do the same for the forced quantities (in cases of force_assign or incomming shipment for example)
        for product, qty in forced_qties.items():
            if qty <= 0.0:
                continue
            key = _Mapping(product, self.env['stock.quant.package'], self.owner_id, self.location_id,
                           computed_putaway_locations[product])
            qtys_grouped.setdefault(key, 0.0)
            qtys_grouped[key] += qty

        # Create the necessary operations for the grouped quants and remaining qtys
        Uom = self.env['product.uom']
        product_id_to_vals = {}  # use it to create operations using the same order as the picking stock moves
        for mapping, qty in qtys_grouped.items():
            uom = product_to_uom[mapping.product.id]
            val_dict = {
                'picking_id': self.id,
                'product_qty': mapping.product.uom_id._compute_quantity(qty, uom),
                'product_id': mapping.product.id,
                'package_id': mapping.package.id,
                'owner_id': mapping.owner.id,
                'location_id': mapping.location.id,
                'location_dest_id': mapping.location_dst_id,
                'product_uom_id': uom.id,
                'pack_lot_ids': [
                    (0, 0, {'lot_id': lot, 'qty': 0.0, 'qty_todo': lots_grouped[mapping][lot]})
                    for lot in lots_grouped.get(mapping, {}).keys()],
            }
            product_id_to_vals.setdefault(mapping.product.id, list()).append(val_dict)

        for move in self.move_lines.filtered(lambda move: move.state not in ('done', 'cancel')):

            values = product_id_to_vals.pop(move.product_id.id, [])
            if values and values[0]:
                values[0].update({'product_description': move.product_description})
            pack_operation_values += values

        return pack_operation_values

class stock_pack_operation(models.Model):
    _inherit = 'stock.pack.operation'

    product_description = fields.Char('Product Description')

class procurement_order(models.Model):
    _inherit = 'procurement.order'

    product_description = fields.Char('Product Description')

    def _get_stock_move_values(self):
        ''' Returns a dictionary of values that will be used to create a stock move from a procurement.
        This function assumes that the given procurement has a rule (action == 'move') set on it.

        :param procurement: browse record
        :rtype: dictionary
        '''
        group_id = False
        if self.rule_id.group_propagation_option == 'propagate':
            group_id = self.group_id.id
        elif self.rule_id.group_propagation_option == 'fixed':
            group_id = self.rule_id.group_id.id
        date_expected = (datetime.strptime(self.date_planned, DEFAULT_SERVER_DATETIME_FORMAT) - relativedelta(
            days=self.rule_id.delay or 0)).strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        # it is possible that we've already got some move done, so check for the done qty and create
        # a new move with the correct qty
        qty_done = sum(self.move_ids.filtered(lambda move: move.state == 'done').mapped('product_uom_qty'))
        qty_left = max(self.product_qty - qty_done, 0)
        return {
            'name': self.name,
            'product_description': self.product_description,
            'company_id': self.rule_id.company_id.id or self.rule_id.location_src_id.company_id.id or self.rule_id.location_id.company_id.id or self.company_id.id,
            'product_id': self.product_id.id,
            'product_uom': self.product_uom.id,
            'product_uom_qty': qty_left,
            'partner_id': self.rule_id.partner_address_id.id or (
                        self.group_id and self.group_id.partner_id.id) or False,
            'location_id': self.rule_id.location_src_id.id,
            'location_dest_id': self.location_id.id,
            'move_dest_id': self.move_dest_id and self.move_dest_id.id or False,
            'procurement_id': self.id,
            'rule_id': self.rule_id.id,
            'procure_method': self.rule_id.procure_method,
            'origin': self.origin,
            'picking_type_id': self.rule_id.picking_type_id.id,
            'group_id': group_id,
            'route_ids': [(4, route.id) for route in self.route_ids],
            'warehouse_id': self.rule_id.propagate_warehouse_id.id or self.rule_id.warehouse_id.id,
            'date': date_expected,
            'date_expected': date_expected,
            'propagate': self.rule_id.propagate,
            'priority': self.priority,
        }

class stock_move(models.Model):
    _inherit = 'stock.move'

    product_description = fields.Char(string="Description")

    @api.onchange('product_id')
    def description(self) :
        self.product_description = self.product_id.display_name
    

class purchase_order(models.Model):
    _inherit = 'purchase.order.line'

    @api.multi
    def _create_stock_moves(self, picking):
        moves = self.env['stock.move']
        done = self.env['stock.move'].browse()
        for line in self:
            if line.product_id.type not in ['product', 'consu']:
                continue
            qty = 0.0
            price_unit = line._get_stock_move_price_unit()
            for move in line.move_ids.filtered(lambda x: x.state != 'cancel'):
                qty += move.product_qty
            template = {
                'name': line.name or '',
                'product_description': line.name,
                'product_id': line.product_id.id,
                'product_uom': line.product_uom.id,
                'date': line.order_id.date_order,
                'date_expected': line.date_planned,
                'location_id': line.order_id.partner_id.property_stock_supplier.id,
                'location_dest_id': line.order_id._get_destination_location(),
                'picking_id': picking.id,
                'partner_id': line.order_id.dest_address_id.id,
                'move_dest_id': False,
                'state': 'draft',
                'purchase_line_id': line.id,
                'company_id': line.order_id.company_id.id,
                'price_unit': price_unit,
                'picking_type_id': line.order_id.picking_type_id.id,
                'group_id': line.order_id.group_id.id,
                'procurement_id': False,
                'origin': line.order_id.name,
                'route_ids': line.order_id.picking_type_id.warehouse_id and [
                    (6, 0, [x.id for x in line.order_id.picking_type_id.warehouse_id.route_ids])] or [],
                'warehouse_id': line.order_id.picking_type_id.warehouse_id.id,
            }
            # Fullfill all related procurements with this po line
            diff_quantity = line.product_qty - qty
            for procurement in line.procurement_ids:
                # If the procurement has some moves already, we should deduct their quantity
                sum_existing_moves = sum(x.product_qty for x in procurement.move_ids if x.state != 'cancel')
                existing_proc_qty = procurement.product_id.uom_id._compute_quantity(sum_existing_moves,
                                                                                    procurement.product_uom)
                procurement_qty = procurement.product_uom._compute_quantity(procurement.product_qty,
                                                                            line.product_uom) - existing_proc_qty
                if float_compare(procurement_qty, 0.0, precision_rounding=procurement.product_uom.rounding) > 0:
                    tmp = template.copy()
                    tmp.update({
                        'product_uom_qty': min(procurement_qty, diff_quantity),
                        'move_dest_id': procurement.move_dest_id.id,
                    # move destination is same as procurement destination
                        'procurement_id': procurement.id,
                        'propagate': procurement.rule_id.propagate,
                    })
                    done += moves.create(tmp)
                    diff_quantity -= min(procurement_qty, diff_quantity)
            if float_compare(diff_quantity, 0.0, precision_rounding=line.product_uom.rounding) > 0:
                template['product_uom_qty'] = diff_quantity
                done += moves.create(template)
        return done








