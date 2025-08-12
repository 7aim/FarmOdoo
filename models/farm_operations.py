from odoo import models, fields, api
from odoo.exceptions import ValidationError


class FarmPlowing(models.Model):
    """Şumlama Əməliyyatı"""
    _name = 'farm.plowing'
    _description = 'Şumlama'
    _order = 'operation_date desc'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char('Əməliyyat Adı', required=True, compute='_compute_name', default='Şumlama', tracking=True)
    operation_date = fields.Datetime('Tarix', required=True, default=fields.Datetime.now, tracking=True)

    field_id = fields.Many2one('farm.field', string='Sahə', ondelete='cascade', required=True, tracking=True)
    parcel_id = fields.Many2one('farm.parcel', string='Parsel', domain="[('field_id', '=', field_id)]", ondelete='cascade', tracking=True)
    row_id = fields.Many2one('farm.row', string='Cərgə', domain="[('parcel_id', '=', parcel_id)]", ondelete='cascade', tracking=True)

    # Texniki məlumatlar
    equipment = fields.Many2one('res.partner', string='İcrakar', tracking=True)
    plowing_depth = fields.Float('Şumlama Dərinliyi (cm)', default=5.0, required=True, tracking=True)
    area_hectare = fields.Float('Genişlik (ha)', default=10.0, required=True, tracking=True)

    # İşçi məlumatları
    operator_id = fields.Many2one('res.partner', string='Operator', domain="[('category_id.name', '=', 'Operator')]", tracking=True)
    worker_line_ids = fields.One2many('farm.plowing.worker', 'plowing_id', string='İşçi Sətirləri')
    total_worker_cost = fields.Float('İşçi Xərci', compute='_compute_total_worker_cost', store=True)
    
    # Əlavə xərclər
    additional_expense_ids = fields.One2many('farm.additional.expense', 'plowing_id', string='Əlavə Xərclər')
    total_additional_cost = fields.Float('Əlavə Xərc', compute='_compute_total_additional_cost', store=True)

    # Ümumi xərc
    total_cost = fields.Float('Ümumi Xərc', compute='_compute_total_cost', store=True)

    notes = fields.Text('Qeydlər')

    @api.depends('worker_line_ids.amount')
    def _compute_total_worker_cost(self):
        for record in self:
            record.total_worker_cost = sum(line.amount for line in record.worker_line_ids)

    @api.depends('additional_expense_ids.amount')
    def _compute_total_additional_cost(self):
        for record in self:
            record.total_additional_cost = sum(expense.amount for expense in record.additional_expense_ids)

    @api.depends('total_worker_cost', 'total_additional_cost')
    def _compute_total_cost(self):
        for record in self:
            record.total_cost = record.total_worker_cost + record.total_additional_cost

    @api.constrains('plowing_depth', 'area_hectare')
    def _check_positive_values(self):
        for record in self:
            if record.plowing_depth <= 0:
                raise ValidationError('Şumlama dərinliyi müsbət olmalıdır!')
            if record.area_hectare <= 0:
                raise ValidationError('Genişlik müsbət olmalıdır!')

    @api.depends('field_id', 'parcel_id', 'operation_date')
    def _compute_name(self):
        for record in self:
            if record.field_id and record.parcel_id and record.operation_date:
                record.name = f" Şumlama - {record.field_id.name} - {record.parcel_id.name} - ({record.operation_date})"
            elif record.field_id and record.operation_date:
                record.name = f" Şumlama - {record.field_id.name} - ({record.operation_date})"
            else:
                record.name = 'Yeni Şumlama Qeydi'

    
