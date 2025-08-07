from odoo import models, fields, api
from odoo.tools import sql


class FarmReporting(models.Model):
    """Kənd Təsərrüfatı Hesabatlıq"""
    _name = 'farm.reporting'
    _description = 'Kənd Təsərrüfatı Hesabatlıq'
    _auto = False
    _order = 'operation_date desc'

    # Ümumi məlumatlar
    operation_date = fields.Date('Tarix')
    field_id = fields.Many2one('farm.field', string='Sahə')
    field_name = fields.Char('Sahə Adı')
    parcel_id = fields.Many2one('farm.parcel', string='Parsel')
    parcel_name = fields.Char('Parsel Adı')
    
    # Əməliyyat məlumatları
    operation_type = fields.Selection([
        ('plowing', 'Şumlama'),
        ('planting', 'Əkin'),
        ('irrigation', 'Sulama'),
        ('fertilizing', 'Gübrələmə'),
        ('treatment', 'Dərmanlama'),
        ('pruning', 'Budama'),
        ('harvest', 'Yığım'),
        ('cold_storage', 'Soyuducu'),
        ('purchase', 'Satınalma'),
        ('worker_payment', 'İşçi Ödənişi'),
        ('additional_expense', 'Əlavə Xərc')
    ], string='Əməliyyat Növü')
    
    operation_name = fields.Char('Əməliyyat Adı')
    operation_id = fields.Integer('Əməliyyat ID')
    
    # Maliyyə məlumatları
    total_cost = fields.Float('Ümumi Xərc')
    worker_cost = fields.Float('İşçi Xərci')
    material_cost = fields.Float('Material Xərci')
    additional_cost = fields.Float('Əlavə Xərc')
    
    # İşçi məlumatları
    worker_id = fields.Many2one('farm.worker', string='İşçi')
    worker_name = fields.Char('İşçi Adı')
    worker_hours = fields.Float('İş Saatı')
    hourly_rate = fields.Float('Saatlıq Tarif')
    
    # Satınalma məlumatları
    purchase_order_id = fields.Many2one('purchase.order', string='Satınalma Sifarişi')
    vendor_id = fields.Many2one('res.partner', string='Təchizatçı')
    vendor_name = fields.Char('Təchizatçı Adı')
    
    # Məhsul məlumatları
    product_id = fields.Many2one('product.product', string='Məhsul')
    product_name = fields.Char('Məhsul Adı')
    product_qty = fields.Float('Miqdar')
    product_uom = fields.Char('Ölçü Vahidi')
    unit_price = fields.Float('Vahid Qiymət')
    
    # Zaman filtri
    year = fields.Integer('İl')
    month = fields.Integer('Ay')
    quarter = fields.Integer('Rüb')
    week = fields.Integer('Həftə')
    
    # Kateqoriya
    expense_category = fields.Selection([
        ('operational', 'Əməliyyat'),
        ('material', 'Material'),
        ('labor', 'İşçi'),
        ('equipment', 'Avadanlıq'),
        ('transport', 'Nəqliyyat'),
        ('fuel', 'Yanacaq'),
        ('maintenance', 'Təmir'),
        ('other', 'Digər')
    ], string='Xərc Kateqoriyası')

    def init(self):
        """SQL View yaratmaq üçün"""
        self.env.cr.execute("DROP VIEW IF EXISTS farm_reporting CASCADE")
        self.env.cr.execute("""
            CREATE VIEW farm_reporting AS (
                -- Şumlama əməliyyatları
                SELECT 
                    row_number() OVER () AS id,
                    p.operation_date::date as operation_date,
                    p.field_id,
                    f.name as field_name,
                    p.parcel_id,
                    pr.name as parcel_name,
                    'plowing' as operation_type,
                    p.name as operation_name,
                    p.id as operation_id,
                    p.total_cost,
                    p.total_worker_cost as worker_cost,
                    0.0 as material_cost,
                    p.total_additional_cost as additional_cost,
                    NULL::integer as worker_id,
                    NULL as worker_name,
                    0.0 as worker_hours,
                    0.0 as hourly_rate,
                    NULL::integer as purchase_order_id,
                    NULL::integer as vendor_id,
                    NULL as vendor_name,
                    NULL::integer as product_id,
                    NULL as product_name,
                    0.0 as product_qty,
                    NULL as product_uom,
                    0.0 as unit_price,
                    EXTRACT(year FROM p.operation_date)::integer as year,
                    EXTRACT(month FROM p.operation_date)::integer as month,
                    EXTRACT(quarter FROM p.operation_date)::integer as quarter,
                    EXTRACT(week FROM p.operation_date)::integer as week,
                    'operational' as expense_category
                FROM farm_plowing p
                LEFT JOIN farm_field f ON p.field_id = f.id
                LEFT JOIN farm_parcel pr ON p.parcel_id = pr.id
                
                UNION ALL
                
                -- Əkin əməliyyatları
                SELECT 
                    row_number() OVER () + 1000000 AS id,
                    p.planting_date::date as operation_date,
                    p.field_id,
                    f.name as field_name,
                    p.parcel_id,
                    pr.name as parcel_name,
                    'planting' as operation_type,
                    p.name as operation_name,
                    p.id as operation_id,
                    p.total_cost,
                    p.total_worker_cost as worker_cost,
                    0.0 as material_cost,
                    p.total_additional_cost as additional_cost,
                    NULL::integer as worker_id,
                    NULL as worker_name,
                    0.0 as worker_hours,
                    0.0 as hourly_rate,
                    NULL::integer as purchase_order_id,
                    NULL::integer as vendor_id,
                    NULL as vendor_name,
                    NULL::integer as product_id,
                    NULL as product_name,
                    0.0 as product_qty,
                    NULL as product_uom,
                    0.0 as unit_price,
                    EXTRACT(year FROM p.planting_date)::integer as year,
                    EXTRACT(month FROM p.planting_date)::integer as month,
                    EXTRACT(quarter FROM p.planting_date)::integer as quarter,
                    EXTRACT(week FROM p.planting_date)::integer as week,
                    'operational' as expense_category
                FROM farm_planting p
                LEFT JOIN farm_field f ON p.field_id = f.id
                LEFT JOIN farm_parcel pr ON p.parcel_id = pr.id
                
                UNION ALL
                
                -- Sulama əməliyyatları
                SELECT 
                    row_number() OVER () + 2000000 AS id,
                    i.irrigation_date::date as operation_date,
                    i.field_id,
                    f.name as field_name,
                    i.parcel_id,
                    pr.name as parcel_name,
                    'irrigation' as operation_type,
                    i.name as operation_name,
                    i.id as operation_id,
                    i.total_cost,
                    i.total_worker_cost as worker_cost,
                    0.0 as material_cost,
                    i.total_additional_cost as additional_cost,
                    NULL::integer as worker_id,
                    NULL as worker_name,
                    0.0 as worker_hours,
                    0.0 as hourly_rate,
                    NULL::integer as purchase_order_id,
                    NULL::integer as vendor_id,
                    NULL as vendor_name,
                    NULL::integer as product_id,
                    NULL as product_name,
                    0.0 as product_qty,
                    NULL as product_uom,
                    0.0 as unit_price,
                    EXTRACT(year FROM i.irrigation_date)::integer as year,
                    EXTRACT(month FROM i.irrigation_date)::integer as month,
                    EXTRACT(quarter FROM i.irrigation_date)::integer as quarter,
                    EXTRACT(week FROM i.irrigation_date)::integer as week,
                    'operational' as expense_category
                FROM farm_irrigation i
                LEFT JOIN farm_field f ON i.field_id = f.id
                LEFT JOIN farm_parcel pr ON i.parcel_id = pr.id
                
                UNION ALL
                
                -- Gübrələmə əməliyyatları
                SELECT 
                    row_number() OVER () + 3000000 AS id,
                    fe.fertilizing_date::date as operation_date,
                    fe.field_id,
                    f.name as field_name,
                    fe.parcel_id,
                    pr.name as parcel_name,
                    'fertilizing' as operation_type,
                    fe.name as operation_name,
                    fe.id as operation_id,
                    fe.total_cost,
                    fe.total_worker_cost as worker_cost,
                    fe.total_product_cost as material_cost,
                    fe.total_additional_cost as additional_cost,
                    NULL::integer as worker_id,
                    NULL as worker_name,
                    0.0 as worker_hours,
                    0.0 as hourly_rate,
                    NULL::integer as purchase_order_id,
                    NULL::integer as vendor_id,
                    NULL as vendor_name,
                    NULL::integer as product_id,
                    NULL as product_name,
                    0.0 as product_qty,
                    NULL as product_uom,
                    0.0 as unit_price,
                    EXTRACT(year FROM fe.fertilizing_date)::integer as year,
                    EXTRACT(month FROM fe.fertilizing_date)::integer as month,
                    EXTRACT(quarter FROM fe.fertilizing_date)::integer as quarter,
                    EXTRACT(week FROM fe.fertilizing_date)::integer as week,
                    'operational' as expense_category
                FROM farm_fertilizing fe
                LEFT JOIN farm_field f ON fe.field_id = f.id
                LEFT JOIN farm_parcel pr ON fe.parcel_id = pr.id
                
                UNION ALL
                
                -- Dərmanlama əməliyyatları
                SELECT 
                    row_number() OVER () + 4000000 AS id,
                    t.treatment_date::date as operation_date,
                    t.field_id,
                    f.name as field_name,
                    t.parcel_id,
                    pr.name as parcel_name,
                    'treatment' as operation_type,
                    t.name as operation_name,
                    t.id as operation_id,
                    t.total_cost,
                    t.total_worker_cost as worker_cost,
                    t.total_product_cost as material_cost,
                    t.total_additional_cost as additional_cost,
                    NULL::integer as worker_id,
                    NULL as worker_name,
                    0.0 as worker_hours,
                    0.0 as hourly_rate,
                    NULL::integer as purchase_order_id,
                    NULL::integer as vendor_id,
                    NULL as vendor_name,
                    NULL::integer as product_id,
                    NULL as product_name,
                    0.0 as product_qty,
                    NULL as product_uom,
                    0.0 as unit_price,
                    EXTRACT(year FROM t.treatment_date)::integer as year,
                    EXTRACT(month FROM t.treatment_date)::integer as month,
                    EXTRACT(quarter FROM t.treatment_date)::integer as quarter,
                    EXTRACT(week FROM t.treatment_date)::integer as week,
                    'operational' as expense_category
                FROM farm_treatment t
                LEFT JOIN farm_field f ON t.field_id = f.id
                LEFT JOIN farm_parcel pr ON t.parcel_id = pr.id
                
                UNION ALL
                
                -- Budama əməliyyatları
                SELECT 
                    row_number() OVER () + 5000000 AS id,
                    pr.pruning_date::date as operation_date,
                    pr.field_id,
                    f.name as field_name,
                    pr.parcel_id,
                    pa.name as parcel_name,
                    'pruning' as operation_type,
                    pr.name as operation_name,
                    pr.id as operation_id,
                    pr.total_cost,
                    pr.total_worker_cost as worker_cost,
                    0.0 as material_cost,
                    pr.total_additional_cost as additional_cost,
                    NULL::integer as worker_id,
                    NULL as worker_name,
                    0.0 as worker_hours,
                    0.0 as hourly_rate,
                    NULL::integer as purchase_order_id,
                    NULL::integer as vendor_id,
                    NULL as vendor_name,
                    NULL::integer as product_id,
                    NULL as product_name,
                    0.0 as product_qty,
                    NULL as product_uom,
                    0.0 as unit_price,
                    EXTRACT(year FROM pr.pruning_date)::integer as year,
                    EXTRACT(month FROM pr.pruning_date)::integer as month,
                    EXTRACT(quarter FROM pr.pruning_date)::integer as quarter,
                    EXTRACT(week FROM pr.pruning_date)::integer as week,
                    'operational' as expense_category
                FROM farm_pruning pr
                LEFT JOIN farm_field f ON pr.field_id = f.id
                LEFT JOIN farm_parcel pa ON pr.parcel_id = pa.id
                
                UNION ALL
                
                -- Yığım əməliyyatları
                SELECT 
                    row_number() OVER () + 6000000 AS id,
                    h.harvest_date::date as operation_date,
                    h.field_id,
                    f.name as field_name,
                    h.parcel_id,
                    pr.name as parcel_name,
                    'harvest' as operation_type,
                    h.name as operation_name,
                    h.id as operation_id,
                    h.total_cost,
                    h.total_worker_cost as worker_cost,
                    0.0 as material_cost,
                    h.total_additional_cost as additional_cost,
                    NULL::integer as worker_id,
                    NULL as worker_name,
                    0.0 as worker_hours,
                    0.0 as hourly_rate,
                    NULL::integer as purchase_order_id,
                    NULL::integer as vendor_id,
                    NULL as vendor_name,
                    NULL::integer as product_id,
                    NULL as product_name,
                    h.quantity_kg as product_qty,
                    'kq' as product_uom,
                    0.0 as unit_price,
                    EXTRACT(year FROM h.harvest_date)::integer as year,
                    EXTRACT(month FROM h.harvest_date)::integer as month,
                    EXTRACT(quarter FROM h.harvest_date)::integer as quarter,
                    EXTRACT(week FROM h.harvest_date)::integer as week,
                    'operational' as expense_category
                FROM farm_harvest h
                LEFT JOIN farm_field f ON h.field_id = f.id
                LEFT JOIN farm_parcel pr ON h.parcel_id = pr.id
                
                UNION ALL
                
                -- Soyuducu əməliyyatları
                SELECT 
                    row_number() OVER () + 7000000 AS id,
                    cs.entry_time::date as operation_date,
                    NULL::integer as field_id,
                    NULL as field_name,
                    NULL::integer as parcel_id,
                    NULL as parcel_name,
                    'cold_storage' as operation_type,
                    cs.name as operation_name,
                    cs.id as operation_id,
                    cs.total_cost,
                    cs.total_worker_cost as worker_cost,
                    0.0 as material_cost,
                    cs.total_additional_cost as additional_cost,
                    NULL::integer as worker_id,
                    NULL as worker_name,
                    0.0 as worker_hours,
                    0.0 as hourly_rate,
                    NULL::integer as purchase_order_id,
                    NULL::integer as vendor_id,
                    NULL as vendor_name,
                    NULL::integer as product_id,
                    NULL as product_name,
                    cs.quantity_kg as product_qty,
                    'kq' as product_uom,
                    0.0 as unit_price,
                    EXTRACT(year FROM cs.entry_time)::integer as year,
                    EXTRACT(month FROM cs.entry_time)::integer as month,
                    EXTRACT(quarter FROM cs.entry_time)::integer as quarter,
                    EXTRACT(week FROM cs.entry_time)::integer as week,
                    'operational' as expense_category
                FROM farm_cold_storage cs
                
                UNION ALL
                
                -- İşçi ödənişləri
                SELECT 
                    row_number() OVER () + 8000000 AS id,
                    wp.payment_date as operation_date,
                    NULL::integer as field_id,
                    NULL as field_name,
                    NULL::integer as parcel_id,
                    NULL as parcel_name,
                    'worker_payment' as operation_type,
                    CONCAT('İşçi Ödənişi - ', w.name) as operation_name,
                    wp.id as operation_id,
                    wp.amount as total_cost,
                    wp.amount as worker_cost,
                    0.0 as material_cost,
                    0.0 as additional_cost,
                    wp.worker_id,
                    w.name as worker_name,
                    0.0 as worker_hours,
                    0.0 as hourly_rate,
                    NULL::integer as purchase_order_id,
                    NULL::integer as vendor_id,
                    NULL as vendor_name,
                    NULL::integer as product_id,
                    NULL as product_name,
                    0.0 as product_qty,
                    NULL as product_uom,
                    0.0 as unit_price,
                    EXTRACT(year FROM wp.payment_date)::integer as year,
                    EXTRACT(month FROM wp.payment_date)::integer as month,
                    EXTRACT(quarter FROM wp.payment_date)::integer as quarter,
                    EXTRACT(week FROM wp.payment_date)::integer as week,
                    'labor' as expense_category
                FROM farm_worker_payment wp
                LEFT JOIN farm_worker w ON wp.worker_id = w.id
                
                UNION ALL
                
                -- Satınalmalar
                SELECT 
                    row_number() OVER () + 9000000 AS id,
                    po.date_order::date as operation_date,
                    po.farm_field_id as field_id,
                    f.name as field_name,
                    NULL::integer as parcel_id,
                    NULL as parcel_name,
                    'purchase' as operation_type,
                    po.name as operation_name,
                    po.id as operation_id,
                    po.amount_total as total_cost,
                    0.0 as worker_cost,
                    po.amount_total as material_cost,
                    0.0 as additional_cost,
                    NULL::integer as worker_id,
                    NULL as worker_name,
                    0.0 as worker_hours,
                    0.0 as hourly_rate,
                    po.id as purchase_order_id,
                    po.partner_id as vendor_id,
                    pt.name as vendor_name,
                    NULL::integer as product_id,
                    NULL as product_name,
                    0.0 as product_qty,
                    NULL as product_uom,
                    0.0 as unit_price,
                    EXTRACT(year FROM po.date_order)::integer as year,
                    EXTRACT(month FROM po.date_order)::integer as month,
                    EXTRACT(quarter FROM po.date_order)::integer as quarter,
                    EXTRACT(week FROM po.date_order)::integer as week,
                    'material' as expense_category
                FROM purchase_order po
                LEFT JOIN farm_field f ON po.farm_field_id = f.id
                LEFT JOIN res_partner pt ON po.partner_id = pt.id
                WHERE po.state IN ('purchase', 'done')
                
                UNION ALL
                
                -- Əlavə xərclər
                SELECT 
                    row_number() OVER () + 10000000 AS id,
                    ae.expense_date as operation_date,
                    NULL::integer as field_id,
                    NULL as field_name,
                    NULL::integer as parcel_id,
                    NULL as parcel_name,
                    'additional_expense' as operation_type,
                    ae.name as operation_name,
                    ae.id as operation_id,
                    ae.amount as total_cost,
                    0.0 as worker_cost,
                    0.0 as material_cost,
                    ae.amount as additional_cost,
                    NULL::integer as worker_id,
                    NULL as worker_name,
                    0.0 as worker_hours,
                    0.0 as hourly_rate,
                    NULL::integer as purchase_order_id,
                    NULL::integer as vendor_id,
                    NULL as vendor_name,
                    NULL::integer as product_id,
                    NULL as product_name,
                    0.0 as product_qty,
                    NULL as product_uom,
                    0.0 as unit_price,
                    EXTRACT(year FROM ae.expense_date)::integer as year,
                    EXTRACT(month FROM ae.expense_date)::integer as month,
                    EXTRACT(quarter FROM ae.expense_date)::integer as quarter,
                    EXTRACT(week FROM ae.expense_date)::integer as week,
                    CASE 
                        WHEN ae.expense_type = 'transport' THEN 'transport'
                        WHEN ae.expense_type = 'fuel' THEN 'fuel'
                        WHEN ae.expense_type = 'equipment' THEN 'equipment'
                        WHEN ae.expense_type = 'maintenance' THEN 'maintenance'
                        ELSE 'other'
                    END as expense_category
                FROM farm_additional_expense ae
                WHERE ae.expense_date IS NOT NULL
            )
        """)


