from odoo import models, fields, api


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    farm_field_id = fields.Many2one('farm.field', string='Sahə')
    

