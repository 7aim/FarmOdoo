from odoo import models, fields, api
from odoo.exceptions import ValidationError


class FarmPlowing(models.Model):
    """Şumlama Əməliyyatı"""
    _name = 'farm.plowing'
    _description = 'Şumlama'
    _order = 'operation_date desc'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char('Əməliyyat Adı', required=True, default='Şumlama', tracking=True)
    operation_date = fields.Datetime('Tarix', required=True, default=fields.Datetime.now, tracking=True)

    # Sahə və Parsel
    field_id = fields.Many2one('farm.field', string='Sahə', required=False, ondelete='cascade', tracking=True)
    parcel_id = fields.Many2one('farm.parcel', string='Parsel', domain="[('field_id', '=', field_id)]", ondelete='cascade', tracking=True)
    
    # Texniki məlumatlar
    equipment = fields.Char('Texnika/İcrakar', required=False, tracking=True)
    plowing_depth = fields.Float('Şumlama Dərinliyi (cm)', default=5.0, required=True, tracking=True)
    area_hectare = fields.Float('Genişlik (ha)', default=10.0, required=True, tracking=True)

    # İşçi məlumatları
    operator_id = fields.Many2one('res.partner', string='Operator', domain="[('category_id.name', '=', 'Operator')]", tracking=True)
    worker_line_ids = fields.One2many('farm.plowing.worker', 'plowing_id', string='İşçi Sətirləri')
    total_worker_cost = fields.Float('Ümumi İşçi Xərci', compute='_compute_total_worker_cost', store=True)
    notes = fields.Text('Qeydlər')
    cost = fields.Float('Xərc')

    @api.depends('worker_line_ids.amount')
    def _compute_total_worker_cost(self):
        for record in self:
            record.total_worker_cost = sum(line.amount for line in record.worker_line_ids)

    @api.constrains('plowing_depth', 'area_hectare')
    def _check_positive_values(self):
        for record in self:
            if record.plowing_depth <= 0:
                raise ValidationError('Şumlama dərinliyi müsbət olmalıdır!')
            if record.area_hectare <= 0:
                raise ValidationError('Genişlik müsbət olmalıdır!')


class FarmPlanting(models.Model):
    """Əkin Əməliyyatı"""
    _name = 'farm.planting'
    _description = 'Əkin'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'planting_date desc'

    name = fields.Char('Əməliyyat Adı', required=True, default='Əkin', tracking=True)
    planting_date = fields.Datetime('Əkin Tarixi', required=True, default=fields.Datetime.now, tracking=True)

    # Parsel və Cərgə
    parcel_id = fields.Many2one('farm.parcel', string='Parsel', required=True, ondelete='cascade', tracking=True)
    row_id = fields.Many2one('farm.row', string='Cərgə', domain="[('parcel_id', '=', parcel_id)]", ondelete='cascade', tracking=True)
    
    # Ağac məlumatları
    variety_id = fields.Many2one('farm.variety', string='Sort (Ağac)', required=True, ondelete='cascade', tracking=True)
    tree_count = fields.Integer('Say (ağac sayı)', required=True, tracking=True)

    # Fidan məlumatları
    seedling_type = fields.Selection([
        ('open_root', 'Açıq Kök'),
        ('closed_root', 'Qapalı Kök')
    ], string='Fidan Növü', required=True, tracking=True)

    # Təchizatçı və qiymət
    supplier = fields.Char('Təchizatçı', tracking=True)
    unit_price = fields.Float('Vahid Qiymət', tracking=True)
    total_cost = fields.Float('Ümumi Xərc', compute='_compute_total_cost', store=True)
    
    # İşçi məlumatları
    worker_line_ids = fields.One2many('farm.planting.worker', 'planting_id', string='İşçi Sətirləri')
    total_worker_cost = fields.Float('Ümumi İşçi Xərci', compute='_compute_total_worker_cost', store=True)
    
    # Qeydlər
    notes = fields.Text('Qeydlər')

    @api.depends('tree_count', 'unit_price')
    def _compute_total_cost(self):
        for record in self:
            record.total_cost = record.tree_count * record.unit_price

    @api.depends('worker_line_ids.amount')
    def _compute_total_worker_cost(self):
        for record in self:
            record.total_worker_cost = sum(line.amount for line in record.worker_line_ids)

    @api.constrains('tree_count')
    def _check_tree_count(self):
        for record in self:
            if record.tree_count <= 0:
                raise ValidationError('Ağac sayı müsbət olmalıdır!')


