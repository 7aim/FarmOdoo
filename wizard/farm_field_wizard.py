from odoo import models, fields, api
from odoo.exceptions import ValidationError


class FarmFieldWizard(models.TransientModel):
    _name = 'farm.field.wizard'
    _description = 'Avto Sahə'

    # Sahə məlumatları
    field_name = fields.Char('Sahə Adı', required=True)
    
    # Parsel məlumatları
    parcel_count = fields.Integer('Parsel Sayı', default=1, required=True)
    area_per_parcel = fields.Float('Hər Parselin Ölçüsü (ha)', default=20.0, required=True)
    max_trees_per_row = fields.Integer('Cərgədə Maksimum Ağac Sayı', default=30, required=True)
    
    # Cərgə məlumatları
    rows_per_parcel = fields.Integer('Hər Parseldə Cərgə Sayı', default=10, required=True)
    row_length = fields.Float('Cərgə Uzunluğu (m)', default=100.0, required=True)
    tree_spacing = fields.Float('Ağac Məsafəsi (m)', default=3.0, required=True)
    
    # Ağac məlumatları
    create_trees = fields.Boolean('Ağaclar da yaradılsın', default=True)
    variety_id = fields.Many2one('farm.variety', string='Sort', help='Bütün ağaclar üçün sort (Ağac yaradılacaqsa məcburidir)')
    trees_per_row = fields.Integer('Hər Cərgədə Ağac Sayı', default=25, required=True)
    
    # Digər məlumatlar
    soil_depth = fields.Float('Torpaq Dərinliyi (cm)', default=30.0)
    irrigation_available = fields.Boolean('Suvarma İmkanı', default=False)
    
    # Hesablanmış sahələr
    total_rows = fields.Integer('Cəmi Cərgə Sayı', compute='_compute_totals', store=False)
    total_trees = fields.Integer('Cəmi Ağac Sayı', compute='_compute_totals', store=False)
    estimated_area = fields.Float('Təxmini Sahə (ha)', compute='_compute_totals', store=False)
    
    @api.depends('parcel_count', 'rows_per_parcel', 'trees_per_row', 'area_per_parcel')
    def _compute_totals(self):
        for record in self:
            record.total_rows = record.parcel_count * record.rows_per_parcel
            record.total_trees = record.total_rows * record.trees_per_row if record.create_trees else 0
            record.estimated_area = record.parcel_count * record.area_per_parcel
    
    @api.constrains('parcel_count', 'rows_per_parcel', 'trees_per_row', 'max_trees_per_row', 'create_trees', 'variety_id')
    def _check_values(self):
        for record in self:
            if record.parcel_count <= 0:
                raise ValidationError('Parsel sayı müsbət olmalıdır!')
            if record.rows_per_parcel <= 0:
                raise ValidationError('Cərgə sayı müsbət olmalıdır!')
            if record.trees_per_row <= 0:
                raise ValidationError('Ağac sayı müsbət olmalıdır!')
            if record.trees_per_row > record.max_trees_per_row:
                raise ValidationError('Ağac sayı maksimum ağac sayından çox ola bilməz!')
            if record.area_per_parcel <= 0:
                raise ValidationError('Parsel ölçüsü müsbət olmalıdır!')
            if record.create_trees and not record.variety_id:
                raise ValidationError('Ağac yaradılacaqsa sort seçilməlidir!')

    def action_create_field(self):
        """Sahə və bütün strukturunu yarat"""
        self.ensure_one()
        
        # 1. Sahəni yarat
        field = self.env['farm.field'].create({
            'name': self.field_name,
            'description': f'Sihirbaz ilə yaradılmış sahə - {self.parcel_count} parsel, {self.rows_per_parcel} cərgə/parsel'
        })
        
        total_trees = 0
        
        # Bütün sahədəki son ağac nömrəsini tap
        last_tree = self.env['farm.tree'].search([], order='tree_id desc', limit=1)
        tree_counter = 1
        if last_tree and last_tree.tree_id:
            try:
                # Son ağacın nömrəsini götür (məsələn: S1-P1-C1-A5 -> 5)
                parts = last_tree.tree_id.split('-A')
                if len(parts) == 2:
                    tree_counter = int(parts[1]) + 1
            except (ValueError, IndexError):
                tree_counter = 1
        
        # 2. Parselləri yarat
        for parcel_num in range(1, self.parcel_count + 1):
            parcel = self.env['farm.parcel'].create({
                'field_id': field.id,
                'name': f'Parsel {parcel_num}',
                'area_hectare': self.area_per_parcel,
                'max_trees_per_row': self.max_trees_per_row,
                'soil_depth': self.soil_depth,
                'irrigation_available': self.irrigation_available,
            })
            
            # 3. Cərgələri yarat
            for row_num in range(1, self.rows_per_parcel + 1):
                row = self.env['farm.row'].create({
                    'parcel_id': parcel.id,
                    'name': f'Cərgə {row_num}',
                    'length_meter': self.row_length,
                    'tree_spacing': self.tree_spacing,
                })
                
                # 4. Ağacları yarat (əgər seçilibsə)
                if self.create_trees:
                    if not self.variety_id:
                        raise ValidationError('Ağac yaradılacaqsa sort seçilməlidir!')
                    
                    for tree_num in range(1, self.trees_per_row + 1):
                        # Unikal tree_id generasiya et
                        tree_id = f'{row.code}-A{tree_counter}'
                        tree_vals = {
                            'row_id': row.id,
                            'tree_id': tree_id,
                            'name': tree_id,
                            'field_id': field.id,
                            'status': 'healthy',
                            'variety_id': self.variety_id.id,
                        }
                        
                        self.env['farm.tree'].create(tree_vals)
                        total_trees += 1
                        tree_counter += 1
        
        # Nəticə mesajı
        message = f"""
        Sahə uğurla yaradıldı!
        
        📍 Sahə: {field.name} ({field.code})
        📦 Parsel sayı: {self.parcel_count}
        📏 Cərgə sayı: {self.parcel_count * self.rows_per_parcel}
        """
        
        if self.create_trees:
            message += f"🌳 Ağac sayı: {total_trees}"
        
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
