from odoo import models, fields, api
from odoo.exceptions import ValidationError


class FarmRow(models.Model):
    _name = 'farm.row'
    _description = 'Cərgə'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'sequence desc'

    name = fields.Char('Cərgə Adı')
    code = fields.Char('Cərgə Kodu', copy=False, readonly=True)
    sequence = fields.Integer('Sıra', default=1, help='Cərgələrin sıralanması üçün')
    row_variety = fields.Many2one('farm.variety', string='Cərgə Bitki Növü', ondelete='cascade')

    # Sahə və Parsel əlaqəsi
    field_id = fields.Many2one('farm.field', string='Sahə', required=True)
    parcel_id = fields.Many2one('farm.parcel', string='Parsel', required=True, ondelete='cascade', 
                               domain="[('field_id', '=', field_id)]")
    
    # Statistikalar
    tree_count = fields.Integer('Ağac Sayı', compute='_compute_tree_count')
    
    # Fiziki məlumatlar
    length_meter = fields.Float('Uzunluq (m)', default=100.0)
    tree_spacing = fields.Float('Məsafə (m)', default=3.0)
    max_trees = fields.Integer('Maksimum Ağac Sayı', help='Bu cərgədə maksimum neçə ağac ola bilər', compute='_compute_default_max_trees', store=True, readonly=False)

    # Əlaqəli sahələr
    tree_ids = fields.One2many('farm.tree', 'row_id', string='Ağaclar')
    
    # Status
    description = fields.Text('Açıqlama')

    @api.onchange('field_id')
    def _onchange_field_id(self):
        """Sahə dəyişəndə parseli sıfırla və domain filtrləri"""
        if self.field_id:
            self.parcel_id = False
            return {'domain': {'parcel_id': [('field_id', '=', self.field_id.id)]}}
        else:
            return {'domain': {'parcel_id': []}}

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

    @api.constrains('name', 'parcel_id')
    def _check_unique_name_in_field(self):
        """Eyni sahədə cərgə adları unikal olmalıdır"""
        for record in self:
            if record.name and record.parcel_id and record.parcel_id.field_id:
                field_id = record.parcel_id.field_id.id
                existing_row = self.search([
                    ('name', '=', record.name),
                    ('parcel_id.field_id', '=', field_id),
                    ('id', '!=', record.id)
                ])
                if existing_row:
                    raise ValidationError(f'Bu sahədə "{record.name}" adlı cərgə artıq mövcuddur! Fərqli ad seçin.')

    @api.model_create_multi
    def create(self, vals_list):
        # Parsel əsaslı kod sayğacı
        parcel_code_counters = {}
        
        for vals in vals_list:
            # Parcel ID context-dən götür
            if not vals.get('parcel_id') and self._context.get('default_parcel_id'):
                vals['parcel_id'] = self._context.get('default_parcel_id')
            
            if vals.get('parcel_id'):
                parcel = self.env['farm.parcel'].browse(vals['parcel_id'])
                
                if not parcel.code:
                    raise ValidationError('Parsel kodu olmayan bir parseldə cərgə yarada bilməzsiniz!')
                
                # Sıra nömrəsini təyin et (addan müstəqil)
                if not vals.get('sequence'):
                    # Adından rəqəm çıxar display üçün
                    if vals.get('name'):
                        import re
                        match = re.search(r'\d+', vals['name'])
                        if match:
                            vals['sequence'] = int(match.group())
                        else:
                            # Eger adında rəqəm yoxdursa, son sıra + 1
                            last_row = self.search([('parcel_id', '=', parcel.id)], order='sequence desc', limit=1)
                            vals['sequence'] = (last_row.sequence if last_row else 0) + 1
                
                # Cərgə kodunu generasiya et (sadə artan nömrə 1,2,3...)
                if not vals.get('code'):
                    # Batch yaradılarkən eyni parsel üçün sayğacı artır
                    if parcel.id not in parcel_code_counters:
                        # İlk dəfə bu parsel üçün mövcud sayı tap
                        existing_count = self.search_count([('parcel_id', '=', parcel.id)])
                        parcel_code_counters[parcel.id] = existing_count
                    
                    # Sayğacı artır və kod generasiya et
                    parcel_code_counters[parcel.id] += 1
                    row_number = parcel_code_counters[parcel.id]
                    vals['code'] = f'{parcel.code}-C{row_number}'
            
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

    # SQL constraints üçün unikal kod və sahədə unikal ad təmin edilir  
    _sql_constraints = [
        ('code_unique', 'unique(code)', 'Cərgə kodu unikal olmalıdır!'),
    ]