class FarmOperationReport(models.Model):
    """Əməliyyat Hesabatı"""
    _name = 'farm.operation.report'
    _description = 'Əməliyyat Hesabatı'
    _auto = False
    _order = 'operation_date desc'

    operation_date = fields.Date('Tarix')
    operation_type = fields.Selection([
        ('plowing', 'Şumlama'),
        ('planting', 'Əkin'),
        ('irrigation', 'Sulama'),
        ('fertilizing', 'Gübrələmə'),
        ('treatment', 'Dərmanlama'),
        ('pruning', 'Budama'),
        ('harvest', 'Yığım'),
        ('cold_storage', 'Soyuducu')
    ], string='Əməliyyat Növü')
    
    field_name = fields.Char('Sahə')
    parcel_name = fields.Char('Parsel')
    total_cost = fields.Float('Ümumi Xərc')
    worker_cost = fields.Float('İşçi Xərci')
    material_cost = fields.Float('Material Xərci')
    additional_cost = fields.Float('Əlavə Xərc')
    operation_count = fields.Integer('Əməliyyat Sayı')
    
    year = fields.Integer('İl')
    month = fields.Integer('Ay')
    quarter = fields.Integer('Rüb')

    def init(self):
        self.env.cr.execute("DROP VIEW IF EXISTS farm_operation_report CASCADE")
        self.env.cr.execute("""
            CREATE VIEW farm_operation_report AS (
                SELECT 
                    row_number() OVER () AS id,
                    operation_date,
                    operation_type,
                    field_name,
                    parcel_name,
                    SUM(total_cost) as total_cost,
                    SUM(worker_cost) as worker_cost,
                    SUM(material_cost) as material_cost,
                    SUM(additional_cost) as additional_cost,
                    COUNT(*) as operation_count,
                    year,
                    month,
                    quarter
                FROM farm_reporting
                WHERE operation_type IN ('plowing', 'planting', 'irrigation', 'fertilizing', 'treatment', 'pruning', 'harvest', 'cold_storage')
                GROUP BY operation_date, operation_type, field_name, parcel_name, year, month, quarter
            )
        """)


