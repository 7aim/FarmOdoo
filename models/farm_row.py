from odoo import models, fields, api
from odoo.exceptions import ValidationError


class FarmRow(models.Model):
    _name = 'farm.row'
    _description = 'Cərgə'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'code'

    name = fields.Char('Cərgə Adı', tracking=True)
    code = fields.Char('Cərgə Kodu', copy=False, readonly=True)
    
    # Parsel əlaqəsi
    parcel_id = fields.Many2one('farm.parcel', string='Parsel', required=True, ondelete='cascade')
    field_id = fields.Many2one(related='parcel_id.field_id', string='Sahə', store=True, readonly=True)
    
    # Statistikalar
    tree_count = fields.Integer('Ağac Sayı', compute='_compute_tree_count')
    
    # Fiziki məlumatlar
    length_meter = fields.Float('Uzunluq (m)', default=100.0, tracking=True)
    tree_spacing = fields.Float('Məsafə (m)', default=3.0, tracking=True)
    max_trees = fields.Integer('Maksimum Ağac Sayı', tracking=True, help='Bu cərgədə maksimum neçə ağac ola bilər', compute='_compute_default_max_trees', store=True, readonly=False)

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
            
    @api.depends('parcel_id', 'parcel_id.max_trees_per_row')
    def _compute_default_max_trees(self):
        """Parseldəki maksimum ağac sayını götür"""
        for record in self:
            if record.parcel_id:
                record.max_trees = record.parcel_id.max_trees_per_row
            else:
                record.max_trees = 30  # Default dəyər

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            # Parcel ID context-dən götür
            if not vals.get('parcel_id') and self._context.get('default_parcel_id'):
                vals['parcel_id'] = self._context.get('default_parcel_id')
            
            if vals.get('parcel_id'):
                parcel = self.env['farm.parcel'].browse(vals['parcel_id'])
                
                # max_trees artıq compute field olduğundan burada təyin edilməsinə ehtiyac yoxdur
                
                if not parcel.code:
                    raise ValidationError('Parsel kodu olmayan bir parseldə cərgə yarada bilməzsiniz!')
                
                # Cərgə kodunu generasiya et
                if not vals.get('code'):
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

    @api.constrains('max_trees', 'length_meter', 'tree_spacing')
    def _check_row_values(self):
        for record in self:
            if record.max_trees and record.max_trees <= 0:
                raise ValidationError('Maksimum ağac sayı müsbət olmalıdır!')
            if record.length_meter <= 0:
                raise ValidationError('Cərgə uzunluğu müsbət olmalıdır!')
            if record.tree_spacing <= 0:
                raise ValidationError('Ağaclar arası məsafə müsbət olmalıdır!')

    # SQL constraints üçün unikal kod təmin edilir  
    _sql_constraints = [
        ('code_unique', 'unique(code)', 'Cərgə kodu unikal olmalıdır!'),
    ]
