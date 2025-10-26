from odoo import models, fields, api
from odoo.exceptions import ValidationError


class FarmPallet(models.Model):
    _name = 'farm.pallet'
    _description = 'Paletlər'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'pallet_code'

    name = fields.Char('Palet Adı')
    pallet_code = fields.Char('Palet Kodu', copy=False, readonly=True)
    
    # Palet tipi
    pallet_type = fields.Selection([
        ('wood', 'Taxta'),
        ('plastic', 'Plastik'),
        ('metal', 'Metal'),
        ('cardboard', 'Karton'),
        ('other', 'Digər')
    ], string='Palet Tipi', default='wood')

    # Həcm məlumatları
    capacity_kg = fields.Float('Həcm (kq)', default=5.0)
    capacity_liter = fields.Float('Həcm (litr)', default=0.0)

    # Status məlumatları
    availability_status = fields.Selection([
        ('empty', 'Boş'),
        ('full', 'Dolu'),
        ('reserved', 'Rezerv'),
        ('maintenance', 'Təmir'),
        ('damaged', 'Zədəli')
    ], string='Mövcudluq', default='empty')

    # Saxlanma yeri
    storage_area = fields.Selection([
        ('field', 'Sahədə'),
        ('warehouse', 'Anbarda'),
        ('cooler', 'Soyuducuda'),
        ('transport', 'Nəqldə'),
        ('other', 'Digər')
    ], string='Saxlanma Sahəsi', default='warehouse')

    # Soyuducu əlaqəsi
    cooler_id = fields.Many2one('farm.cooler', string='Soyuducu')
    
    # Tarixi məlumatlar
    purchase_date = fields.Date('Alınma Tarixi', default=fields.Date.today)
    last_maintenance_date = fields.Date('Son Təmir Tarixi')

    # Əlavə məlumatlar
    description = fields.Text('Açıqlama')
    condition = fields.Selection([
        ('excellent', 'Əla'),
        ('good', 'Yaxşı'),
        ('fair', 'Orta'),
        ('poor', 'Pis'),
        ('damaged', 'Zədəli')
    ], string='Vəziyyət', default='good')

    def name_get(self):
        """Override name_get for custom display name"""
        result = []
        for record in self:
            if record.pallet_code and record.name:
                name = f"{record.pallet_code} - {record.name}"
            elif record.pallet_code:
                name = record.pallet_code
            elif record.name:
                name = record.name
            else:
                name = 'Yeni Palet'
            result.append((record.id, name))
        return result

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('pallet_code'):
                # Palet kodu PL001, PL002, PL003... formatında generasiya et
                last_pallet = self.search([('pallet_code', 'like', 'PL%')], order='pallet_code desc', limit=1)
                if last_pallet and last_pallet.pallet_code:
                    try:
                        # "PL001" formatından nömrəni çıxar
                        number = int(last_pallet.pallet_code.replace('PL', '')) + 1
                        vals['pallet_code'] = f'PL{number:03d}'
                    except ValueError:
                        vals['pallet_code'] = 'PL001'
                else:
                    vals['pallet_code'] = 'PL001'
            
            # Default ad ver
            if not vals.get('name') and vals.get('pallet_code'):
                vals['name'] = vals['pallet_code']
        return super().create(vals_list)

    @api.constrains('capacity_kg')
    def _check_capacity(self):
        for record in self:
            if record.capacity_kg <= 0:
                raise ValidationError('Palet həcmi müsbət olmalıdır!')

    _sql_constraints = [
        ('pallet_code_unique', 'unique(pallet_code)', 'Palet kodu unikal olmalıdır!'),
    ]