class FarmPlanting(models.Model):
    """Əkin Əməliyyatı"""
    _name = 'farm.planting'
    _description = 'Əkin'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'planting_date desc'

    name = fields.Char('Əməliyyat Adı', required=True, compute='_compute_name', default='Əkin', tracking=True)
    planting_date = fields.Datetime('Əkin Tarixi', required=True, default=fields.Datetime.now, tracking=True)

    field_id = fields.Many2one('farm.field', string='Sahə', ondelete='cascade', required=True, tracking=True)
    parcel_id = fields.Many2one('farm.parcel', string='Parsel', domain="[('field_id', '=', field_id)]", ondelete='cascade', tracking=True)
    row_id = fields.Many2one('farm.row', string='Cərgə', domain="[('parcel_id', '=', parcel_id)]", ondelete='cascade', tracking=True)
    
    # Ağac məlumatları
    variety_id = fields.Many2one('farm.variety', string='Sort (Ağac)', required=True, ondelete='cascade', tracking=True)
    tree_count = fields.Integer('Ağac sayı', required=True, default=1, tracking=True)

    # Fidan məlumatları
    seedling_type = fields.Selection([
        ('open_root', 'Açıq Kök'),
        ('closed_root', 'Qapalı Kök')
    ], string='Fidan Növü', required=True, tracking=True)

    # Təchizatçı və qiymət
    supplier = fields.Many2one('res.partner', string='Təchizatçı', domain="[('category_id.name', '=', 'Techizatcı')]", tracking=True)
    unit_price = fields.Float('Vahid Qiymət', tracking=True)
    # total_cost = fields.Float('Ümumi Xərc', compute='_compute_total_cost', store=True)

    # İşçi məlumatları
    worker_line_ids = fields.One2many('farm.planting.worker', 'planting_id', string='İşçi Sətirləri')
    total_worker_cost = fields.Float('İşçi Xərci', compute='_compute_total_worker_cost', store=True)
    
    # Əlavə xərclər
    additional_expense_ids = fields.One2many('farm.additional.expense', 'planting_id', string='Əlavə Xərclər')
    total_additional_cost = fields.Float('Əlavə Xərc', compute='_compute_total_additional_cost', store=True)

    # Ümumi xərc
    total_cost = fields.Float('Ümumi Xərc', compute='_compute_total_cost', store=True)

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

    @api.depends('additional_expense_ids.amount')
    def _compute_total_additional_cost(self):
        for record in self:
            record.total_additional_cost = sum(expense.amount for expense in record.additional_expense_ids)

    @api.depends('total_worker_cost', 'total_additional_cost')
    def _compute_total_cost(self):
        for record in self:
            record.total_cost = record.total_worker_cost + record.total_additional_cost

    @api.constrains('tree_count')
    def _check_tree_count(self):
        for record in self:
            if record.tree_count <= 0:
                raise ValidationError('Ağac sayı müsbət olmalıdır!')

    @api.depends('field_id', 'parcel_id', 'planting_date')
    def _compute_name(self):
        for record in self:
            if record.field_id and record.parcel_id and record.planting_date:
                record.name = f" Əkin - {record.field_id.name} - {record.parcel_id.name} - ({record.planting_date})"
            elif record.field_id and record.planting_date:
                record.name = f" Əkin - {record.field_id.name} - ({record.planting_date})"
            else:
                record.name = 'Yeni Əkin Qeydi'


