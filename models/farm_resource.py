from odoo import models, fields

class FarmResource(models.Model):
    _name = 'farm.resource'
    _description = 'Farm Resource'

    name = fields.Char(string='Vəsait Adı', required=True)
    image = fields.Binary(string='Şəkil')
    note = fields.Text(string='Qeyd')
    area_id = fields.Many2one('farm.field', string='Sahə', required=True, ondelete='cascade')


class FarmResource(models.Model):
    _name = 'farm.tech'
    _description = 'Farm Tech'

    name = fields.Char(string='Texnika Adı', required=True)
    image = fields.Binary(string='Şəkil')
    note = fields.Text(string='Qeyd')
    area_id = fields.Many2one('farm.field', string='Sahə', required=True, ondelete='cascade')