class FarmWorkerReport(models.Model):
    """İşçi Hesabatı"""
    _name = 'farm.worker.report'
    _description = 'İşçi Hesabatı'
    _auto = False
    _order = 'worker_name, operation_date desc'

    worker_name = fields.Char('İşçi Adı')
    operation_date = fields.Date('Tarix')
    operation_type = fields.Selection([
        ('plowing', 'Şumlama'),
        ('planting', 'Əkin'),
        ('irrigation', 'Sulama'),
        ('fertilizing', 'Gübrələmə'),
        ('treatment', 'Dərmanlama'),
        ('pruning', 'Budama'),
        ('harvest', 'Yığım'),
        ('cold_storage', 'Soyuducu'),
        ('worker_payment', 'İşçi Ödənişi')
    ], string='Əməliyyat Növü')
    
    total_earned = fields.Float('Qazanılan Məbləğ')
    total_paid = fields.Float('Ödənilən Məbləğ')
    balance = fields.Float('Balans')
    hours_worked = fields.Float('İş Saatı')
    hourly_rate = fields.Float('Saatlıq Tarif')
    
    year = fields.Integer('İl')
    month = fields.Integer('Ay')
    quarter = fields.Integer('Rüb')

    def init(self):
        self.env.cr.execute("DROP VIEW IF EXISTS farm_worker_report CASCADE")
        self.env.cr.execute("""
            CREATE VIEW farm_worker_report AS (
                -- İşçi qazancları (bütün əməliyyatlardan)
                SELECT 
                    row_number() OVER () AS id,
                    w.name as worker_name,
                    CURRENT_DATE as operation_date,
                    'summary' as operation_type,
                    w.total_earned,
                    w.total_paid,
                    w.balance,
                    w.total_hours as hours_worked,
                    w.hourly_rate,
                    EXTRACT(year FROM CURRENT_DATE)::integer as year,
                    EXTRACT(month FROM CURRENT_DATE)::integer as month,
                    EXTRACT(quarter FROM CURRENT_DATE)::integer as quarter
                FROM farm_worker w
                
                UNION ALL
                
                -- İşçi ödənişləri
                SELECT 
                    row_number() OVER () + 1000000 AS id,
                    w.name as worker_name,
                    wp.payment_date as operation_date,
                    'worker_payment' as operation_type,
                    0.0 as total_earned,
                    wp.amount as total_paid,
                    -wp.amount as balance,
                    0.0 as hours_worked,
                    0.0 as hourly_rate,
                    EXTRACT(year FROM wp.payment_date)::integer as year,
                    EXTRACT(month FROM wp.payment_date)::integer as month,
                    EXTRACT(quarter FROM wp.payment_date)::integer as quarter
                FROM farm_worker_payment wp
                LEFT JOIN farm_worker w ON wp.worker_id = w.id
            )
        """)