class FarmIrrigation(models.Model):
    """Sulama Əməliyyatı"""
    _name = 'farm.irrigation'
    _description = 'Sulama'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'irrigation_date desc'

    name = fields.Char('Əməliyyat Adı', required=True, compute='_compute_name', default='Sulama', tracking=True)
    irrigation_date = fields.Datetime('Tarix', required=True, default=fields.Datetime.now, tracking=True)

    field_id = fields.Many2one('farm.field', string='Sahə', ondelete='cascade', required=True, tracking=True)
    parcel_id = fields.Many2one('farm.parcel', string='Parsel', domain="[('field_id', '=', field_id)]", ondelete='cascade', tracking=True)
    row_id = fields.Many2one('farm.row', string='Cərgə', domain="[('parcel_id', '=', parcel_id)]", ondelete='cascade', tracking=True)

    # Sulama tipi
    irrigation_type = fields.Selection([
        ('drip', 'Damla'),
        ('motor', 'Motor'),
        ('rain', 'Süni Yağış')
    ], string='Sulama Tipi', required=True, tracking=True)
    
    # Su məlumatları
    water_liters = fields.Float('Su Miqdarı', required=True, default=1000.0, tracking=True)
    water_source = fields.Char('Su Mənbəyi', tracking=True)
    water_cost = fields.Float('Su Məsrəfi', tracking=True)

    # İşçi məlumatları
    operator_id = fields.Many2one('res.partner', string='Operator', domain="[('category_id.name', '=', 'Operator')]")
    worker_line_ids = fields.One2many('farm.irrigation.worker', 'irrigation_id', string='İşçi Sətirləri')
    total_worker_cost = fields.Float('İşçi Xərci', compute='_compute_total_worker_cost', store=True)
    
    # Əlavə xərclər
    additional_expense_ids = fields.One2many('farm.additional.expense', 'irrigation_id', string='Əlavə Xərclər')
    total_additional_cost = fields.Float('Əlavə Xərc', compute='_compute_total_additional_cost', store=True)

    # Ümumi xərc
    total_cost = fields.Float('Ümumi Xərc', compute='_compute_total_cost', store=True)

    notes = fields.Text('Qeydlər')
    #active = fields.Boolean('Aktiv', default=True)

    @api.depends('worker_line_ids.amount')
    def _compute_total_worker_cost(self):
        for record in self:
            record.total_worker_cost = sum(line.amount for line in record.worker_line_ids)

    @api.depends('additional_expense_ids.amount')
    def _compute_total_additional_cost(self):
        for record in self:
            record.total_additional_cost = sum(expense.amount for expense in record.additional_expense_ids)

    @api.depends('total_worker_cost', 'total_additional_cost')
    def _compute_total_cost(self):
        for record in self:
            record.total_cost = record.total_worker_cost + record.total_additional_cost

    @api.constrains('water_liters')
    def _check_positive_values(self):
        for record in self:
            if record.water_liters <= 0:
                raise ValidationError('Su miqdarı müsbət olmalıdır!')

    @api.depends('field_id', 'parcel_id', 'irrigation_date')
    def _compute_name(self):
        for record in self:
            if  record.parcel_id and record.field_id and record.irrigation_date:
                record.name = f" Sulama - {record.field_id.name} - {record.parcel_id.name} - ({record.irrigation_date})"
            elif record.field_id and record.irrigation_date:
                record.name = f" Sulama - {record.field_id.name} - ({record.irrigation_date})"
            else:
                record.name = 'Yeni Sulama Qeydi'


class FarmFertilizing(models.Model):
    """Gübrələmə Əməliyyatı"""
    _name = 'farm.fertilizing'
    _description = 'Gübrələmə'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'fertilizing_date desc'

    name = fields.Char('Əməliyyat Adı', required=True, compute='_compute_name', default='Gübrələmə', tracking=True)
    fertilizing_date = fields.Datetime('Tarix', required=True, default=fields.Datetime.now, tracking=True)

    field_id = fields.Many2one('farm.field', string='Sahə', ondelete='cascade', required=True, tracking=True)
    parcel_id = fields.Many2one('farm.parcel', string='Parsel', domain="[('field_id', '=', field_id)]", ondelete='cascade', tracking=True)
    row_id = fields.Many2one('farm.row', string='Cərgə', domain="[('parcel_id', '=', parcel_id)]", ondelete='cascade', tracking=True)


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
    total_product_cost = fields.Float('Məhsul Xərci', compute='_compute_total_product_cost', store=True)

    # İşçi məlumatları
    worker_line_ids = fields.One2many('farm.fertilizing.worker', 'fertilizing_id', string='İşçi Sətirləri')
    total_worker_cost = fields.Float('İşçi Xərci', compute='_compute_total_worker_cost', store=True)
    
    # Əlavə xərclər
    additional_expense_ids = fields.One2many('farm.additional.expense', 'fertilizing_id', string='Əlavə Xərclər')
    total_additional_cost = fields.Float('Əlavə Xərc', compute='_compute_total_additional_cost', store=True)

    # Umumi xərc
    total_cost = fields.Float('Ümumi Xərc', compute='_compute_total_cost', store=True)

    # Əlavə məlumatlar
    supplier = fields.Many2one('res.partner', string='Təchizatçı', domain="[('category_id.name', '=', 'Techizatcı')]", tracking=True)
    notes = fields.Text('Qeydlər')
    active = fields.Boolean('Aktiv', default=True)

    @api.depends('product_line_ids.cost')
    def _compute_total_product_cost(self):
        for record in self:
            record.total_product_cost = sum(line.cost for line in record.product_line_ids)

    @api.depends('worker_line_ids.amount')
    def _compute_total_worker_cost(self):
        for record in self:
            record.total_worker_cost = sum(line.amount for line in record.worker_line_ids)

    @api.depends('additional_expense_ids.amount')
    def _compute_total_additional_cost(self):
        for record in self:
            record.total_additional_cost = sum(expense.amount for expense in record.additional_expense_ids)

    @api.depends('product_line_ids.cost', 'total_worker_cost', 'total_additional_cost')
    def _compute_total_cost(self):
        for record in self:
            record.total_cost = record.total_product_cost + record.total_worker_cost + record.total_additional_cost

    @api.depends('field_id', 'parcel_id', 'fertilizing_date')
    def _compute_name(self):
        for record in self:
            if  record.parcel_id and record.field_id and record.fertilizing_date:
                record.name = f" Gübrələmə - {record.field_id.name} - {record.parcel_id.name} - ({record.fertilizing_date})"
            elif record.field_id and record.fertilizing_date:
                record.name = f" Gübrələmə - {record.field_id.name} - ({record.fertilizing_date})"
            else:
                record.name = 'Yeni Gübrələmə Qeydi'


