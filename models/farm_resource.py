from odoo import models, fields

class FarmResource(models.Model):
    _name = 'farm.resource'
    _description = 'Farm Resource'

    name = fields.Char(string='Vəsait Adı', required=True)
    
    # Vəsait növü
    asset_type = fields.Selection([
        ('machinery', 'Texnikalar'),
        ('irrigation_equipment', 'Suvarma Avadanlıqları'),
        ('buildings', 'Bina və Tikililər'),
        ('movable_property', 'Daşınar Əmlaklar'),
        ('perennial_plants', 'Çoxillik Bitkilər'),
        ('other', 'Digər')
    ], string='Vəsait Növü', required=True, default='machinery')
    
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