class FarmIrrigation(models.Model):
    """Sulama Əməliyyatı"""
    _name = 'farm.irrigation'
    _description = 'Sulama'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'irrigation_date desc'

    name = fields.Char('Əməliyyat Adı', required=True, default='Sulama', tracking=True)
    irrigation_date = fields.Datetime('Tarix', required=True, default=fields.Datetime.now, tracking=True)

    # Parsel və Cərgə
    parcel_id = fields.Many2one('farm.parcel', string='Parsel', required=True, ondelete='cascade', tracking=True)
    row_id = fields.Many2one('farm.row', string='Cərgə', domain="[('parcel_id', '=', parcel_id)]", ondelete='cascade', tracking=True)

    # Sulama tipi
    irrigation_type = fields.Selection([
        ('drip', 'Damla'),
        ('motor', 'Motor'),
        ('rain', 'Süni Yağış')
    ], string='Sulama Tipi', required=True, tracking=True)
    
    # Su məlumatları
    water_liters = fields.Float('Günlük/Litrlər', required=True, tracking=True)
    water_source = fields.Char('Su Mənbəyi', tracking=True)
    water_cost = fields.Float('Su Məsrəfi', tracking=True)
    
    # İşçi məlumatları
    operator_id = fields.Many2one('res.partner', string='Operator', domain="[('category_id.name', '=', 'Operator')]")
    worker_line_ids = fields.One2many('farm.irrigation.worker', 'irrigation_id', string='İşçi Sətirləri')
    total_worker_cost = fields.Float('Ümumi İşçi Xərci', compute='_compute_total_worker_cost', store=True)
    notes = fields.Text('Qeydlər')
    #active = fields.Boolean('Aktiv', default=True)

    @api.depends('worker_line_ids.amount')
    def _compute_total_worker_cost(self):
        for record in self:
            record.total_worker_cost = sum(line.amount for line in record.worker_line_ids)

    @api.constrains('water_liters')
    def _check_positive_values(self):
        for record in self:
            if record.water_liters <= 0:
                raise ValidationError('Su miqdarı müsbət olmalıdır!')


class FarmFertilizing(models.Model):
    """Gübrələmə Əməliyyatı"""
    _name = 'farm.fertilizing'
    _description = 'Gübrələmə'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'fertilizing_date desc'

    name = fields.Char('Əməliyyat Adı', required=True, default='Gübrələmə', tracking=True)
    fertilizing_date = fields.Datetime('Tarix', required=True, default=fields.Datetime.now, tracking=True)

    # Sahə və Parsel
    field_id = fields.Many2one('farm.field', string='Sahə', ondelete='cascade', tracking=True)
    parcel_id = fields.Many2one('farm.parcel', string='Parsel', domain="[('field_id', '=', field_id)]", ondelete='cascade', tracking=True)

    # Gübrə tipi
    fertilizer_type = fields.Selection([
        ('nitrogen', 'Azot'),
        ('phosphorus', 'Fosfor'),
        ('potassium', 'Kalium'),
        ('organic', 'Üzvi'),
        ('complex', 'Kompleks'),
        ('other', 'Digər')
    ], string='Gübrə Tipi', required=True, tracking=True)
    
    # Gübrə məlumatları
    product_line_ids = fields.One2many('farm.fertilizing.line', 'fertilizing_id', string='Məhsul Xərcləri')
    total_cost = fields.Float('Ümumi Xərc', compute='_compute_total_cost', store=True)
    
    # İşçi məlumatları
    worker_line_ids = fields.One2many('farm.fertilizing.worker', 'fertilizing_id', string='İşçi Sətirləri')
    total_worker_cost = fields.Float('Ümumi İşçi Xərci', compute='_compute_total_worker_cost', store=True)
    
    # Əlavə məlumatlar
    supplier = fields.Char('Təchizatçı', tracking=True)
    notes = fields.Text('Qeydlər')
    active = fields.Boolean('Aktiv', default=True)

    @api.depends('product_line_ids.cost')
    def _compute_total_cost(self):
        for record in self:
            record.total_cost = sum(line.cost for line in record.product_line_ids)

    @api.depends('worker_line_ids.amount')
    def _compute_total_worker_cost(self):
        for record in self:
            record.total_worker_cost = sum(line.amount for line in record.worker_line_ids)