class FarmTreatment(models.Model):
    """Dərmanlama Əməliyyatı"""
    _name = 'farm.treatment'
    _description = 'Dərmanlama'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'treatment_date desc'

    name = fields.Char('Əməliyyat Adı', required=True, compute='_compute_name', default='Dərmanlama')
    treatment_date = fields.Datetime('Tarix', required=True, default=fields.Datetime.now)

    field_id = fields.Many2one('farm.field', string='Sahə', ondelete='cascade', required=True, tracking=True)
    parcel_id = fields.Many2one('farm.parcel', string='Parsel', domain="[('field_id', '=', field_id)]", ondelete='cascade', tracking=True)
    row_id = fields.Many2one('farm.row', string='Cərgə', domain="[('parcel_id', '=', parcel_id)]", ondelete='cascade', tracking=True)
    
    # Tətbiq üsulu
    application_method = fields.Selection([
        ('spray', 'Püskürtmə'),
        ('injection', 'İnjeksiya'),
        ('soil', 'Torpağa'),
        ('foliar', 'Yarpağa'),
        ('other', 'Digər')
    ], string='Tətbiq Üsulu', required=True)

    # Xəstəlik və dərman
    product_line_ids = fields.One2many('farm.treatment.line', 'treatment_id', string='Dərman Xərcləri')
    total_product_cost = fields.Float('Məhsul Xərci', compute='_compute_total_product_cost', store=True)

    # İşçi məlumatları
    worker_line_ids = fields.One2many('farm.treatment.worker', 'treatment_id', string='İşçi Sətirləri')
    total_worker_cost = fields.Float('İşçi Xərci', compute='_compute_total_worker_cost', store=True)
    
    # Əlavə xərclər
    additional_expense_ids = fields.One2many('farm.additional.expense', 'treatment_id', string='Əlavə Xərclər')
    total_additional_cost = fields.Float('Əlavə Xərc', compute='_compute_total_additional_cost', store=True)

    # Umumi xərc
    total_cost = fields.Float('Ümumi Xərc', compute='_compute_total_cost', store=True)
    
    notes = fields.Text('Qeydlər')
    active = fields.Boolean('Aktiv', default=True)

    @api.depends('product_line_ids.cost')
    def _compute_total_product_cost(self):
        for record in self:
            record.total_product_cost = sum(line.cost for line in record.product_line_ids)

    @api.depends('worker_line_ids.amount')
    def _compute_total_worker_cost(self):
        for record in self:
            record.total_worker_cost = sum(line.amount for line in record.worker_line_ids)

    @api.depends('additional_expense_ids.amount')
    def _compute_total_additional_cost(self):
        for record in self:
            record.total_additional_cost = sum(expense.amount for expense in record.additional_expense_ids)

    @api.depends('total_worker_cost', 'total_additional_cost')
    def _compute_total_cost(self):
        for record in self:
            record.total_cost = record.total_worker_cost + record.total_additional_cost + record.total_product_cost

    @api.depends('field_id', 'parcel_id', 'treatment_date')
    def _compute_name(self):
        for record in self:
            if  record.parcel_id and record.field_id and record.treatment_date:
                record.name = f" Dərmanlama - {record.field_id.name} - {record.parcel_id.name} - ({record.treatment_date})"
            elif record.field_id and record.treatment_date:
                record.name = f" Dərmanlama - {record.field_id.name} - ({record.treatment_date})"
            else:
                record.name = 'Yeni Dərmanlama Qeydi'


