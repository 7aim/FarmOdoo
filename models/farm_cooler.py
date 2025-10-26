from odoo import models, fields, api
from odoo.exceptions import ValidationError


class FarmCooler(models.Model):
    _name = 'farm.cooler'
    _description = 'Soyuducu'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'cooler_code'

    name = fields.Char('Soyuducu Adı')
    cooler_code = fields.Char('Soyuducu Kodu', copy=False, readonly=True)
    
    # Tutum məlumatları
    capacity_kg = fields.Float('Tutum (kq)', default=5.0)

    # Temperatura nəzarət
    target_temperature = fields.Float('Hədəf Temperatura (°C)', default=4.0)
    current_temperature = fields.Float('Hazırkı Temperatura (°C)')

    # Status
    status = fields.Selection([
        ('active', 'Aktiv'),
        ('passive', 'Passiv')
    ], string='Status', default='active', required=True)

    def name_get(self):
        """Override name_get for custom display name"""
        result = []
        for record in self:
            if record.cooler_code and record.name:
                name = f"{record.cooler_code} - {record.name}"
            elif record.cooler_code:
                name = record.cooler_code
            elif record.name:
                name = record.name
            else:
                name = 'Yeni Soyuducu'
            result.append((record.id, name))
        return result

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('cooler_code'):
                # Soyuducu kodu SOY001, SOY002, SOY003... formatında generasiya et
                last_cooler = self.search([('cooler_code', 'like', 'SOY%')], order='cooler_code desc', limit=1)
                if last_cooler and last_cooler.cooler_code:
                    try:
                        # "SOY001" formatından nömrəni çıxar
                        number = int(last_cooler.cooler_code.replace('SOY', '')) + 1
                        vals['cooler_code'] = f'SOY{number:03d}'
                    except ValueError:
                        vals['cooler_code'] = 'SOY001'
                else:
                    vals['cooler_code'] = 'SOY001'

            # Default ad ver
            if not vals.get('name') and vals.get('cooler_code'):
                vals['name'] = vals['cooler_code']
        return super().create(vals_list)

    @api.constrains('capacity_kg')
    def _check_capacity(self):
        for record in self:
            if record.capacity_kg <= 0:
                raise ValidationError('Tutum müsbət olmalıdır!')

    @api.constrains('target_temperature')
    def _check_temperature(self):
        for record in self:
            if record.target_temperature < -50 or record.target_temperature > 50:
                raise ValidationError('Temperatura -50°C ilə 50°C arasında olmalıdır!')

    # SQL constraints
    _sql_constraints = [
        ('cooler_code_unique', 'unique(cooler_code)', 'Soyuducu kodu unikal olmalıdır!'),
    ]
