from odoo import models, fields, api
from odoo.exceptions import ValidationError


class FarmRowWizard(models.TransientModel):
    _name = 'farm.row.wizard'
    _description = 'Cərgə Yaratma Sihirbazı'

    # Əsas məlumatlar
    parcel_id = fields.Many2one('farm.parcel', string='Parsel', required=True)
    field_id = fields.Many2one(related='parcel_id.field_id', string='Sahə', readonly=True)
    
    # Cərgə yaratma üsulu
    creation_method = fields.Selection([
        ('single', 'Tək Cərgə'),
        ('multiple', 'Çoxlu Cərgə'),
        ('range', 'Aralıq (məsələn: 1-10)')
    ], string='Yaratma Üsulu', default='single', required=True)
    
    # Tək çərgə üçün
    single_name = fields.Char('Cərgə Adı')
    
    # Çoxlu çərgə üçün
    start_number = fields.Integer('Başlanğıc Nömrə', default=1)
    count = fields.Integer('Cərgə Sayı', default=1)
    name_prefix = fields.Char('Ad Prefiksi', default='Cərgə', help='Məsələn: "Cərgə" -> Cərgə1, Cərgə2, ...')
    
    # Aralıq üçün
    range_start = fields.Integer('Başlanğıc', default=1)
    range_end = fields.Integer('Bitiş', default=10)
    range_prefix = fields.Char('Ad Prefiksi', default='Cərgə')
    
    # Cərgə fiziki məlumatları
    length_meter = fields.Float('Uzunluq (m)', default=100.0)
    tree_spacing = fields.Float('Ağac Məsafəsi (m)', default=3.0)
    variety_id = fields.Many2one('farm.variety', string='Bitki Növü')
    description = fields.Text('Açıqlama')
    
    # Ağac yaratma
    create_trees = fields.Boolean('Ağaclar da yaradılsın', default=False)
    trees_per_row = fields.Integer('Hər Cərgədə Ağac Sayı', default=25)
    tree_variety_id = fields.Many2one('farm.variety', string='Ağac Bitki Növü')

    @api.onchange('creation_method')
    def _onchange_creation_method(self):
        """Yaratma üsulu dəyişdikdə sahələri sıfırla"""
        if self.creation_method == 'single':
            self.count = 1
            self.range_start = 1
            self.range_end = 1
        elif self.creation_method == 'multiple':
            self.single_name = ''
            self.range_start = 1
            self.range_end = 1
        elif self.creation_method == 'range':
            self.single_name = ''
            self.count = 1

    @api.onchange('create_trees')
    def _onchange_create_trees(self):
        """Ağac yaradılacaqsa variety tələb et"""
        if self.create_trees and not self.tree_variety_id:
            self.tree_variety_id = self.variety_id

    @api.constrains('count', 'range_start', 'range_end', 'trees_per_row', 'creation_method')
    def _check_values(self):
        for record in self:
            if record.creation_method == 'multiple' and record.count <= 0:
                raise ValidationError('Cərgə sayı müsbət olmalıdır!')
            if record.creation_method == 'range':
                if record.range_start <= 0 or record.range_end <= 0:
                    raise ValidationError('Aralıq dəyərləri müsbət olmalıdır!')
                if record.range_start > record.range_end:
                    raise ValidationError('Başlanğıc bitiş dəyərindən kiçik olmalıdır!')
            if record.create_trees:
                if record.trees_per_row <= 0:
                    raise ValidationError('Ağac sayı müsbət olmalıdır!')
                if not record.tree_variety_id:
                    raise ValidationError('Ağac yaradılacaqsa bitki növü seçilməlidir!')

    def _check_name_uniqueness(self, names_to_check):
        """Sahədə çərgə adlarının unikallığını yoxla"""
        if not self.parcel_id or not self.parcel_id.field_id:
            return
        
        field_id = self.parcel_id.field_id.id
        for name in names_to_check:
            existing_row = self.env['farm.row'].search([
                ('name', '=', name),
                ('parcel_id.field_id', '=', field_id)
            ])
            if existing_row:
                raise ValidationError(f'Bu sahədə "{name}" adlı çərgə artıq mövcuddur! Fərqli ad seçin.')

    def action_create_rows(self):
        """Cərgələri yarat"""
        self.ensure_one()
        
        if not self.parcel_id:
            raise ValidationError('Parsel seçilməlidir!')
        
        rows_to_create = []
        names_to_check = []
        
        # Yaradılacaq çərgələrin adlarını hazırla
        if self.creation_method == 'single':
            if not self.single_name:
                raise ValidationError('Cərgə adı daxil edilməlidir!')
            names_to_check = [self.single_name]
            # Addan rəqəm çıxar sequence üçün
            import re
            sequence = 1
            match = re.search(r'\d+', self.single_name)
            if match:
                sequence = int(match.group())
            rows_to_create = [{
                'name': self.single_name,
                'sequence': sequence,
                'parcel_id': self.parcel_id.id,
                'length_meter': self.length_meter,
                'tree_spacing': self.tree_spacing,
                'row_variety': self.variety_id.id if self.variety_id else False,
                'description': self.description,
            }]
            
        elif self.creation_method == 'multiple':
            if not self.name_prefix:
                raise ValidationError('Ad prefiksi daxil edilməlidir!')
            for i in range(self.count):
                sequence = self.start_number + i
                name = f"{self.name_prefix}{sequence}"
                names_to_check.append(name)
                rows_to_create.append({
                    'name': name,
                    'sequence': sequence,
                    'parcel_id': self.parcel_id.id,
                    'length_meter': self.length_meter,
                    'tree_spacing': self.tree_spacing,
                    'row_variety': self.variety_id.id if self.variety_id else False,
                    'description': self.description,
                })
                
        elif self.creation_method == 'range':
            if not self.range_prefix:
                raise ValidationError('Ad prefiksi daxil edilməlidir!')
            for i in range(self.range_start, self.range_end + 1):
                name = f"{self.range_prefix}{i}"
                names_to_check.append(name)
                rows_to_create.append({
                    'name': name,
                    'sequence': i,
                    'parcel_id': self.parcel_id.id,
                    'length_meter': self.length_meter,
                    'tree_spacing': self.tree_spacing,
                    'row_variety': self.variety_id.id if self.variety_id else False,
                    'description': self.description,
                })
        
        # Adların unikallığını yoxla
        self._check_name_uniqueness(names_to_check)
        
        # Cərgələri yarat
        created_rows = self.env['farm.row'].create(rows_to_create)
        
        total_trees = 0
        # Ağaclar yaradılacaqsa
        if self.create_trees and self.tree_variety_id:
            for row in created_rows:
                for tree_num in range(1, self.trees_per_row + 1):
                    tree_name = f"{row.name}-A{tree_num}"
                    self.env['farm.tree'].create({
                        'row_id': row.id,
                        'name': tree_name,
                        'variety_id': self.tree_variety_id.id,
                        'status': 'healthy',
                        'description': f'{row.name} çərgəsindəki {tree_num} nömrəli ağac',
                    })
                    total_trees += 1
        
        # Nəticə mesajı
        created_count = len(created_rows)
        message = f"""
        Cərgələr uğurla yaradıldı!
        
        📏 Yaradılan çərgə sayı: {created_count}
        📦 Parsel: {self.parcel_id.name}
        🌾 Sahə: {self.parcel_id.field_id.name}
        """
        
        if self.create_trees:
            message += f"\n🌳 Yaradılan ağac sayı: {total_trees}"
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Uğur!',
                'message': message,
                'type': 'success',
                'sticky': False,
            }
        }