class FarmPurchaseReport(models.Model):
    """Satınalma Hesabatı"""
    _name = 'farm.purchase.report'
    _description = 'Satınalma Hesabatı'
    _auto = False
    _order = 'order_date desc'

    order_date = fields.Date('Sifariş Tarixi')
    order_name = fields.Char('Sifariş Nömrəsi')
    vendor_name = fields.Char('Təchizatçı')
    field_name = fields.Char('Sahə')
    product_name = fields.Char('Məhsul')
    quantity = fields.Float('Miqdar')
    unit_price = fields.Float('Vahid Qiymət')
    total_amount = fields.Float('Ümumi Məbləğ')
    state = fields.Char('Vəziyyət')
    
    year = fields.Integer('İl')
    month = fields.Integer('Ay')
    quarter = fields.Integer('Rüb')

    def init(self):
        self.env.cr.execute("DROP VIEW IF EXISTS farm_purchase_report CASCADE")
        self.env.cr.execute("""
            CREATE VIEW farm_purchase_report AS (
                SELECT 
                    row_number() OVER () AS id,
                    po.date_order::date as order_date,
                    po.name as order_name,
                    pt.name as vendor_name,
                    f.name as field_name,
                    pr.name as product_name,
                    pol.product_qty as quantity,
                    pol.price_unit as unit_price,
                    pol.price_subtotal as total_amount,
                    po.state,
                    EXTRACT(year FROM po.date_order)::integer as year,
                    EXTRACT(month FROM po.date_order)::integer as month,
                    EXTRACT(quarter FROM po.date_order)::integer as quarter
                FROM purchase_order po
                LEFT JOIN purchase_order_line pol ON po.id = pol.order_id
                LEFT JOIN product_product pp ON pol.product_id = pp.id
                LEFT JOIN product_template pr ON pp.product_tmpl_id = pr.id
                LEFT JOIN res_partner pt ON po.partner_id = pt.id
                LEFT JOIN farm_field f ON po.farm_field_id = f.id
                WHERE po.state IN ('purchase', 'done')
            )
        """)


