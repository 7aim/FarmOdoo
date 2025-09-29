from odoo import models, fields, api
from odoo.exceptions import ValidationError


class FarmTree(models.Model):
    _name = 'farm.tree'
    _description = 'Ağac'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'tree_id'

    name = fields.Char('Ağac Adı', tracking=True)
    tree_id = fields.Char('Ağac kodu', copy=False, readonly=True)

    # Cərgə əlaqəsi
    row_id = fields.Many2one('farm.row', string='Cərgə', required=True, ondelete='cascade')
    parcel_id = fields.Many2one(related='row_id.parcel_id', string='Parsel', store=True, readonly=True)
    field_id = fields.Many2one(related='row_id.field_id', string='Sahə', store=True, readonly=True)
    
    # Ağac məlumatları
    variety_id = fields.Many2one('farm.variety', string='Bitki Növü', required=True, tracking=True)
    sort_id = fields.Many2one('farm.sort', string='Bitki Sortu', tracking=True)
    rootstock = fields.Char(string='Calaqaltı', tracking=True)

    # Tarixi məlumatlar
    planting_date = fields.Date('Əkin Tarixi' , default=fields.Date.today, tracking=True)
    season_count = fields.Integer('Mövsüm Sayı (il)', store=True, tracking=True)
    
    # Status
    status = fields.Selection([
        ('healthy', 'Sağlam'),
        ('sick', 'Xəstə'),
        ('dead', 'Ölü'),
        ('removed', 'Silinmiş')
    ], string='Status', default='healthy', required=True)
    
    # Xəstəlik əlaqəsi
    disease_ids = fields.One2many('farm.disease.record', 'tree_id', string='Xəstəlik Qeydləri')
    
    # Əlavə məlumatlar
    description = fields.Text('Açıqlama')

    @api.onchange('variety_id')
    def _onchange_variety_id(self):
        """Bitki növü dəyişdikdə sortu sıfırla"""
        self.sort_id = False

    @api.onchange('variety_id', 'sort_id')
    def _filter_sorts(self):
        """Yalnız seçilmiş bitki növünə aid olan sortları göstər"""
        if self.variety_id:
            return {'domain': {'sort_id': [('id', 'in', self.variety_id.variety_name.ids)]}}
        return {'domain': {'sort_id': []}}

    def name_get(self):
        """Override name_get for custom display name"""
        result = []
        for record in self:
            if record.tree_id and record.name:
                name = f"{record.tree_id} - {record.name}"
            elif record.tree_id:
                name = record.tree_id
            elif record.name:
                name = record.name
            else:
                name = 'Yeni Ağac'
            result.append((record.id, name))
        return result

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            # Row ID context-dən götür
            if not vals.get('row_id') and self._context.get('default_row_id'):
                vals['row_id'] = self._context.get('default_row_id')
            
            if vals.get('row_id'):
                row = self.env['farm.row'].browse(vals['row_id'])
                
                if not row.code:
                    raise ValidationError('Cərgə kodu olmayan bir cərgədə ağac yarada bilməzsiniz!')
                
                # Ağac kodunu generasiya et
                if not vals.get('tree_id'):
                    # Bu cərgədəki bütün ağacları tap
                    existing_trees = self.search([('row_id', '=', row.id)])
                    existing_codes = existing_trees.mapped('tree_id')
                    
                    # Bu cərgə üçün növbəti nömrəni tap
                    counter = 1
                    while True:
                        new_code = f'{row.code}-A{counter}'
                        if new_code not in existing_codes:
                            vals['tree_id'] = new_code
                            break
                        counter += 1
            
            # Default ad ver
            if not vals.get('name') and vals.get('tree_id'):
                vals['name'] = vals['tree_id']
        
        return super().create(vals_list)

    # @api.depends('planting_date')
    # def _compute_season_count(self):
    #     from datetime import date
    #     for record in self:
    #         if record.planting_date:
    #             current_year = date.today().year
    #             planting_year = record.planting_date.year
    #             record.season_count = max(0, current_year - planting_year)
    #         else:
    #             record.season_count = 0

    # SQL constraints üçün unikal ağac ID təmin edilir
    _sql_constraints = [
        ('tree_id_unique', 'unique(tree_id)', 'Ağac ID unikal olmalıdır!'),
    ]