class FarmTreatment(models.Model):
    """Dərmanlama Əməliyyatı"""
    _name = 'farm.treatment'
    _description = 'Dərmanlama'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'treatment_date desc'

    name = fields.Char('Əməliyyat Adı', required=True, default='Dərmanlama')
    treatment_date = fields.Datetime('Tarix', required=True, default=fields.Datetime.now)

    # Parsel və Cərgə
    parcel_id = fields.Many2one('farm.parcel', string='Parsel', required=False, ondelete='cascade')
    row_id = fields.Many2one('farm.row', string='Cərgə', domain="[('parcel_id', '=', parcel_id)]", ondelete='cascade')
    
    # Xəstəlik və dərman
    product_line_ids = fields.One2many('farm.treatment.line', 'treatment_id', string='Dərman Xərcləri')
    total_cost = fields.Float('Ümumi Xərc', compute='_compute_total_cost', store=True)
    
    # Tətbiq üsulu
    application_method = fields.Selection([
        ('spray', 'Püskürtmə'),
        ('injection', 'İnjeksiya'),
        ('soil', 'Torpağa'),
        ('foliar', 'Yarpağa'),
        ('other', 'Digər')
    ], string='Tətbiq Üsulu', required=True)
    
    # İşçi məlumatları
    worker_line_ids = fields.One2many('farm.treatment.worker', 'treatment_id', string='İşçi Sətirləri')
    total_worker_cost = fields.Float('Ümumi İşçi Xərci', compute='_compute_total_worker_cost', store=True)
    notes = fields.Text('Qeydlər')
    active = fields.Boolean('Aktiv', default=True)

    @api.depends('product_line_ids.cost')
    def _compute_total_cost(self):
        for record in self:
            record.total_cost = sum(line.cost for line in record.product_line_ids)

    @api.depends('worker_line_ids.amount')
    def _compute_total_worker_cost(self):
        for record in self:
            record.total_worker_cost = sum(line.amount for line in record.worker_line_ids)


class FarmFertilizingLine(models.Model):
    """Gübrələmə Məhsul Sətiri"""
    _name = 'farm.fertilizing.line'
    _description = 'Gübrələmə Məhsul Sətiri'

    fertilizing_id = fields.Many2one('farm.fertilizing', string='Gübrələmə', ondelete='cascade', required=True)
    product_id = fields.Many2one('product.product', string='Gübrə Məhsulu', required=True, domain="[('type', '=', 'consu')]", ondelete='cascade')
    product_qty = fields.Float(string='Miqdar (kq/litr)', required=True, default=1.0)
    product_uom_id = fields.Many2one('uom.uom', string='Ölçü Vahidi', related='product_id.uom_id')
    available_qty = fields.Float(string='Anbardakı Miqdar', compute='_compute_available_qty', store=False, readonly=True)
    
    unit_cost = fields.Float(string='Vahid Qiymət', related='product_id.standard_price')
    cost = fields.Float(string='Xərc', compute='_compute_cost', store=True)

    @api.depends('product_id')
    def _compute_available_qty(self):
        for line in self:
            if line.product_id:
                try:
                    line.available_qty = line.product_id.qty_available
                except:
                    line.available_qty = 0.0
            else:
                line.available_qty = 0.0

    @api.depends('product_qty', 'unit_cost')
    def _compute_cost(self):
        for line in self:
            line.cost = line.product_qty * line.unit_cost
            
    @api.onchange('product_qty', 'product_id')
    def _onchange_product_qty(self):
        if self.product_id and self.product_qty > self.available_qty:
            return {
                'warning': {
                    'title': 'Diqqət!',
                    'message': f'Seçdiyiniz miqdar ({self.product_qty}) anbarda mövcud miqdardan ({self.available_qty}) çoxdur.'
                }
            }


class FarmTreatmentLine(models.Model):
    """Dərmanlama Məhsul Sətiri"""
    _name = 'farm.treatment.line'
    _description = 'Dərmanlama Məhsul Sətiri'

    treatment_id = fields.Many2one('farm.treatment', string='Dərmanlama', ondelete='cascade', required=True)
    product_id = fields.Many2one('product.product', string='Dərman Məhsulu', required=True, domain="[('type', '=', 'consu')]", ondelete='cascade')
    product_qty = fields.Float(string='Miqdar (litr/kq)', required=True, default=1.0)
    product_uom_id = fields.Many2one('uom.uom', string='Ölçü Vahidi', related='product_id.uom_id')
    available_qty = fields.Float(string='Anbardakı Miqdar', compute='_compute_available_qty', store=False, readonly=True)
    
    unit_cost = fields.Float(string='Vahid Qiymət', related='product_id.standard_price')
    cost = fields.Float(string='Xərc', compute='_compute_cost', store=True)

    @api.depends('product_id')
    def _compute_available_qty(self):
        for line in self:
            if line.product_id:
                try:
                    line.available_qty = line.product_id.qty_available
                except:
                    line.available_qty = 0.0
            else:
                line.available_qty = 0.0

    @api.depends('product_qty', 'unit_cost')
    def _compute_cost(self):
        for line in self:
            line.cost = line.product_qty * line.unit_cost
            
    @api.onchange('product_qty', 'product_id')
    def _onchange_product_qty(self):
        if self.product_id and self.product_qty > self.available_qty:
            return {
                'warning': {
                    'title': 'Diqqət!',
                    'message': f'Seçdiyiniz miqdar ({self.product_qty}) anbarda mövcud miqdardan ({self.available_qty}) çoxdur.'
                }
            }