class FarmFertilizingLine(models.Model):
    """Gübrələmə Məhsul Sətiri"""
    _name = 'farm.fertilizing.line'
    _description = 'Gübrələmə Məhsul Sətiri'

    fertilizing_id = fields.Many2one('farm.fertilizing', string='Gübrələmə', ondelete='cascade', required=True)
    product_id = fields.Many2one('product.product', string='Gübrə Məhsulu', required=True, domain="[('type', '=', 'consu')]", ondelete='cascade')
    product_qty = fields.Float(string='Quantity', required=True, default=1.0)
    product_uom_id = fields.Many2one('uom.uom', string='Ölçü Vahidi', related='product_id.uom_id')
    available_qty = fields.Float(string='Anbarda Mövcud', compute='_compute_available_qty', store=False, readonly=True)
    product_weight = fields.Float(
        string='Çəki (kg)',
        related='product_id.weight',
        readonly=True,
        help='Məhsulun vahid çəkisi'
    )
    
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
    product_qty = fields.Float(string='Miqdar', required=True, default=1.0)
    product_uom_id = fields.Many2one('uom.uom', string='Ölçü Vahidi', related='product_id.uom_id')
    available_qty = fields.Float(string='Anbarda Mövcud', compute='_compute_available_qty', store=False, readonly=True)
    product_weight = fields.Float(
        string='Çəki (kg)',
        related='product_id.weight',
        readonly=True,
        help='Məhsulun vahid çəkisi'
    )
    
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


# Əlavə Xərclər Base Model
class FarmAdditionalExpense(models.Model):
    """Əlavə Xərclər Base Model"""
    _name = 'farm.additional.expense'
    _description = 'Əlavə Xərclər'

    name = fields.Char('Xərc Adı', required=True)
    description = fields.Text('Açıqlama')
    amount = fields.Float('Məbləğ', required=True)
    expense_type = fields.Selection([
        ('transport', 'Nəqliyyat'),
        ('fuel', 'Yanacaq'),
        ('equipment', 'Avadanlıq'),
        ('material', 'Material'),
        ('service', 'Xidmət'),
        ('maintenance', 'Təmir'),
        ('other', 'Digər')
    ], string='Xərc Növü', required=True, default='other')
    expense_date = fields.Date('Xərc Tarixi', default=fields.Date.today)

    # Əməliyyat növləri üçün Many2one sahələr
    plowing_id = fields.Many2one('farm.plowing', string='Şumlama', ondelete='cascade')
    planting_id = fields.Many2one('farm.planting', string='Əkin', ondelete='cascade')
    irrigation_id = fields.Many2one('farm.irrigation', string='Sulama', ondelete='cascade')
    fertilizing_id = fields.Many2one('farm.fertilizing', string='Gübrələmə', ondelete='cascade')
    treatment_id = fields.Many2one('farm.treatment', string='Dərmanlama', ondelete='cascade')
    pruning_id = fields.Many2one('farm.pruning', string='Budama', ondelete='cascade')
    harvest_id = fields.Many2one('farm.harvest', string='Yığım', ondelete='cascade')
    cold_storage_id = fields.Many2one('farm.cold.storage', string='Soyuducu Anbarı', ondelete='cascade')

    @api.constrains('amount')
    def _check_amount(self):
        for expense in self:
            if expense.amount < 0:
                raise ValidationError('Xərc məbləği mənfi ola bilməz!')

