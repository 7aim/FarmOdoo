from odoo import models, fields, api

class FarmMeter(models.Model):
    _name = 'farm.meter'
    _description = 'Sayğac'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Sayğac adı', required=True)
    serial_number = fields.Char(string='Seriya nömrəsi')
    capacity_liters = fields.Float(string='Tutum (litr)')
    
    installation_date = fields.Date(string='Quraşdırılma tarixi')
    location = fields.Char(string='Yerləşdiyi yer')
    description = fields.Text(string='Açıqlama')