class FarmPruning(models.Model):
    """Budama və Təmizləmə Əməliyyatı"""
    _name = 'farm.pruning'
    _description = 'Budama və Təmizləmə'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'pruning_date desc'

    name = fields.Char('Əməliyyat Adı', required=True, default='Budama', tracking=True)
    pruning_date = fields.Datetime('Tarix', required=True, default=fields.Datetime.now, tracking=True)

    # Parsel və Cərgə
    parcel_id = fields.Many2one('farm.parcel', string='Parsel', required=True, ondelete='cascade')
    row_id = fields.Many2one('farm.row', string='Cərgə', domain="[('parcel_id', '=', parcel_id)]", ondelete='cascade')
    
    # Budama məlumatları
    pruned_tree_count = fields.Integer('Budanan Ağac Sayı', required=True, tracking=True)
    pruning_type = fields.Selection([
        ('dry', 'Quru Budama'),
        ('formal', 'Formal Budama'),
        ('cleaning', 'Təmizləmə'),
        ('shaping', 'Formalaşdırma')
    ], string='Budama Növü', required=True, tracking=True)
    
    # Alətlər və işçilər
    tools_used = fields.Text('İstifadə Olunan Alətlər', tracking=True)
    worker_line_ids = fields.One2many('farm.pruning.worker', 'pruning_id', string='İşçi Sətirləri')
    total_worker_cost = fields.Float('Ümumi İşçi Xərci', compute='_compute_total_worker_cost', store=True)
    worker_count = fields.Integer('İşçi Sayı')
    work_hours = fields.Float('İş Saatı')
    
    # Xərclər
    cost = fields.Float('Xərc')
    notes = fields.Text('Qeydlər')
    active = fields.Boolean('Aktiv', default=True)

    @api.depends('worker_line_ids.amount')
    def _compute_total_worker_cost(self):
        for record in self:
            record.total_worker_cost = sum(line.amount for line in record.worker_line_ids)

    @api.constrains('pruned_tree_count', 'worker_count')
    def _check_positive_values(self):
        for record in self:
            if record.pruned_tree_count <= 0:
                raise ValidationError('Budanan ağac sayı müsbət olmalıdır!')
            if record.worker_count and record.worker_count <= 0:
                raise ValidationError('İşçi sayı müsbət olmalıdır!')


class FarmHarvest(models.Model):
    """Yığım Əməliyyatı"""
    _name = 'farm.harvest'
    _description = 'Yığım'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'harvest_date desc'

    name = fields.Char('Əməliyyat Adı', required=True, default='Yığım', tracking=True)
    harvest_date = fields.Datetime('Yığım Tarixi', required=True, default=fields.Datetime.now, tracking=True)

    # Parsel və Cərgə
    parcel_id = fields.Many2one('farm.parcel', string='Parsel', required=True, ondelete='cascade')
    row_id = fields.Many2one('farm.row', string='Cərgə', domain="[('parcel_id', '=', parcel_id)]", ondelete='cascade')
    
    # Yığım məlumatları
    harvest_type = fields.Selection([
        ('manual', 'Əllə'),
        ('mechanical', 'Mexaniki')
    ], string='Yığım Növü', required=True, tracking=True)

    tree_count = fields.Integer('Ağac Sayı', required=True, tracking=True)
    quantity_kg = fields.Float('Miqdar (kq)', required=True, tracking=True)
    loaded_to_pallets = fields.Boolean('Paletlərə Yükləndimi?', default=False, tracking=True)

    # İşçi məlumatları
    worker_line_ids = fields.One2many('farm.harvest.worker', 'harvest_id', string='İşçi Sətirləri')
    total_worker_cost = fields.Float('Ümumi İşçi Xərci', compute='_compute_total_worker_cost', store=True)
    worker_count = fields.Integer('İşçi Sayı', required=True)
    work_hours = fields.Float('İş Vaxtı (saat)', required=True)
    
    # Xərclər
    cost_per_kg = fields.Float('Kq-a Görə Qiymət')
    total_cost = fields.Float('Ümumi Xərc', compute='_compute_total_cost', store=True)
    
    # Qeydlər
    notes = fields.Text('Qeydlər')
    active = fields.Boolean('Aktiv', default=True)

    @api.depends('quantity_kg', 'cost_per_kg')
    def _compute_total_cost(self):
        for record in self:
            record.total_cost = record.quantity_kg * record.cost_per_kg

    @api.depends('worker_line_ids.amount')
    def _compute_total_worker_cost(self):
        for record in self:
            record.total_worker_cost = sum(line.amount for line in record.worker_line_ids)

    @api.constrains('tree_count', 'quantity_kg', 'worker_count', 'work_hours')
    def _check_positive_values(self):
        for record in self:
            if record.tree_count <= 0:
                raise ValidationError('Ağac sayı müsbət olmalıdır!')
            if record.quantity_kg <= 0:
                raise ValidationError('Məhsul miqdarı müsbət olmalıdır!')
            if record.worker_count <= 0:
                raise ValidationError('İşçi sayı müsbət olmalıdır!')
            if record.work_hours <= 0:
                raise ValidationError('İş vaxtı müsbət olmalıdır!')


