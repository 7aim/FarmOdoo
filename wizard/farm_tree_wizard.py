from odoo import models, fields, api
from odoo.exceptions import ValidationError


class FarmTreeWizard(models.TransientModel):
    _name = 'farm.tree.wizard'
    _description = 'Ağac Yaratma Sihirbazı'

    # Əsas məlumatlar
    field_id = fields.Many2one('farm.field', string='Sahə', required=True)
    parcel_id = fields.Many2one('farm.parcel', string='Parsel', required=True, domain="[('field_id', '=', field_id)]")
    row_id = fields.Many2one('farm.row', string='Cərgə', required=True, domain="[('parcel_id', '=', parcel_id)]")
    
    # Ağac yaratma üsulu
    creation_method = fields.Selection([
        ('single', 'Tək Ağac'),
        ('multiple', 'Çoxlu Ağac'),
        ('range', 'Aralıq (məsələn: 1-25)')
    ], string='Yaratma Üsulu', default='single', required=True)
    
    # Tək ağac üçün
    single_name = fields.Char('Ağac Adı')
    
    # Çoxlu ağac üçün
    start_number = fields.Integer('Başlanğıc Nömrə', default=1)
    count = fields.Integer('Ağac Sayı', default=1)
    name_prefix = fields.Char('Ad Prefiksi', help='Məsələn: "A" -> A1, A2, ... və ya boş buraxsanız avtomatik nömrələnir')
    
    # Aralıq üçün
    range_start = fields.Integer('Başlanğıc', default=1)
    range_end = fields.Integer('Bitiş', default=25)
    range_prefix = fields.Char('Ad Prefiksi', help='Məsələn: "A" -> A1, A2, ...')
    
    # Ağac məlumatları
    variety_id = fields.Many2one('farm.variety', string='Bitki Növü', required=True)
    sort_id = fields.Many2one('farm.sort', string='Bitki Sortu')
    rootstock = fields.Char('Calaqaltı')
    planting_date = fields.Date('Əkin Tarixi', default=fields.Date.today)
    status = fields.Selection([
        ('healthy', 'Sağlam'),
        ('sick', 'Xəstə'),
        ('dead', 'Ölü'),
        ('removed', 'Silinmiş')
    ], string='Status', default='healthy', required=True)
    description = fields.Text('Açıqlama')

    @api.onchange('field_id')
    def _onchange_field_id(self):
        """Sahə dəyişəndə parsel və cərgəni sıfırla"""
        if self.field_id:
            self.parcel_id = False
            self.row_id = False
            return {'domain': {'parcel_id': [('field_id', '=', self.field_id.id)]}}
        else:
            return {'domain': {'parcel_id': [], 'row_id': []}}

    @api.onchange('parcel_id')
    def _onchange_parcel_id(self):
        """Parsel dəyişəndə cərgəni sıfırla"""
        if self.parcel_id:
            self.row_id = False
            return {'domain': {'row_id': [('parcel_id', '=', self.parcel_id.id)]}}
        else:
            return {'domain': {'row_id': []}}

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

    @api.onchange('variety_id')
    def _onchange_variety_id(self):
        """Bitki növü dəyişdikdə sortu sıfırla"""
        self.sort_id = False

    @api.constrains('count', 'range_start', 'range_end', 'creation_method')
    def _check_values(self):
        for record in self:
            if record.creation_method == 'multiple' and record.count <= 0:
                raise ValidationError('Ağac sayı müsbət olmalıdır!')
            if record.creation_method == 'range':
                if record.range_start <= 0 or record.range_end <= 0:
                    raise ValidationError('Aralıq dəyərləri müsbət olmalıdır!')
                if record.range_start > record.range_end:
                    raise ValidationError('Başlanğıc bitiş dəyərindən kiçik olmalıdır!')

    def _check_name_uniqueness(self, names_to_check):
        """Sahədə ağac adlarının unikallığını yoxla"""
        if not self.row_id or not self.row_id.parcel_id or not self.row_id.parcel_id.field_id:
            return
        
        field_id = self.row_id.parcel_id.field_id.id
        for name in names_to_check:
            existing_tree = self.env['farm.tree'].search([
                ('name', '=', name),
                ('row_id.parcel_id.field_id', '=', field_id)
            ])
            if existing_tree:
                raise ValidationError(f'Bu sahədə "{name}" adlı ağac artıq mövcuddur! Fərqli ad seçin.')

    def _generate_tree_name(self, prefix, number):
        """Ağac adı generasiya et"""
        if prefix:
            return f"{prefix}{number}"
        else:
            # Prefix yoxdursa çərgə adı ilə birləşdir
            return f"{self.row_id.name}-A{number}"

    def action_create_trees(self):
        """Ağacları yarat"""
        self.ensure_one()
        
        if not self.row_id:
            raise ValidationError('Cərgə seçilməlidir!')
        
        if not self.variety_id:
            raise ValidationError('Bitki növü seçilməlidir!')
        
        trees_to_create = []
        names_to_check = []
        
        # Yaradılacaq ağacların adlarını hazırla
        if self.creation_method == 'single':
            if not self.single_name:
                raise ValidationError('Ağac adı daxil edilməlidir!')
            names_to_check = [self.single_name]
            trees_to_create = [{
                'name': self.single_name,
                'row_id': self.row_id.id,
                'parcel_id': self.row_id.parcel_id.id,
                'field_id': self.row_id.field_id.id,
                'variety_id': self.variety_id.id,
                'sort_id': self.sort_id.id if self.sort_id else False,
                'rootstock': self.rootstock,
                'planting_date': self.planting_date,
                'status': self.status,
                'description': self.description,
            }]
            
        elif self.creation_method == 'multiple':
            for i in range(self.count):
                sequence = self.start_number + i
                name = self._generate_tree_name(self.name_prefix, sequence)
                names_to_check.append(name)
                trees_to_create.append({
                    'name': name,
                    'row_id': self.row_id.id,
                    'parcel_id': self.row_id.parcel_id.id,
                    'field_id': self.row_id.field_id.id,
                    'variety_id': self.variety_id.id,
                    'sort_id': self.sort_id.id if self.sort_id else False,
                    'rootstock': self.rootstock,
                    'planting_date': self.planting_date,
                    'status': self.status,
                    'description': self.description,
                })
                
        elif self.creation_method == 'range':
            for i in range(self.range_start, self.range_end + 1):
                name = self._generate_tree_name(self.range_prefix, i)
                names_to_check.append(name)
                trees_to_create.append({
                    'name': name,
                    'row_id': self.row_id.id,
                    'parcel_id': self.row_id.parcel_id.id,
                    'field_id': self.row_id.field_id.id,
                    'variety_id': self.variety_id.id,
                    'sort_id': self.sort_id.id if self.sort_id else False,
                    'rootstock': self.rootstock,
                    'planting_date': self.planting_date,
                    'status': self.status,
                    'description': self.description,
                })
        
        # Adların unikallığını yoxla
        self._check_name_uniqueness(names_to_check)
        
        # Cərgədəki maksimum ağac sayını yoxla
        existing_trees_count = len(self.row_id.tree_ids)
        new_trees_count = len(trees_to_create)
        max_trees = self.row_id.max_trees or self.row_id.parcel_id.max_trees_per_row
        
        if existing_trees_count + new_trees_count > max_trees:
            raise ValidationError(f'Bu çərgədə maksimum {max_trees} ağac ola bilər! '
                                f'Hal-hazırda {existing_trees_count} ağac var, '
                                f'{new_trees_count} əlavə etmək istəyirsiniz.')
        
        # Ağacları yarat
        created_trees = self.env['farm.tree'].create(trees_to_create)
        
        # Nəticə mesajı
        created_count = len(created_trees)
        message = f"""
        Ağaclar uğurla yaradıldı!
        
        🌳 Yaradılan ağac sayı: {created_count}
        📏 Cərgə: {self.row_id.name}
        📦 Parsel: {self.row_id.parcel_id.name}
        🌾 Sahə: {self.row_id.parcel_id.field_id.name}
        🌱 Bitki növü: {self.variety_id.name}
        """
        
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