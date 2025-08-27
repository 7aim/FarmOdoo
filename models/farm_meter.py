from odoo import models, fields, api

class FarmMeter(models.Model):
    _name = 'farm.meter'
    _description = 'Sayğac'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Sayğac adı', required=True, tracking=True)
    serial_number = fields.Char(string='Seriya nömrəsi', tracking=True)
    capacity_liters = fields.Float(string='Tutum (litr)', tracking=True)
    
    installation_date = fields.Date(string='Quraşdırılma tarixi', tracking=True)
    location = fields.Char(string='Yerləşdiyi yer', tracking=True)
    description = fields.Text(string='Açıqlama')