class FarmForecast(models.Model):
    """Proqnozlaşdırma"""
    _name = 'farm.forecast'
    _description = 'Proqnozlaşdırma'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'forecast_year desc, forecast_month'

    name = fields.Char('Proqnoz Adı', required=True, default='Proqnozlaşdırma', tracking=True)
    forecast_year = fields.Integer('İl', required=True, default=lambda self: fields.Date.today().year, tracking=True)
    forecast_month = fields.Selection([
        ('1', 'Yanvar'), ('2', 'Fevral'), ('3', 'Mart'),
        ('4', 'Aprel'), ('5', 'May'), ('6', 'İyun'),
        ('7', 'İyul'), ('8', 'Avqust'), ('9', 'Sentyabr'),
        ('10', 'Oktyabr'), ('11', 'Noyabr'), ('12', 'Dekabr')
    ], string='Ay', required=True, default=lambda self: fields.Date.today().month, tracking=True)
    
    # Sahə və Parsel
    field_id = fields.Many2one('farm.field', string='Sahə', ondelete='cascade')
    parcel_id = fields.Many2one('farm.parcel', string='Parsel', domain="[('field_id', '=', field_id)]", ondelete='cascade')
    
    # Proqnoz məlumatları
    expected_quantity_kg = fields.Float('Gözlənən Miqdar (kq)', required=True, tracking=True)
    historical_data_based = fields.Boolean('Tarixi Məlumatlara Əsaslanan', default=True, tracking=True)
    
    # Risk faktoru
    climate_risk_factor = fields.Selection([
        ('low', 'Aşağı'),
        ('medium', 'Orta'),
        ('high', 'Yüksək'),
        ('very_high', 'Çox Yüksək')
    ], string='İqlim Risk Faktoru', required=True, default='medium', tracking=True)
    
    # Əlavə məlumatlar
    confidence_level = fields.Float('Etibarlılıq Səviyyəsi (%)', default=80.0, tracking=True)
    notes = fields.Text('Analiz və Qeydlər', tracking=True)
    active = fields.Boolean('Aktiv', default=True, tracking=True)

    @api.constrains('expected_quantity_kg', 'confidence_level')
    def _check_values(self):
        for record in self:
            if record.expected_quantity_kg < 0:
                raise ValidationError('Gözlənən miqdar mənfi ola bilməz!')
            if not (0 <= record.confidence_level <= 100):
                raise ValidationError('Etibarlılıq səviyyəsi 0-100 arasında olmalıdır!')


