from odoo import models, fields, api
from odoo.exceptions import ValidationError

class FarmParcel(models.Model):
    _name = 'farm.parcel'
    _description = 'Parsel'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'code'

    name = fields.Char('Parsel Adı', tracking=True)
    code = fields.Char('Parsel Kodu', copy=False, readonly=True)
    
    # Sahə əlaqəsi
    field_id = fields.Many2one('farm.field', string='Sahə', required=True, ondelete='cascade')
    
    # Parsel məlumatları
    parcel_type_id = fields.Many2one('farm.parcel.type', string='Parsel Tipi', tracking=True)
    area_hectare = fields.Float('Parselin Ölçüsü (ha)', default=20.0, tracking=True)
    soil_depth = fields.Float('Torpaq Dərinliyi (cm)', default=30.0, tracking=True)
    irrigation_available = fields.Boolean('Suvarma İmkanı', default=False, tracking=True)

    # Əlaqəli sahələr
    row_ids = fields.One2many('farm.row', 'parcel_id', string='Cərgələr')

    # Statistikalar
    total_rows = fields.Integer('Cərgə Sayı', compute='_compute_statistics')
    total_trees = fields.Integer('Ağac Sayı', compute='_compute_statistics')

    # Əlavə məlumatlar
    description = fields.Text('Açıqlama')
    
    
    @api.depends('row_ids', 'row_ids.tree_ids')
    def _compute_statistics(self):
        for parcel in self:
            parcel.total_rows = len(parcel.row_ids)
            parcel.total_trees = sum(len(row.tree_ids) for row in parcel.row_ids)

    def name_get(self):
        """Override name_get for custom display name"""
        result = []
        for record in self:
            if record.code and record.name:
                name = f"{record.code} - {record.name}"
            elif record.code:
                name = record.code
            elif record.name:
                name = record.name
            else:
                name = 'Yeni Parsel'
            result.append((record.id, name))
        return result

    def _ensure_field_code(self, field):
        """Sahə kodunun mövcudluğunu təmin edir"""
        if not field.code:
            last_field = self.env['farm.field'].search([('code', 'like', 'S%')], order='code desc', limit=1)
            if last_field and last_field.code:
                try:
                    number = int(last_field.code[1:]) + 1
                except ValueError:
                    number = 1
            else:
                number = 1
            field.code = f'S{number}'

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            # Field ID context-dən götür
            if not vals.get('field_id') and self._context.get('default_field_id'):
                vals['field_id'] = self._context.get('default_field_id')
            
            if not vals.get('code') and vals.get('field_id'):
                field = self.env['farm.field'].browse(vals['field_id'])
                self._ensure_field_code(field)
                
                # Parsel kodunu generasiya et
                last_parcel = self.search([
                    ('field_id', '=', field.id),
                    ('code', 'like', f'{field.code}-P%')
                ], order='code desc', limit=1)
                
                if last_parcel and last_parcel.code:
                    try:
                        number = int(last_parcel.code.split('-P')[1]) + 1
                    except (ValueError, IndexError):
                        number = 1
                else:
                    number = 1
                vals['code'] = f'{field.code}-P{number}'
            
            # Default ad ver
            if not vals.get('name') and vals.get('code'):
                vals['name'] = vals['code']
        return super().create(vals_list)

    @api.constrains('area_hectare')
    def _check_area(self):
        for record in self:
            if record.area_hectare <= 0:
                raise ValidationError('Parselin ölçüsü müsbət olmalıdır!')

    # SQL constraints üçün unikal kod təmin edilir
    _sql_constraints = [
        ('code_unique', 'unique(code)', 'Parsel kodu unikal olmalıdır!'),
    ]


class FarmParcelType(models.Model):
    _name = 'farm.parcel.type'
    _description = 'Parsel Tipi'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'code'

    name = fields.Char('Tip Adı', required=True, tracking=True)
    code = fields.Char('Tip Kodu', copy=False, readonly=True)
    fruit_category = fields.Selection([
        ('citrus', 'Sitrus'),
        ('stone_fruit', 'Çəyirdəkli'),
        ('pome_fruit', 'Alma-Armud'),
        ('pomegranate', 'Nar'),
        ('mixed', 'Qarışıq'),
        ('empty', 'Boş'),
        ('other', 'Digər')
    ], string='Meyvə Kateqoriyası', default='mixed', tracking=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('code'):
                # Parsel tip kodu PT001, PT002, PT003... formatında generasiya et
                last_type = self.search([('code', 'like', 'PT%')], order='code desc', limit=1)
                if last_type and last_type.code:
                    try:
                        number = int(last_type.code[2:]) + 1
                        vals['code'] = f'PT{number:03d}'
                    except ValueError:
                        vals['code'] = 'PT001'
                else:
                    vals['code'] = 'PT001'
        return super().create(vals_list)

    _sql_constraints = [
        ('code_unique', 'unique(code)', 'Tip kodu unikal olmalıdır!'),
    ]
