from odoo import models, fields, api


class FarmDiseaseType(models.Model):
    _name = 'farm.disease.type'
    _description = 'Xəstəlik Səbəbi'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'category, name'

    name = fields.Char('Xəstəlik/Zərərverici Adı')
    code = fields.Char('Xəstəlik/Zərərverici Kodu', copy=False, readonly=True)

    # Kateqoriya
    category = fields.Selection([
        ('pest', 'Zərərverici'),
        ('disease', 'Xəstəlik')
    ], string='Kateqoriya', required=True)
    
    # Zərərverici növləri
    pest_type = fields.Selection([
        ('aphid', 'Afid'),
        ('mite', 'Qırpız'),
        ('caterpillar', 'Tırtıl'),
        ('scale', 'Qabıqlı bit'),
        ('thrips', 'Trips'),
        ('other_pest', 'Digər zərərverici')
    ], string='Zərərverici Tipi')
    
    # Xəstəlik növləri
    disease_type = fields.Selection([
        ('fungal', 'Göbələk'),
        ('bacterial', 'Bakteriya'),
        ('viral', 'Virus'),
        ('physiological', 'Fizioloji'),
        ('other_disease', 'Digər xəstəlik')
    ], string='Xəstəlik Tipi')
    
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
                name = 'Yeni Xəstəlik'
            result.append((record.id, name))
        return result

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('code'):
                # Xəstəlik kodu XS001, XS002, XS003... formatında generasiya et
                last_disease = self.search([('code', 'like', 'XS%')], order='code desc', limit=1)
                if last_disease and last_disease.code:
                    try:
                        # "XS001" formatından nömrəni çıxar
                        number = int(last_disease.code.replace('XS', '')) + 1
                        vals['code'] = f'XS{number:03d}'
                    except ValueError:
                        vals['code'] = 'XS001'
                else:
                    vals['code'] = 'XS001'
            
            # Default ad ver
            if not vals.get('name') and vals.get('code'):
                vals['name'] = vals['code']
        return super().create(vals_list)

    _sql_constraints = [
        ('code_unique', 'unique(code)', 'Xəstəlik kodu unikal olmalıdır!'),
    ]


class FarmDiseaseRecord(models.Model):
    _name = 'farm.disease.record'
    _description = 'Xəstəlik Qeydi'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'detection_date desc'

    name = fields.Char('Qeyd Adı', compute='_compute_name', store=True, readonly=True)
    
    # Ağac əlaqəsi
    tree_id = fields.Many2one('farm.tree', string='Ağac', required=True, ondelete='cascade')
    row_id = fields.Many2one(related='tree_id.row_id', string='Cərgə', store=True, readonly=True)
    parcel_id = fields.Many2one(related='tree_id.parcel_id', string='Parsel', store=True, readonly=True)
    field_id = fields.Many2one(related='tree_id.field_id', string='Sahə', store=True, readonly=True)
    
    # Xəstəlik məlumatları
    disease_type_id = fields.Many2one('farm.disease.type', string='Xəstəlik/Zərərverici', required=True, tracking=True)
    detection_date = fields.Datetime('Təyin Tarixi', required=True, default=fields.Datetime.now, tracking=True)

    # Zərər səviyyəsi
    damage_level = fields.Selection([
        ('low', 'Aşağı'),
        ('medium', 'Orta'),
        ('high', 'Yüksək'),
        ('critical', 'Kritik')
    ], string='Zərər Səviyyəsi', default='low', tracking=True)

    # Status
    status = fields.Selection([
        ('detected', 'Aşkar edildi'),
        ('treatment_started', 'Müalicə başlandı'),
        ('under_treatment', 'Müalicə davam edir'),
        ('recovered', 'Sağaldı'),
        ('chronic', 'Xroniki')
    ], string='Status', default='detected', required=True, tracking=True)

    description = fields.Text('Qeydlər')

    @api.depends('tree_id', 'disease_type_id', 'detection_date')
    def _compute_name(self):
        for record in self:
            if record.tree_id and record.disease_type_id and record.detection_date:
                record.name = f"{record.tree_id.tree_id} - {record.disease_type_id.name} ({record.detection_date})"
            else:
                record.name = 'Yeni Xəstəlik Qeydi'