class FarmDamagedTrees(models.Model):
    """Zərərçəkmiş Ağaclar"""
    _name = 'farm.damaged.trees'
    _description = 'Zərərçəkmiş Ağaclar'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'damage_date desc'

    name = fields.Char('Qeyd Adı', required=True, default='Zərərçəkmiş Ağaclar', tracking=True)
    damage_date = fields.Datetime('Tarix', required=True, default=fields.Datetime.now, tracking=True)

    # Parsel məlumatları
    parcel_id = fields.Many2one('farm.parcel', string='Parsel', required=True, ondelete='cascade')
    row_id = fields.Many2one('farm.row', string='Cərgə', domain="[('parcel_id', '=', parcel_id)]", ondelete='cascade')
    
    # Zərər məlumatları
    damaged_tree_count = fields.Integer('Zərərçəkmiş Ağac Sayı', required=True, tracking=True)
    damage_reason = fields.Selection([
        ('disease', 'Xəstəlik'),
        ('frost', 'Don'),
        ('flood', 'Su Basması'),
        ('mechanical', 'Mexaniki'),
        ('pest', 'Zərərverici'),
        ('drought', 'Quraqlıq'),
        ('wind', 'Külək'),
        ('other', 'Digər')
    ], string='Zərər Səbəbi', required=True, tracking=True)

    # Müalicə tədbiri
    treatment_applied = fields.Boolean('Müalicə Tədbiri Görülübmü?', default=False, tracking=True)
    treatment_description = fields.Text('Müalicə Təsviri', tracking=True)
    treatment_date = fields.Date('Müalicə Tarixi', tracking=True)
    treatment_cost = fields.Float('Müalicə Xərci', tracking=True)

    # Nəticə
    recovery_status = fields.Selection([
        ('recovered', 'Sağalıb'),
        ('partial', 'Qismən Sağalıb'),
        ('lost', 'İtirilmiş'),
        ('pending', 'Gözləyir')
    ], string='Bərpa Statusu', default='pending', required=True, tracking=True)
    
    # Qeydlər
    notes = fields.Text('Əlavə Qeydlər')
    active = fields.Boolean('Aktiv', default=True)

    @api.constrains('damaged_tree_count')
    def _check_tree_count(self):
        for record in self:
            if record.damaged_tree_count <= 0:
                raise ValidationError('Zərərçəkmiş ağac sayı müsbət olmalıdır!')


class FarmColdStorage(models.Model):
    """Malların Soyuducuya Yerləşdirilməsi"""
    _name = 'farm.cold.storage'
    _description = 'Soyuducu Anbarı'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'storage_date desc'

    name = fields.Char('Əməliyyat Adı', required=True, default='Soyuducuya Yerləşdirmə', tracking=True)
    storage_date = fields.Datetime('Tarix', required=True, default=fields.Datetime.now, tracking=True)

    # Palet məlumatları
    pallet_id = fields.Many2one('farm.pallet', string='Palet', required=True, ondelete='cascade')
    pallet_code = fields.Char('Palet Kodu', related='pallet_id.pallet_code', store=True)
    quantity_kg = fields.Float('Miqdar (kq)', required=True, tracking=True)
    
    # Soyuducu məlumatları
    cooler_id = fields.Many2one('farm.cooler', string='Soyuducu', required=True, ondelete='cascade')
    cold_storage_code = fields.Char('Soyuducu Kodu', related='cooler_id.cooler_code', store=True)
    storage_section = fields.Char('Bölmə', tracking=True)
    storage_position = fields.Char('Paletin Yerləşdiyi Nömrə', tracking=True)

    # Temperatura və şərait
    temperature = fields.Float('Temperatura (°C)', tracking=True)
    humidity = fields.Float('Rütubət (%)', tracking=True)

    # İşçi məlumatları
    worker_line_ids = fields.One2many('farm.cold.storage.worker', 'cold_storage_id', string='İşçi Sətirləri')
    total_worker_cost = fields.Float('Ümumi İşçi Xərci', compute='_compute_total_worker_cost', store=True)
    operator_id = fields.Many2one('res.partner', string='Operator', domain="[('category_id.name', '=', 'Operator')]")
    entry_time = fields.Datetime('Giriş Vaxtı', default=fields.Datetime.now)
    exit_time = fields.Datetime('Çıxış Vaxtı')
    
    # Status
    status = fields.Selection([
        ('stored', 'Anbarlandırılıb'),
        ('processing', 'İşləmədə'),
        ('shipped', 'Göndərildi'),
        ('damaged', 'Zədələnib')
    ], string='Status', default='stored', required=True, tracking=True)
    
    # Qeydlər
    notes = fields.Text('Qeydlər')
    active = fields.Boolean('Aktiv', default=True)

    @api.depends('worker_line_ids.amount')
    def _compute_total_worker_cost(self):
        for record in self:
            record.total_worker_cost = sum(line.amount for line in record.worker_line_ids)

    @api.constrains('quantity_kg', 'temperature', 'humidity')
    def _check_values(self):
        for record in self:
            if record.quantity_kg <= 0:
                raise ValidationError('Məhsul miqdarı müsbət olmalıdır!')
            if record.humidity and not (0 <= record.humidity <= 100):
                raise ValidationError('Rütubət 0-100% arasında olmalıdır!')

    @api.constrains('pallet_code')
    def _check_unique_pallet_code(self):
        for record in self:
            if self.search_count([
                ('pallet_code', '=', record.pallet_code),
                ('status', '=', 'stored'),
                ('id', '!=', record.id)
            ]) > 0:
                raise ValidationError('Bu palet kodu artıq soyuducuda mövcuddur!')