class FarmExpenseReport(models.Model):
    """Xərc Hesabatı"""
    _name = 'farm.expense.report'
    _description = 'Xərc Hesabatı'
    _auto = False
    _order = 'expense_date desc'

    expense_date = fields.Date('Xərc Tarixi')
    expense_name = fields.Char('Xərc Adı')
    expense_type = fields.Selection([
        ('transport', 'Nəqliyyat'),
        ('fuel', 'Yanacaq'),
        ('equipment', 'Avadanlıq'),
        ('material', 'Material'),
        ('service', 'Xidmət'),
        ('maintenance', 'Təmir'),
        ('other', 'Digər')
    ], string='Xərc Növü')
    
    amount = fields.Float('Məbləğ')
    description = fields.Text('Açıqlama')
    operation_type = fields.Char('Əlaqəli Əməliyyat')
    
    year = fields.Integer('İl')
    month = fields.Integer('Ay')
    quarter = fields.Integer('Rüb')

    def init(self):
        self.env.cr.execute("DROP VIEW IF EXISTS farm_expense_report CASCADE")
        self.env.cr.execute("""
            CREATE VIEW farm_expense_report AS (
                SELECT 
                    ae.id,
                    ae.expense_date,
                    ae.name as expense_name,
                    ae.expense_type,
                    ae.amount,
                    ae.description,
                    CASE 
                        WHEN ae.plowing_id IS NOT NULL THEN 'Şumlama'
                        WHEN ae.planting_id IS NOT NULL THEN 'Əkin'
                        WHEN ae.irrigation_id IS NOT NULL THEN 'Sulama'
                        WHEN ae.fertilizing_id IS NOT NULL THEN 'Gübrələmə'
                        WHEN ae.treatment_id IS NOT NULL THEN 'Dərmanlama'
                        WHEN ae.pruning_id IS NOT NULL THEN 'Budama'
                        WHEN ae.harvest_id IS NOT NULL THEN 'Yığım'
                        WHEN ae.cold_storage_id IS NOT NULL THEN 'Soyuducu'
                        ELSE 'Ümumi'
                    END as operation_type,
                    EXTRACT(year FROM ae.expense_date)::integer as year,
                    EXTRACT(month FROM ae.expense_date)::integer as month,
                    EXTRACT(quarter FROM ae.expense_date)::integer as quarter
                FROM farm_additional_expense ae
                WHERE ae.expense_date IS NOT NULL
            )
        """)


