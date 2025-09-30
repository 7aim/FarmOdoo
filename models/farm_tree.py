from odoo import models, fields, api
from odoo.exceptions import ValidationError


class FarmTree(models.Model):
    _name = 'farm.tree'
    _description = 'Ağac'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'sequence desc'

    name = fields.Char('Ağac Adı', tracking=True)
    tree_id = fields.Char('Ağac kodu', copy=False, readonly=True)
    sequence = fields.Integer('Sıra', default=1, help='Ağacların sıralanması üçün')

    # Sahə, Parsel və Cərgə əlaqəsi
    field_id = fields.Many2one('farm.field', string='Sahə', required=True, tracking=True)
    parcel_id = fields.Many2one('farm.parcel', string='Parsel', required=True, tracking=True,
                               domain="[('field_id', '=', field_id)]")
    row_id = fields.Many2one('farm.row', string='Cərgə', required=True, ondelete='cascade',
                            domain="[('parcel_id', '=', parcel_id)]")
    
    # Ağac məlumatları
    variety_id = fields.Many2one('farm.variety', string='Bitki Növü', required=True, tracking=True)
    sort_id = fields.Many2one('farm.sort', string='Bitki Sortu', tracking=True)
    rootstock = fields.Many2one('farm.rootstock', string='Çalaqaltı', tracking=True)

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

    @api.onchange('field_id')
    def _onchange_field_id(self):
        """Sahə dəyişdirildikdə parseli sıfırla və domain tətbiq et"""
        if self.field_id:
            self.parcel_id = False
            self.row_id = False
            return {'domain': {'parcel_id': [('field_id', '=', self.field_id.id)]}}
        else:
            self.parcel_id = False
            self.row_id = False
            return {'domain': {'parcel_id': []}}

    @api.onchange('parcel_id')
    def _onchange_parcel_id(self):
        """Parsel dəyişdirildikdə cərgəni sıfırla və domain tətbiq et"""
        if self.parcel_id:
            self.row_id = False
            return {'domain': {'row_id': [('parcel_id', '=', self.parcel_id.id)]}}
        else:
            self.row_id = False
            return {'domain': {'row_id': []}}

    @api.constrains('name', 'row_id')
    def _check_unique_name_in_field(self):
        """Eyni sahədə ağac adları unikal olmalıdır"""
        for record in self:
            if record.name and record.row_id and record.row_id.parcel_id and record.row_id.parcel_id.field_id:
                field_id = record.row_id.parcel_id.field_id.id
                existing_tree = self.search([
                    ('name', '=', record.name),
                    ('row_id.parcel_id.field_id', '=', field_id),
                    ('id', '!=', record.id)
                ])
                if existing_tree:
                    raise ValidationError(f'Bu sahədə "{record.name}" adlı ağac artıq mövcuddur! Fərqli ad seçin.')

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
        # Cərgə əsaslı kod sayğacı
        row_code_counters = {}
        
        for vals in vals_list:
            # Row ID context-dən götür
            if not vals.get('row_id') and self._context.get('default_row_id'):
                vals['row_id'] = self._context.get('default_row_id')
            
            if vals.get('row_id'):
                row = self.env['farm.row'].browse(vals['row_id'])
                
                if not row.code:
                    raise ValidationError('Cərgə kodu olmayan bir cərgədə ağac yarada bilməzsiniz!')
                
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
                            last_tree = self.search([('row_id', '=', row.id)], order='sequence desc', limit=1)
                            vals['sequence'] = (last_tree.sequence if last_tree else 0) + 1
                
                # Ağac kodunu generasiya et (sadə artan nömrə 1,2,3...)
                if not vals.get('tree_id'):
                    # Batch yaradılarkən eyni cərgə üçün sayğacı artır
                    if row.id not in row_code_counters:
                        # İlk dəfə bu cərgə üçün mövcud sayı tap
                        existing_count = self.search_count([('row_id', '=', row.id)])
                        row_code_counters[row.id] = existing_count
                    
                    # Sayğacı artır və kod generasiya et
                    row_code_counters[row.id] += 1
                    tree_number = row_code_counters[row.id]
                    vals['tree_id'] = f'{row.code}-A{tree_number}'
            
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