# Worker Line Models
class FarmPlowingWorker(models.Model):
    """Şumlama İşçi Sətiri"""
    _name = 'farm.plowing.worker'
    _description = 'Şumlama İşçi Sətiri'

    plowing_id = fields.Many2one('farm.plowing', string='Şumlama', ondelete='cascade', required=True)
    worker_id = fields.Many2one('farm.worker', string='İşçi', ondelete='cascade')
    worker_name = fields.Char('İşçi Adı', required=False)
    hours_worked = fields.Float('İş Saatı', required=True, default=1.0)
    hourly_rate = fields.Float('Saatlıq Tarif', required=True, default=0.0)
    amount = fields.Float('Məbləğ', compute='_compute_amount', store=True)

    @api.depends('hours_worked', 'hourly_rate')
    def _compute_amount(self):
        for record in self:
            record.amount = record.hours_worked * record.hourly_rate

    @api.onchange('worker_id')
    def _onchange_worker_id(self):
        if self.worker_id:
            self.worker_name = self.worker_id.name
            self.hourly_rate = self.worker_id.hourly_rate


class FarmPlantingWorker(models.Model):
    """Əkin İşçi Sətiri"""
    _name = 'farm.planting.worker'
    _description = 'Əkin İşçi Sətiri'

    planting_id = fields.Many2one('farm.planting', string='Əkin', ondelete='cascade', required=True)
    worker_id = fields.Many2one('farm.worker', string='İşçi', ondelete='cascade')
    worker_name = fields.Char('İşçi Adı', required=False)
    hours_worked = fields.Float('İş Saatı', required=True, default=1.0)
    hourly_rate = fields.Float('Saatlıq Tarif', required=True, default=0.0)
    amount = fields.Float('Məbləğ', compute='_compute_amount', store=True)

    @api.depends('hours_worked', 'hourly_rate')
    def _compute_amount(self):
        for record in self:
            record.amount = record.hours_worked * record.hourly_rate

    @api.onchange('worker_id')
    def _onchange_worker_id(self):
        if self.worker_id:
            self.worker_name = self.worker_id.name
            self.hourly_rate = self.worker_id.hourly_rate


class FarmIrrigationWorker(models.Model):
    """Sulama İşçi Sətiri"""
    _name = 'farm.irrigation.worker'
    _description = 'Sulama İşçi Sətiri'

    irrigation_id = fields.Many2one('farm.irrigation', string='Sulama', ondelete='cascade', required=True)
    worker_id = fields.Many2one('farm.worker', string='İşçi', ondelete='cascade')
    worker_name = fields.Char('İşçi Adı', required=False)
    hours_worked = fields.Float('İş Saatı', required=True, default=1.0)
    hourly_rate = fields.Float('Saatlıq Tarif', required=True, default=0.0)
    amount = fields.Float('Məbləğ', compute='_compute_amount', store=True)

    @api.depends('hours_worked', 'hourly_rate')
    def _compute_amount(self):
        for record in self:
            record.amount = record.hours_worked * record.hourly_rate

    @api.onchange('worker_id')
    def _onchange_worker_id(self):
        if self.worker_id:
            self.worker_name = self.worker_id.name
            self.hourly_rate = self.worker_id.hourly_rate


class FarmFertilizingWorker(models.Model):
    """Gübrələmə İşçi Sətiri"""
    _name = 'farm.fertilizing.worker'
    _description = 'Gübrələmə İşçi Sətiri'

    fertilizing_id = fields.Many2one('farm.fertilizing', string='Gübrələmə', ondelete='cascade', required=True)
    worker_id = fields.Many2one('farm.worker', string='İşçi', ondelete='cascade')
    worker_name = fields.Char('İşçi Adı', required=False)
    hours_worked = fields.Float('İş Saatı', required=True, default=1.0)
    hourly_rate = fields.Float('Saatlıq Tarif', required=True, default=0.0)
    amount = fields.Float('Məbləğ', compute='_compute_amount', store=True)

    @api.depends('hours_worked', 'hourly_rate')
    def _compute_amount(self):
        for record in self:
            record.amount = record.hours_worked * record.hourly_rate

    @api.onchange('worker_id')
    def _onchange_worker_id(self):
        if self.worker_id:
            self.worker_name = self.worker_id.name
            self.hourly_rate = self.worker_id.hourly_rate


