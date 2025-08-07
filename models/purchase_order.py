from odoo import models, fields, api


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    farm_field_id = fields.Many2one('farm.field', string='Sahə')


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    stock_qty_available = fields.Float(
        string='Anbarda Mövcud',
        compute='_compute_stock_qty_available',
        help='Bu məhsuldan anbarda mövcud olan miqdar'
    )
    
    product_weight = fields.Float(
        string='Çəki (kg)',
        related='product_id.weight',
        readonly=True,
        help='Məhsulun vahid çəkisi'
    )

    @api.depends('product_id')
    def _compute_stock_qty_available(self):
        for line in self:
            if line.product_id:
                line.stock_qty_available = line.product_id.qty_available
            else:
                line.stock_qty_available = 0
    