class FarmFinancialSummary(models.Model):
    """Maliyyə Xülasəsi"""
    _name = 'farm.financial.summary'
    _description = 'Maliyyə Xülasəsi'
    _auto = False
    _order = 'period_year desc, period_month desc'

    period_year = fields.Integer('İl')
    period_month = fields.Integer('Ay')
    period_name = fields.Char('Dövr')
    
    # Əməliyyat xərcləri
    operational_cost = fields.Float('Əməliyyat Xərcləri')
    plowing_cost = fields.Float('Şumlama Xərci')
    planting_cost = fields.Float('Əkin Xərci')
    irrigation_cost = fields.Float('Sulama Xərci')
    fertilizing_cost = fields.Float('Gübrələmə Xərci')
    treatment_cost = fields.Float('Dərmanlama Xərci')
    pruning_cost = fields.Float('Budama Xərci')
    harvest_cost = fields.Float('Yığım Xərci')
    cold_storage_cost = fields.Float('Soyuducu Xərci')
    
    # Digər xərclər
    worker_payment_cost = fields.Float('İşçi Ödənişləri')
    purchase_cost = fields.Float('Satınalma Xərcləri')
    additional_expense_cost = fields.Float('Əlavə Xərclər')
    
    # Ümumi
    total_cost = fields.Float('Ümumi Xərc')
    operation_count = fields.Integer('Əməliyyat Sayı')

    def init(self):
        self.env.cr.execute("DROP VIEW IF EXISTS farm_financial_summary CASCADE")
        self.env.cr.execute("""
            CREATE VIEW farm_financial_summary AS (
                SELECT 
                    row_number() OVER () AS id,
                    year as period_year,
                    month as period_month,
                    CONCAT(month, '/', year) as period_name,
                    
                    SUM(CASE WHEN operation_type IN ('plowing', 'planting', 'irrigation', 'fertilizing', 'treatment', 'pruning', 'harvest', 'cold_storage') THEN total_cost ELSE 0 END) as operational_cost,
                    
                    SUM(CASE WHEN operation_type = 'plowing' THEN total_cost ELSE 0 END) as plowing_cost,
                    SUM(CASE WHEN operation_type = 'planting' THEN total_cost ELSE 0 END) as planting_cost,
                    SUM(CASE WHEN operation_type = 'irrigation' THEN total_cost ELSE 0 END) as irrigation_cost,
                    SUM(CASE WHEN operation_type = 'fertilizing' THEN total_cost ELSE 0 END) as fertilizing_cost,
                    SUM(CASE WHEN operation_type = 'treatment' THEN total_cost ELSE 0 END) as treatment_cost,
                    SUM(CASE WHEN operation_type = 'pruning' THEN total_cost ELSE 0 END) as pruning_cost,
                    SUM(CASE WHEN operation_type = 'harvest' THEN total_cost ELSE 0 END) as harvest_cost,
                    SUM(CASE WHEN operation_type = 'cold_storage' THEN total_cost ELSE 0 END) as cold_storage_cost,
                    
                    SUM(CASE WHEN operation_type = 'worker_payment' THEN total_cost ELSE 0 END) as worker_payment_cost,
                    SUM(CASE WHEN operation_type = 'purchase' THEN total_cost ELSE 0 END) as purchase_cost,
                    SUM(CASE WHEN operation_type = 'additional_expense' THEN total_cost ELSE 0 END) as additional_expense_cost,
                    
                    SUM(total_cost) as total_cost,
                    COUNT(*) as operation_count
                    
                FROM farm_reporting
                GROUP BY year, month
            )
        """)
