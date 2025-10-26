from odoo import models, fields

class FarmDocument(models.Model):
    _name = 'farm.document'
    _description = 'Farm Document'

    name = fields.Char(string='Sənəd Adı', required=True)
    image = fields.Binary(string='Sənəd')
    note = fields.Text(string='Qeyd')
    area_id = fields.Many2one('farm.field', string='Sahə', required=True, ondelete='cascade')