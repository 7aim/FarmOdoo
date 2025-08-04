from odoo import models, fields, api
from odoo.exceptions import ValidationError

class FarmField(models.Model):
    _name = 'farm.field'
    _description = 'Sahə (Field)'
    _order = 'code'

    name = fields.Char('Sahə Adı', required=True)
    code = fields.Char('Sahə Kodu', copy=False, readonly=True)
    
    # Yer məlumatları
    district = fields.Selection([
        ('absheron', 'Abşeron'),
        ('agadash', 'Ağdaş'),
        ('agdam', 'Ağdam'),
        ('agjabadi', 'Ağcabədi'),
        ('agstafa', 'Ağstafa'),
        ('agsu', 'Ağsu'),
        ('astara', 'Astara'),
        ('baku', 'Bakı'),
        ('babek', 'Babək'),
        ('balakan', 'Balakən'),
        ('barda', 'Bərdə'),
        ('beylagan', 'Beyləqan'),
        ('bilasuvar', 'Biləsuvar'),
        ('dashkasan', 'Daşkəsən'),
        ('davachi', 'Şabran'),
        ('fizuli', 'Füzuli'),
        ('gakh', 'Qax'),
        ('gandja', 'Gəncə'),
        ('goranboy', 'Goranboy'),
        ('goychay', 'Göyçay'),
        ('goygol', 'Göygöl'),
        ('guba', 'Quba'),
        ('gusar', 'Qusar'),
        ('hajigabul', 'Hacıqabul'),
        ('imtishad', 'İmişli'),
        ('ismayilli', 'İsmayıllı'),
        ('jabrayil', 'Cəbrayıl'),
        ('jalilabad', 'Cəlilabad'),
        ('julfa', 'Culfa'),
        ('kalbajar', 'Kəlbəcər'),
        ('kangarli', 'Kəngərli'),
        ('kurdamir', 'Kürdəmir'),
        ('lacin', 'Laçın'),
        ('lerik', 'Lerik'),
        ('lankaran', 'Lənkəran'),
        ('masalli', 'Masallı'),
        ('mingachevir', 'Mingəçevir'),
        ('naftalan', 'Naftalan'),
        ('neftchala', 'Neftçala'),
        ('oguz', 'Oğuz'),
        ('ordubad', 'Ordubad'),
        ('qabala', 'Qəbələ'),
        ('qakh', 'Qax'),
        ('qazakh', 'Qazax'),
        ('qobustan', 'Qobustan'),
        ('quba', 'Quba'),
        ('qusar', 'Qusar'),
        ('saatli', 'Saatlı'),
        ('sabirabad', 'Sabirabad'),
        ('shaki', 'Şəki'),
        ('shamakhi', 'Şamaxı'),
        ('shamkir', 'Şəmkir'),
        ('sharur', 'Şərur'),
        ('shatakh', 'Şahbuz'),
        ('shirvan', 'Şirvan'),
        ('shusha', 'Şuşa'),
        ('siazan', 'Siyəzən'),
        ('sumgait', 'Sumqayıt'),
        ('terter', 'Tərtər'),
        ('tovuz', 'Tovuz'),
        ('ughuz', 'Uğuz'),
        ('ujaar', 'Ucar'),
        ('yardimli', 'Yardımlı'),
        ('yevlakh', 'Yevlax'),
        ('zagatala', 'Zaqatala'),
        ('zardab', 'Zərdab'),
        ('nakhchivan', 'Naxçıvan'),
        ('khizi', 'Xızı'),
        ('khachmaz', 'Xaçmaz'),
        ('khojali', 'Xocalı'),
        ('khojavend', 'Xocavənd'),
        ('gazakh', 'Qazax'),
        ('salyan', 'Salyan'),
        ('other', 'Digər')
    ], string='Rayonlar', required=True, default='baku')
    village = fields.Char('Kənd')
    gps_latitude = fields.Float('GPS Enlemi', digits=(10, 6), default=40.712776)
    gps_longitude = fields.Float('GPS Uzunluğu', digits=(10, 6), default=-74.005974)

    # Sahənin ölçüsü və məlumatları
    area_hectare = fields.Float('Sahənin Ölçüsü (Hektar)', default=40.0)
    soil_type = fields.Selection([
        ('clay', 'Gil'),
        ('sandy', 'Qumlu'),
        ('loamy', 'Gillicə'),
        ('mixed', 'Qarışıq'),
        ('other', 'Digər')
    ], string='Torpaq Tipi', default='mixed')

    # Status
    status = fields.Selection([
        ('active', 'Aktiv'),
        ('passive', 'Passiv')
    ], string='Status', default='active', required=True)
    active = fields.Boolean('Aktiv', store=True, default=True)
    
    # Əlaqəli sahələr
    parcel_ids = fields.One2many('farm.parcel', 'field_id', string='Parsellər')
    
    # Statistikalar
    total_parcel = fields.Integer('Parsel Sayı', compute='_compute_statistics')
    total_rows = fields.Integer('Cərgə Sayı', compute='_compute_statistics')
    total_trees = fields.Integer('Ağac Sayı', compute='_compute_statistics')
    
    # Əlavə məlumatlar
    description = fields.Text('Açıqlama')

    @api.onchange('active')
    def _onchange_active(self):
        if self.active:
            self.status = 'active'
        else:
            self.status = 'passive'
    
    @api.depends('parcel_ids', 'parcel_ids.row_ids', 'parcel_ids.row_ids.tree_ids')
    def _compute_statistics(self):
        for field in self:
            field.total_parcel = len(field.parcel_ids)
            field.total_rows = sum(len(parcel.row_ids) for parcel in field.parcel_ids)
            field.total_trees = sum(len(row.tree_ids) for parcel in field.parcel_ids for row in parcel.row_ids)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('code'):
                # Sahə kodu S1, S2, S3... formatında generasiya et
                last_field = self.search([('code', 'like', 'S%')], order='code desc', limit=1)
                if last_field and last_field.code:
                    try:
                        number = int(last_field.code[1:]) + 1
                    except ValueError:
                        number = 1
                else:
                    number = 1
                vals['code'] = f'S{number}'
        return super().create(vals_list)

    @api.constrains('area_hectare')
    def _check_area(self):
        for record in self:
            if record.area_hectare <= 0:
                raise ValidationError('Sahənin ölçüsü müsbət olmalıdır!')

    # SQL constraints üçün unikal kod təmin edilir
    _sql_constraints = [
        ('code_unique', 'unique(code)', 'Sahə kodu unikal olmalıdır!'),
    ]
