<<<<<<< HEAD
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
=======
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
>>>>>>> a7a8fa33fd80e5758bb2299f93b01ef44ee824d5
    description = fields.Text(string='Açıqlama')