class FarmPruning(models.Model):
    """Budama Əməliyyatı"""
    _name = 'farm.pruning'
    _description = 'Budama'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'pruning_date desc'

    name = fields.Char('Əməliyyat Adı', required=True, compute='_compute_name', default='Budama', tracking=True)
    pruning_date = fields.Datetime('Tarix', required=True, default=fields.Datetime.now, tracking=True)

    field_id = fields.Many2one('farm.field', string='Sahə', ondelete='cascade', required=True, tracking=True)
    parcel_id = fields.Many2one('farm.parcel', string='Parsel', domain="[('field_id', '=', field_id)]", ondelete='cascade', tracking=True)
    row_id = fields.Many2one('farm.row', string='Cərgə', domain="[('parcel_id', '=', parcel_id)]", ondelete='cascade', tracking=True)
    
    # Budama məlumatları
    pruned_tree_count = fields.Integer('Budanan Ağac Sayı', required=True, tracking=True)
    pruning_type = fields.Selection([
        ('summerpruning', 'Yaz budaması'),
        ('winterpruning', 'Qış budaması'),
    ], string='Budama Növü', required=True, tracking=True)
    
    # Alətlər və işçilər
    worker_line_ids = fields.One2many('farm.pruning.worker', 'pruning_id', string='İşçi Sətirləri')
    total_worker_cost = fields.Float('İşçi Xərci', compute='_compute_total_worker_cost', store=True)
    
    # Əlavə xərclər
    additional_expense_ids = fields.One2many('farm.additional.expense', 'pruning_id', string='Əlavə Xərclər')
    total_additional_cost = fields.Float('Əlavə Xərc', compute='_compute_total_additional_cost', store=True)

    # Ümumi xərc
    total_cost = fields.Float('Ümumi Xərc', compute='_compute_total_cost', store=True)

    notes = fields.Text('Qeydlər')
    active = fields.Boolean('Aktiv', default=True)

    @api.depends('worker_line_ids.amount')
    def _compute_total_worker_cost(self):
        for record in self:
            record.total_worker_cost = sum(line.amount for line in record.worker_line_ids)

    @api.depends('additional_expense_ids.amount')
    def _compute_total_additional_cost(self):
        for record in self:
            record.total_additional_cost = sum(expense.amount for expense in record.additional_expense_ids)

    @api.depends('total_worker_cost', 'total_additional_cost')
    def _compute_total_cost(self):
        for record in self:
            record.total_cost = record.total_worker_cost + record.total_additional_cost

    @api.constrains('pruned_tree_count')
    def _check_positive_values(self):
        for record in self:
            if record.pruned_tree_count <= 0:
                raise ValidationError('Budanan ağac sayı müsbət olmalıdır!')

    @api.depends('field_id', 'parcel_id', 'pruning_date')
    def _compute_name(self):
        for record in self:
            if  record.parcel_id and record.field_id and record.pruning_date:
                record.name = f" Budama - {record.field_id.name} - {record.parcel_id.name} - ({record.pruning_date})"
            elif record.field_id and record.pruning_date:
                record.name = f" Budama - {record.field_id.name} - ({record.pruning_date})"
            else:
                record.name = 'Yeni Budama Qeydi'


