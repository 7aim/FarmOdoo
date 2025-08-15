from odoo import models, fields, api
from datetime import datetime, timedelta


class FarmDashboardWizard(models.TransientModel):
    """Sahə Dashboard Wizard - Real vaxtda məlumat göstərmək üçün"""
    _name = 'farm.dashboard.wizard'
    _description = 'Sahə Dashboard Wizard'

    field_id = fields.Many2one('farm.field', string='Sahə', required=True)
    year = fields.Integer('İl', default=lambda self: datetime.now().year, required=True)
    month = fields.Selection([
        ('1', 'Yanvar'), ('2', 'Fevral'), ('3', 'Mart'), ('4', 'Aprel'),
        ('5', 'May'), ('6', 'İyun'), ('7', 'İyul'), ('8', 'Avqust'),
        ('9', 'Sentyabr'), ('10', 'Oktyabr'), ('11', 'Noyabr'), ('12', 'Dekabr'),
        ('all', 'Bütün İl')
    ], string='Ay', default=lambda self: str(datetime.now().month), required=True)
    
    # Filtr parametrləri
    date_filter = fields.Selection([
        ('month', 'Ay üzrə'),
        ('year', 'İl üzrə'),
        ('custom', 'Özel Tarix')
    ], string='📅 Filtr Növü', default='month', required=True)
    date_from = fields.Date('📅 Başlanğıc Tarix')
    date_to = fields.Date('📅 Bitmə Tarix')
    
    # Ağac məlumatları
    total_parcels = fields.Integer('📍 Parsel Sayı', readonly=True)
    total_rows = fields.Integer('📏 Cərgə Sayı', readonly=True)
    total_trees = fields.Integer('🌳 Ağac Sayı', readonly=True)
    area_hectare = fields.Float('📐 Sahə Ölçüsü (Hektar)', readonly=True)
    
    # Ümumi xərclər
    total_expenses = fields.Float('💰 Ümumi Xərclər (AZN)', readonly=True)
    
    # Gübrə məlumatları
    total_fertilizer_cost = fields.Float('🌱 Gübrə Xərci (AZN)', readonly=True)
    last_fertilizing_date = fields.Date('🗓️ Son Gübrələmə Tarixi', readonly=True)
    
    # Su / Sulama məlumatları
    total_water_cost = fields.Float('💧 Su Xərci (AZN)', readonly=True)
    total_water_liters = fields.Float('💧 İstifadə Olunan Su', readonly=True)
    last_irrigation_date = fields.Date('🗓️ Son Sulama Tarixi', readonly=True)
    total_irrigation_count = fields.Integer('🔄 Sulama Sayı', readonly=True)
    
    # İşçi xərcləri (detallı)
    total_worker_cost = fields.Float('👷 Ümumi İşçi Xərci (AZN)', readonly=True)
    total_skilled_worker_cost = fields.Float('👨‍🔧 Fəhlə Xərci (AZN)', readonly=True)
    total_general_worker_cost = fields.Float('👷‍♂️ İşçi Xərci (AZN)', readonly=True)
    
    # Material xərcləri
    total_material_cost = fields.Float('🔧 Material Xərci (AZN)', readonly=True)
    
    # Traktor xərcləri
    total_tractor_cost = fields.Float('🚜 Traktor Xərci (AZN)', readonly=True)
    
    # Diesel xərcləri
    total_diesel_cost = fields.Float('⛽ Diesel Xərci (AZN)', readonly=True)
    
    # Hotel xərcləri
    total_hotel_cost = fields.Float('🏨 Hotel Xərci (AZN)', readonly=True)
    
    # Kommunal xərclər
    total_communal_cost = fields.Float('💡 Kommunal Xərc (AZN)', readonly=True)
    
    # Son əməliyyatlar (tam siyahı)
    last_plowing_date = fields.Date('🚜 Son Şumlama', readonly=True)
    last_planting_date = fields.Date('🌱 Son Əkin', readonly=True)
    last_irrigation_date = fields.Date('💧 Son Sulama', readonly=True)
    last_fertilizing_date = fields.Date('🌿 Son Gübrələmə', readonly=True)
    last_treatment_date = fields.Date('💊 Son Müalicə', readonly=True)
    last_pruning_date = fields.Date('✂️ Son Budama', readonly=True)
    last_harvest_date = fields.Date('🍎 Son Məhsul Yığımı', readonly=True)
    
    # Əməliyyat sayları (bu ay)
    plowing_count = fields.Integer('🚜 Şumlama Sayı', readonly=True)
    planting_count = fields.Integer('🌱 Əkin Sayı', readonly=True)
    irrigation_count = fields.Integer('💧 Sulama Sayı', readonly=True)
    fertilizing_count = fields.Integer('🌿 Gübrələmə Sayı', readonly=True)
    treatment_count = fields.Integer('💊 Müalicə Sayı', readonly=True)
    pruning_count = fields.Integer('✂️ Budama Sayı', readonly=True)
    harvest_count = fields.Integer('🍎 Yığım Sayı', readonly=True)
    
    # Təhlükəsizlik məlumatları
    disease_count = fields.Integer('Aktiv Xəstəlik Sayı', readonly=True)
    active_diseases = fields.Text('Aktiv Xəstəliklər', readonly=True)
    
    # Qiymətləndirmə tarixi
    calculation_date = fields.Datetime('Hesablama Tarixi', readonly=True, default=fields.Datetime.now)

    @api.model
    def default_get(self, fields_list):
        """Wizard yaratılanda default məlumatları təyin et"""
        result = super().default_get(fields_list)
        
        # Context-dən field_id al
        field_id = self.env.context.get('default_field_id')
        if field_id:
            result['field_id'] = field_id
        
        return result

    @api.onchange('field_id', 'year', 'month')
    def _onchange_field_data(self):
        """Sahə, il və ya ay dəyişəndə məlumatları yenilə"""
        if self.field_id:
            self._calculate_dashboard_data()

    def _calculate_dashboard_data(self):
        """Dashboard məlumatlarını hesabla"""
        if not self.field_id:
            return
            
        # Tarix filtrini müəyyən et
        if self.date_filter == 'custom' and self.date_from and self.date_to:
            date_from = self.date_from
            date_to = self.date_to
        elif self.date_filter == 'year' or self.month == 'all':
            date_from = fields.Date.from_string(f'{self.year}-01-01')
            date_to = fields.Date.from_string(f'{self.year}-12-31')
        else:
            # Ay üzrə filtr
            month_int = int(self.month) if self.month != 'all' else datetime.now().month
            date_from = fields.Date.from_string(f'{self.year}-{month_int:02d}-01')
            # Ayın son günü
            if month_int == 12:
                date_to = fields.Date.from_string(f'{self.year + 1}-01-01') - timedelta(days=1)
            else:
                date_to = fields.Date.from_string(f'{self.year}-{month_int + 1:02d}-01') - timedelta(days=1)
        
        # Dashboard məlumatlarını hesabla
        dashboard_data = self._get_dashboard_data(
            self.field_id.id, date_from, date_to
        )
        
        # Məlumatları wizard-a yaz
        for field_name, value in dashboard_data.items():
            if hasattr(self, field_name):
                setattr(self, field_name, value)

    def _get_dashboard_data(self, field_id, date_from, date_to):
        """Müəyyən sahə üçün dashboard məlumatlarını hesablayır"""
        field = self.env['farm.field'].browse(field_id)
        if not field.exists():
            return {}
            
        dashboard_data = {
            'field_id': field.id,
            'field_name': field.name,
            'field_code': field.code,
            'area_hectare': field.area_hectare,
            'total_parcels': field.total_parcel,
            'total_rows': field.total_rows,
            'total_trees': field.total_trees,
            'calculation_date': fields.Datetime.now(),
        }
        
        # Ağac sayı 0 olarsa, hesablama etmə
        trees_count = field.total_trees or 1
        
        # Gübrə xərcləri və sayısı
        fertilizing_records = self.env['farm.fertilizing'].search([
            ('field_id', '=', field_id),
            ('fertilizing_date', '>=', date_from),
            ('fertilizing_date', '<=', date_to)
        ])
        
        total_fertilizer_cost = sum(fertilizing_records.mapped('total_cost'))
        dashboard_data.update({
            'total_fertilizer_cost': total_fertilizer_cost,
            'last_fertilizing_date': max(fertilizing_records.mapped('fertilizing_date')) if fertilizing_records else False,
            'fertilizing_count': len(fertilizing_records),
        })
        
        # Sulama xərcləri və su miqdarı
        irrigation_records = self.env['farm.irrigation'].search([
            ('field_id', '=', field_id),
            ('irrigation_date', '>=', date_from),
            ('irrigation_date', '<=', date_to)
        ])
        
        total_water_cost = sum(irrigation_records.mapped('total_cost'))
        total_water_liters = sum(irrigation_records.mapped('water_liters')) if irrigation_records else 0
        dashboard_data.update({
            'total_water_cost': total_water_cost,
            'total_water_liters': total_water_liters,
            'last_irrigation_date': max(irrigation_records.mapped('irrigation_date')) if irrigation_records else False,
            'total_irrigation_count': len(irrigation_records),
            'irrigation_count': len(irrigation_records),
        })
        
        # İşçi xərcləri (bütün əməliyyatlardan)
        total_worker_cost = 0
        total_skilled_worker_cost = 0
        total_general_worker_cost = 0
        
        # Fəhlə xərclərini əlavə xərclərdən hesabla
        all_additional_expenses = self.env['farm.additional.expense'].search([
            ('expense_date', '>=', date_from),
            ('expense_date', '<=', date_to),
            ('expense_type', '=', 'skilled_worker')
        ])
        
        # Fəhlə xərclərini sahə üzrə filtrlə
        for expense in all_additional_expenses:
            # Hansı əməliyyata aid olduğunu yoxla
            field_ids = []
            if expense.plowing_id:
                field_ids.append(expense.plowing_id.field_id.id)
            elif expense.planting_id:
                field_ids.append(expense.planting_id.field_id.id)
            elif expense.irrigation_id:
                field_ids.append(expense.irrigation_id.field_id.id)
            elif expense.fertilizing_id:
                field_ids.append(expense.fertilizing_id.field_id.id)
            elif expense.treatment_id:
                field_ids.append(expense.treatment_id.field_id.id)
            elif expense.pruning_id:
                field_ids.append(expense.pruning_id.field_id.id)
            elif expense.harvest_id:
                field_ids.append(expense.harvest_id.field_id.id)
            
            if field_id in field_ids:
                total_skilled_worker_cost += expense.amount
        
        # Şumlama əməliyyatları
        plowing_records = self.env['farm.plowing'].search([
            ('field_id', '=', field_id),
            ('operation_date', '>=', date_from),
            ('operation_date', '<=', date_to)
        ])
        total_general_worker_cost += sum(plowing_records.mapped('total_worker_cost'))
        last_plowing = max(plowing_records.mapped('operation_date')) if plowing_records else False
        
        # Əkin əməliyyatları
        planting_records = self.env['farm.planting'].search([
            ('field_id', '=', field_id),
            ('planting_date', '>=', date_from),
            ('planting_date', '<=', date_to)
        ])
        total_general_worker_cost += sum(planting_records.mapped('total_worker_cost'))
        last_planting = max(planting_records.mapped('planting_date')) if planting_records else False
        
        # Gübrələmə işçi xərcləri
        total_general_worker_cost += sum(fertilizing_records.mapped('total_worker_cost'))
        
        # Sulama işçi xərcləri
        total_general_worker_cost += sum(irrigation_records.mapped('total_worker_cost'))
        
        # Müalicə əməliyyatları
        treatment_records = self.env['farm.treatment'].search([
            ('field_id', '=', field_id),
            ('treatment_date', '>=', date_from),
            ('treatment_date', '<=', date_to)
        ])
        total_general_worker_cost += sum(treatment_records.mapped('total_worker_cost'))
        last_treatment = max(treatment_records.mapped('treatment_date')) if treatment_records else False
        
        # Budama əməliyyatları
        pruning_records = self.env['farm.pruning'].search([
            ('field_id', '=', field_id),
            ('pruning_date', '>=', date_from),
            ('pruning_date', '<=', date_to)
        ])
        total_general_worker_cost += sum(pruning_records.mapped('total_worker_cost'))
        last_pruning = max(pruning_records.mapped('pruning_date')) if pruning_records else False
        
        # Məhsul yığımı əməliyyatları
        harvest_records = self.env['farm.harvest'].search([
            ('field_id', '=', field_id),
            ('harvest_date', '>=', date_from),
            ('harvest_date', '<=', date_to)
        ])
        total_general_worker_cost += sum(harvest_records.mapped('total_worker_cost'))
        last_harvest = max(harvest_records.mapped('harvest_date')) if harvest_records else False
        
        # Ümumi işçi xərci hesabla
        total_worker_cost = total_skilled_worker_cost + total_general_worker_cost
        
        dashboard_data.update({
            'total_worker_cost': total_worker_cost,
            'total_skilled_worker_cost': total_skilled_worker_cost,
            'total_general_worker_cost': total_general_worker_cost,
            'last_plowing_date': last_plowing,
            'last_planting_date': last_planting,
            'last_treatment_date': last_treatment,
            'last_pruning_date': last_pruning,
            'last_harvest_date': last_harvest,
            'plowing_count': len(plowing_records),
            'planting_count': len(planting_records),
            'treatment_count': len(treatment_records),
            'pruning_count': len(pruning_records),
            'harvest_count': len(harvest_records),
        })
        
        # Material xərcləri (yalnız bu sahə üçün)
        material_expenses = self.env['farm.material.expense'].search([
            ('field_id', '=', field_id),
            ('expense_date', '>=', date_from),
            ('expense_date', '<=', date_to)
        ])
        total_material_cost = sum(material_expenses.mapped('amount'))
        dashboard_data.update({
            'total_material_cost': total_material_cost,
        })
        
        # Traktor xərcləri (yalnız bu sahə üçün)
        tractor_expenses = self.env['farm.tractor.expense'].search([
            ('field_id', '=', field_id),
            ('expense_date', '>=', date_from),
            ('expense_date', '<=', date_to)
        ])
        total_tractor_cost = sum(tractor_expenses.mapped('amount'))
        dashboard_data.update({
            'total_tractor_cost': total_tractor_cost,
        })
        
        # Diesel xərcləri (yalnız bu sahə üçün)
        diesel_expenses = self.env['farm.diesel.expense'].search([
            ('field_id', '=', field_id),
            ('expense_date', '>=', date_from),
            ('expense_date', '<=', date_to)
        ])
        total_diesel_cost = sum(diesel_expenses.mapped('amount'))
        dashboard_data.update({
            'total_diesel_cost': total_diesel_cost,
        })
        
        # Hotel xərcləri (yalnız bu sahə üçün)
        hotel_expenses = self.env['farm.hotel.expense'].search([
            ('field_id', '=', field_id),
            ('expense_date', '>=', date_from),
            ('expense_date', '<=', date_to)
        ])
        total_hotel_cost = sum(hotel_expenses.mapped('amount'))
        dashboard_data.update({
            'total_hotel_cost': total_hotel_cost,
        })
        
        # Kommunal xərcələr (yalnız bu sahə üçün)
        communal_expenses = self.env['farm.communal.expense'].search([
            ('field_id', '=', field_id),
            ('expense_date', '>=', date_from),
            ('expense_date', '<=', date_to)
        ])
        total_communal_cost = sum(communal_expenses.mapped('amount'))
        dashboard_data.update({
            'total_communal_cost': total_communal_cost,
        })
        
        # Ümumi xərclər hesablama
        total_expenses = (total_fertilizer_cost + total_water_cost + total_worker_cost + 
                         total_material_cost + total_tractor_cost + total_diesel_cost + 
                         total_hotel_cost + total_communal_cost)
        
        dashboard_data.update({
            'total_expenses': total_expenses,
        })
        
        # Xəstəlik məlumatları
        diseases = self.env['farm.disease.record'].search([
            ('field_id', '=', field_id),
            ('status', '=', 'active')
        ])
        active_diseases_text = ', '.join(diseases.mapped('disease_name')) if diseases else 'Xəstəlik yoxdur'
        
        dashboard_data.update({
            'disease_count': len(diseases),
            'active_diseases': active_diseases_text,
        })
        
        return dashboard_data

    def action_refresh(self):
        """Dashboard məlumatlarını yenilə"""
        self._calculate_dashboard_data()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'farm.dashboard.wizard',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }
    
    def action_print_report(self):
        """Dashboard hesabatını çıxart"""
        return self.env.ref('farm_agriculture_v2.action_report_farm_dashboard').report_action(self)
    