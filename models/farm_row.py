from odoo import models, fields, api
from odoo.exceptions import ValidationError


class FarmRow(models.Model):
    _name = 'farm.row'
    _description = 'Cərgə'
    _order = 'code'

    name = fields.Char('Cərgə Adı')
    code = fields.Char('Cərgə Kodu', copy=False, readonly=True)
    
    # Parsel əlaqəsi
    parcel_id = fields.Many2one('farm.parcel', string='Parsel', required=True, ondelete='cascade')
    field_id = fields.Many2one(related='parcel_id.field_id', string='Sahə', store=True, readonly=True)
    
    # Statistikalar
    tree_count = fields.Integer('Ağac Sayı', compute='_compute_tree_count')
    
    # Fiziki məlumatlar
    length_meter = fields.Float('Uzunluq (m)', default=100.0)
    tree_spacing = fields.Float('Məsafə (m)', default=3.0)

    # Əlaqəli sahələr
    tree_ids = fields.One2many('farm.tree', 'row_id', string='Ağaclar')
    
    # Status
    description = fields.Text('Açıqlama')

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
                name = 'Yeni Cərgə'
            result.append((record.id, name))
        return result

    @api.depends('tree_ids')
    def _compute_tree_count(self):
        for record in self:
            record.tree_count = len(record.tree_ids)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            # Parcel ID context-dən götür
            if not vals.get('parcel_id') and self._context.get('default_parcel_id'):
                vals['parcel_id'] = self._context.get('default_parcel_id')
            
            if not vals.get('code') and vals.get('parcel_id'):
                parcel = self.env['farm.parcel'].browse(vals['parcel_id'])
                
                if not parcel.code:
                    raise ValidationError('Parsel kodu olmayan bir parseldə cərgə yarada bilməzsiniz!')
                
                # Cərgə kodunu generasiya et
                last_row = self.search([
                    ('parcel_id', '=', parcel.id),
                    ('code', 'like', f'{parcel.code}-C%')
                ], order='code desc', limit=1)
                
                if last_row and last_row.code:
                    try:
                        number = int(last_row.code.split('-C')[1]) + 1
                    except (ValueError, IndexError):
                        number = 1
                else:
                    number = 1
                
                vals['code'] = f'{parcel.code}-C{number}'
            
            # Default ad ver
            if not vals.get('name') and vals.get('code'):
                vals['name'] = vals['code']
        return super().create(vals_list)

    # SQL constraints üçün unikal kod təmin edilir  
    _sql_constraints = [
        ('code_unique', 'unique(code)', 'Cərgə kodu unikal olmalıdır!'),
    ]