class FarmHarvest(models.Model):
    """Yığım Əməliyyatı"""
    _name = 'farm.harvest'
    _description = 'Yığım'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'harvest_date desc'

    name = fields.Char('Əməliyyat Adı', required=True, compute='_compute_name', default='Yığım', tracking=True)
    harvest_date = fields.Datetime('Yığım Tarixi', required=True, default=fields.Datetime.now, tracking=True)

    field_id = fields.Many2one('farm.field', string='Sahə', ondelete='cascade', required=True, tracking=True)
    parcel_id = fields.Many2one('farm.parcel', string='Parsel', domain="[('field_id', '=', field_id)]", ondelete='cascade', tracking=True)
    row_id = fields.Many2one('farm.row', string='Cərgə', domain="[('parcel_id', '=', parcel_id)]", ondelete='cascade', tracking=True)
    
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
    total_worker_cost = fields.Float('İşçi Xərci', compute='_compute_total_worker_cost', store=True)
    
    # Əlavə xərclər
    additional_expense_ids = fields.One2many('farm.additional.expense', 'harvest_id', string='Əlavə Xərclər')
    total_additional_cost = fields.Float('Əlavə Xərc', compute='_compute_total_additional_cost', store=True)

    # Ümumi xərc
    total_cost = fields.Float('Ümumi Xərc', compute='_compute_total_cost', store=True)

    # Xərclər
    cost_per_kg = fields.Float('Kq-a Görə Qiymət')
    # total_cost = fields.Float('Ümumi Xərc', compute='_compute_total_cost', store=True)
    
    # Qeydlər
    notes = fields.Text('Qeydlər')
    active = fields.Boolean('Aktiv', default=True)

    @api.depends('worker_line_ids.amount')
    def _compute_total_worker_cost(self):
        for record in self:
            record.total_worker_cost = sum(line.amount for line in record.worker_line_ids)

    @api.depends('additional_expense_ids.amount')
    def _compute_total_additional_cost(self):
        for record in self:
            record.total_additional_cost = sum(expense.amount for expense in record.additional_expense_ids)

    @api.depends('total_worker_cost', 'total_additional_cost')
    def _compute_total_cost(self):
        for record in self:
            record.total_cost = record.total_worker_cost + record.total_additional_cost

    @api.constrains('tree_count', 'quantity_kg')
    def _check_positive_values(self):
        for record in self:
            if record.tree_count <= 0:
                raise ValidationError('Ağac sayı müsbət olmalıdır!')
            if record.quantity_kg <= 0:
                raise ValidationError('Məhsul miqdarı müsbət olmalıdır!')
            
    @api.depends('field_id', 'parcel_id', 'harvest_date')
    def _compute_name(self):
        for record in self:
            if  record.parcel_id and record.field_id and record.harvest_date:
                record.name = f" Yığım - {record.field_id.name} - {record.parcel_id.name} - ({record.harvest_date})"
            elif record.field_id and record.harvest_date:
                record.name = f" Yığım - {record.field_id.name} - ({record.harvest_date})"
            else:
                record.name = 'Yeni Yığım Qeydi'

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
    
    field_id = fields.Many2one('farm.field', string='Sahə', ondelete='cascade', required=True, tracking=True)
    parcel_id = fields.Many2one('farm.parcel', string='Parsel', domain="[('field_id', '=', field_id)]", ondelete='cascade', tracking=True)
    row_id = fields.Many2one('farm.row', string='Cərgə', domain="[('parcel_id', '=', parcel_id)]", ondelete='cascade', tracking=True)
    
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

    name = fields.Char('Qeyd Adı', required=True, compute='_compute_name', default='Zərərçəkmiş Ağaclar', tracking=True)
    damage_date = fields.Datetime('Tarix', required=True, default=fields.Datetime.now, tracking=True)

    field_id = fields.Many2one('farm.field', string='Sahə', ondelete='cascade', required=True, tracking=True)
    parcel_id = fields.Many2one('farm.parcel', string='Parsel', domain="[('field_id', '=', field_id)]", ondelete='cascade', tracking=True)
    row_id = fields.Many2one('farm.row', string='Cərgə', domain="[('parcel_id', '=', parcel_id)]", ondelete='cascade', tracking=True)
    
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

    @api.depends('field_id', 'parcel_id', 'treatment_date')
    def _compute_name(self):
        for record in self:
            if  record.parcel_id and record.field_id and record.treatment_date:
                record.name = f" Zərərçəkmiş Ağaclar - {record.field_id.name} - {record.parcel_id.name} - ({record.treatment_date})"
            elif record.field_id and record.treatment_date:
                record.name = f" Zərərçəkmiş Ağaclar - {record.field_id.name} - ({record.treatment_date})"
            else:
                record.name = 'Yeni Zərərçəkmiş Ağaclar Qeydi'

class FarmColdStorage(models.Model):
    """Malların Soyuducuya Yerləşdirilməsi"""
    _name = 'farm.cold.storage'
    _description = 'Soyuducu Anbarı'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'storage_date desc'

    name = fields.Char('Əməliyyat Adı', required=True, compute='_compute_name', default='Soyuducuya Yerləşdirmə', tracking=True)
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
    total_worker_cost = fields.Float('İşçi Xərci', compute='_compute_total_worker_cost', store=True)
    
    # Əlavə xərclər
    additional_expense_ids = fields.One2many('farm.additional.expense', 'cold_storage_id', string='Əlavə Xərclər')
    total_additional_cost = fields.Float('Əlavə Xərc', compute='_compute_total_additional_cost', store=True)

    # Ümumi xərc
    total_cost = fields.Float('Ümumi Xərc', compute='_compute_total_cost', store=True)
    
    operator_id = fields.Many2one('res.partner', string='Operator', domain="[('category_id.name', '=', 'Operator')]", tracking=True)
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

    @api.depends('additional_expense_ids.amount')
    def _compute_total_additional_cost(self):
        for record in self:
            record.total_additional_cost = sum(expense.amount for expense in record.additional_expense_ids)

    @api.depends('total_worker_cost', 'total_additional_cost')
    def _compute_total_cost(self):
        for record in self:
            record.total_cost = record.total_worker_cost + record.total_additional_cost

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

    @api.depends('storage_date')
    def _compute_name(self):
        for record in self:
            if  record.storage_date:
                record.name = f" Soyuducu Anbarı - ({record.storage_date})"
            else:
                record.name = 'Yeni Soyuducu Anbarı Qeydi'


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
