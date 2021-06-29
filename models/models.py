# -*- coding: utf-8 -*-

from odoo import models, fields, api

class po_luarprop(models.Model):
    _inherit = 'purchase.order'

    delivery_status = fields.Selection([('kirim', 'Kirim'), ('kembali', 'Kembali'), ('done', 'Done')],
                                       'Delivery Status')


    # product_id = fields.Many2one('product.product', 'Products')

class po_luarprop_lines(models.Model):
    _inherit = 'purchase.order.line'

    jml_druk = fields.Char("Jml Druk")

    product_category = fields.Char(string="Category", related="product_id.categ_id.name")
    finishing = fields.Selection([('Kirim', 'Kirim'),
                                  ('Waterbase', 'Waterbase'),
                                  ('Waterbase Kilap', 'Waterbase Kilap'),
                                  ('Laminating Gloss', 'Laminating Gloss'),
                                  ('Laminating Doff', 'Laminating Doff'),
                                  ('UV', 'UV'),
                                  ('Spot UV', 'Spot UV'),
                                  ('Spot Pasir', 'Spot Pasir'),
                                  ('OPV', 'OPV'),
                                  ('Laminating Doff + Spot UV', 'Laminating Doff + Spot UV'),
                                  ('Laminasi Duplex', 'Laminasi Duplex'),
                                  ('Laminasi Eflute', 'Laminasi Eflute'),
                                  ('Emboss', 'Emboss'),
                                  ('Klise Emboss', 'Klise Emboss'),
                                  ('Hot Print', 'Hot Print'),
                                  ('Klise Hot Print', 'Klise Hot Print'),
                                  ('Plong', 'Plong'),
                                  ('Pisau Plong', 'Pisau Plong'),
                                  ('Pretel', 'Pretel'),
                                  ('Lem Manual', 'Lem Manual'),
                                  ('Laminasi Karton', 'Laminasi Karton'),
                                  ('Print Digital', 'Print Digital'),
                                  ('Packing','Packing'),
                                  ('Acc', 'Acc'),
                                  ('Vernish Doff', 'Vernish Doff'),
                                  ('Cetak Toko', 'Cetak Toko'),
                                  ('Service', 'Service'),
                                  ('Potong', 'Potong'),
                                  ])
    sides = fields.Selection([('1 Sisi', '1 Sisi'), ('2 Sisi', '2 Sisi')])
    ukuran = fields.Char("Ukuran(PxL)")
    unit = fields.Selection([('pcs','pcs'),
                             ('druk','druk'),
                             ('koli','koli'),
                             ('lbr','lbr'),
                             ('sap','sap')
                             ])

class inv_custom(models.Model):
    _inherit = 'stock.picking'

    no_sj_inv = fields.Char("No SJ Customer",copy=False)


    product_idx = fields.Char(related="move_lines.product_id.name")

    #ordered_qtyx = fields.Char(related="move_lines.ordered_qty")
    #remaining_qtyx = fields.Float(related="move_lines.remaining_qtyx")
    product_qtyx = fields.Float(related="move_lines.product_qty",string="Ordered Quantity")
    product_uomx = fields.Many2one(related="move_lines.product_uom",string="Unit of Measure")
    #qty_donex = fields.Float("Quantity Delivered",related="move_lines.qty_done")

class product_custom(models.Model):
    _inherit = 'product.product'

    product_category = fields.Char(string="Category", related="categ_id.name")