class FarmTreatmentWorker(models.Model):
    """Dərmanlama İşçi Sətiri"""
    _name = 'farm.treatment.worker'
    _description = 'Dərmanlama İşçi Sətiri'

    treatment_id = fields.Many2one('farm.treatment', string='Dərmanlama', ondelete='cascade', required=True)
    worker_id = fields.Many2one('farm.worker', string='İşçi', ondelete='cascade')
    worker_name = fields.Char('İşçi Adı', required=False)
    hours_worked = fields.Float('İş Saatı', required=True, default=1.0)
    hourly_rate = fields.Float('Saatlıq Tarif', required=True, default=0.0)
    amount = fields.Float('Məbləğ', compute='_compute_amount', store=True)

    @api.depends('hours_worked', 'hourly_rate')
    def _compute_amount(self):
        for record in self:
            record.amount = record.hours_worked * record.hourly_rate

    @api.onchange('worker_id')
    def _onchange_worker_id(self):
        if self.worker_id:
            self.worker_name = self.worker_id.name
            self.hourly_rate = self.worker_id.hourly_rate


class FarmPruningWorker(models.Model):
    """Budama İşçi Sətiri"""
    _name = 'farm.pruning.worker'
    _description = 'Budama İşçi Sətiri'

    pruning_id = fields.Many2one('farm.pruning', string='Budama', ondelete='cascade', required=True)
    worker_id = fields.Many2one('farm.worker', string='İşçi', ondelete='cascade')
    worker_name = fields.Char('İşçi Adı', required=False)
    hours_worked = fields.Float('İş Saatı', required=True, default=1.0)
    hourly_rate = fields.Float('Saatlıq Tarif', required=True, default=0.0)
    amount = fields.Float('Məbləğ', compute='_compute_amount', store=True)

    @api.depends('hours_worked', 'hourly_rate')
    def _compute_amount(self):
        for record in self:
            record.amount = record.hours_worked * record.hourly_rate

    @api.onchange('worker_id')
    def _onchange_worker_id(self):
        if self.worker_id:
            self.worker_name = self.worker_id.name
            self.hourly_rate = self.worker_id.hourly_rate


class FarmHarvestWorker(models.Model):
    """Yığım İşçi Sətiri"""
    _name = 'farm.harvest.worker'
    _description = 'Yığım İşçi Sətiri'

    harvest_id = fields.Many2one('farm.harvest', string='Yığım', ondelete='cascade', required=True)
    worker_id = fields.Many2one('farm.worker', string='İşçi', ondelete='cascade')
    worker_name = fields.Char('İşçi Adı', required=False)
    hours_worked = fields.Float('İş Saatı', required=True, default=1.0)
    hourly_rate = fields.Float('Saatlıq Tarif', required=True, default=0.0)
    amount = fields.Float('Məbləğ', compute='_compute_amount', store=True)

    @api.depends('hours_worked', 'hourly_rate')
    def _compute_amount(self):
        for record in self:
            record.amount = record.hours_worked * record.hourly_rate

    @api.onchange('worker_id')
    def _onchange_worker_id(self):
        if self.worker_id:
            self.worker_name = self.worker_id.name
            self.hourly_rate = self.worker_id.hourly_rate


class FarmColdStorageWorker(models.Model):
    """Soyuducu Anbarı İşçi Sətiri"""
    _name = 'farm.cold.storage.worker'
    _description = 'Soyuducu Anbarı İşçi Sətiri'

    cold_storage_id = fields.Many2one('farm.cold.storage', string='Soyuducu Anbarı', ondelete='cascade', required=True)
    worker_id = fields.Many2one('farm.worker', string='İşçi', ondelete='cascade')
    worker_name = fields.Char('İşçi Adı', required=False)
    hours_worked = fields.Float('İş Saatı', required=True, default=1.0)
    hourly_rate = fields.Float('Saatlıq Tarif', required=True, default=0.0)
    amount = fields.Float('Məbləğ', compute='_compute_amount', store=True)

    @api.depends('hours_worked', 'hourly_rate')
    def _compute_amount(self):
        for record in self:
            record.amount = record.hours_worked * record.hourly_rate

    @api.onchange('worker_id')
    def _onchange_worker_id(self):
        if self.worker_id:
            self.worker_name = self.worker_id.name
            self.hourly_rate = self.worker_id.hourly_rate
