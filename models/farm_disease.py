from odoo import models, fields, api


class FarmDiseaseType(models.Model):
    _name = 'farm.disease.type'
    _description = 'Xəstəlik Səbəbi'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name'

    name = fields.Char('Zərərverici Adı')
    code = fields.Char('Zərərverici Kodu', copy=False, readonly=True)

    genus_type = fields.Char('Cins', required=True)
    species_type = fields.Char('Növ', required=True)
    latin_name = fields.Char('Latın Adı', required=True)
    group_type = fields.Char('Qrup', required=True)
    
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
    _description = 'Zərərverici qeydi'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'detection_date desc'

    name = fields.Char('Qeyd Adı', compute='_compute_name', store=True, readonly=True)
    
    # Ağac əlaqəsi
    tree_id = fields.Many2one('farm.tree', string='Ağac', required=True, ondelete='cascade')
    row_id = fields.Many2one(related='tree_id.row_id', string='Cərgə', store=True, readonly=True)
    parcel_id = fields.Many2one(related='tree_id.parcel_id', string='Parsel', store=True, readonly=True)
    field_id = fields.Many2one(related='tree_id.field_id', string='Sahə', store=True, readonly=True)
    
    # Xəstəlik məlumatları
    disease_type_id = fields.Many2one('farm.disease.type', string='Zərərverici', required=True)
    detection_date = fields.Datetime('Təyin Tarixi', required=True, default=fields.Datetime.now)

    # Zərər səviyyəsi
    damage_level = fields.Selection([
        ('low', 'Aşağı'),
        ('medium', 'Orta'),
        ('high', 'Yüksək'),
        ('critical', 'Kritik')
    ], string='Zərər Səviyyəsi', default='low')

    # Status
    status = fields.Selection([
        ('detected', 'Aşkar edildi'),
        ('treatment_started', 'Müalicə başlandı'),
        ('under_treatment', 'Müalicə davam edir'),
        ('recovered', 'Sağaldı'),
        ('chronic', 'Xroniki')
    ], string='Status', default='detected', required=True)

    description = fields.Text('Qeydlər')

    @api.depends('tree_id', 'disease_type_id', 'detection_date')
    def _compute_name(self):
        for record in self:
            if record.tree_id and record.disease_type_id and record.detection_date:
                record.name = f"{record.tree_id.tree_id} - {record.disease_type_id.name} ({record.detection_date})"
            else:
                record.name = 'Yeni Zərərverici qeydi'
