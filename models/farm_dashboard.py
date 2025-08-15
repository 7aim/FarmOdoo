from odoo import models, fields, api, tools
from datetime import datetime, timedelta


class FarmDashboard(models.Model):
    """Sahə Dashboard - Bağ haqqında bütün məlumatlar"""
    _name = 'farm.dashboard'
    _description = 'Sahə Dashboard'
    _auto = False  # Virtual model - bazada cədvəl yaratmır

    field_id = fields.Many2one('farm.field', string='Sahə', required=True)
    
    # Əsas statistikalar
    total_parcels = fields.Integer('Parsel Sayı')
    total_rows = fields.Integer('Cərgə Sayı')
    total_trees = fields.Integer('Ağac Sayı')
    area_hectare = fields.Float('Sahə Ölçüsü (Hektar)')
    
    # Ağac başına xərclər
    cost_per_tree = fields.Float('Ağac Başına Xərc (AZN)')
    total_expenses = fields.Float('Ümumi Xərclər (AZN)')
    
    # Gübrə məlumatları
    total_fertilizer_cost = fields.Float('Gübrə Xərci (AZN)')
    fertilizer_per_tree = fields.Float('Ağac Başına Gübrə (AZN)')
    last_fertilizing_date = fields.Date('Son Gübrələmə Tarixi')
    
    # Su / Sulama məlumatları
    total_water_cost = fields.Float('Su Xərci (AZN)')
    water_per_tree = fields.Float('Ağac Başına Su (AZN)')
    last_irrigation_date = fields.Date('Son Sulama Tarixi')
    total_irrigation_count = fields.Integer('Sulama Sayı')
    
    # İşçi xərcləri
    total_worker_cost = fields.Float('İşçi Xərci (AZN)')
    worker_cost_per_tree = fields.Float('Ağac Başına İşçi Xərci (AZN)')
    
    # Material xərcləri
    total_material_cost = fields.Float('Material Xərci (AZN)')
    material_cost_per_tree = fields.Float('Ağac Başına Material Xərci (AZN)')
    
    # Traktor xərcləri
    total_tractor_cost = fields.Float('Traktor Xərci (AZN)')
    tractor_cost_per_tree = fields.Float('Ağac Başına Traktor Xərci (AZN)')
    
    # Diesel xərcləri
    total_diesel_cost = fields.Float('Diesel Xərci (AZN)')
    diesel_cost_per_tree = fields.Float('Ağac Başına Diesel Xərci (AZN)')
    
    # Hotel xərcləri
    total_hotel_cost = fields.Float('Hotel Xərci (AZN)')
    hotel_cost_per_tree = fields.Float('Ağac Başına Hotel Xərci (AZN)')
    
    # Kommunal xərclər
    total_communal_cost = fields.Float('Kommunal Xərc (AZN)')
    communal_cost_per_tree = fields.Float('Ağac Başına Kommunal Xərc (AZN)')
    
    # Son əməliyyatlar
    last_plowing_date = fields.Date('Son Şumlama')
    last_treatment_date = fields.Date('Son Müalicə')
    last_pruning_date = fields.Date('Son Budama')
    last_harvest_date = fields.Date('Son Məhsul Yığımı')
    
    # Təhlükəsizlik məlumatları
    disease_count = fields.Integer('Xəstəlik Sayı')
    active_diseases = fields.Text('Aktiv Xəstəliklər')
    
    # Qiymətləndirmə tarixi
    calculation_date = fields.Date('Hesablama Tarixi', default=fields.Date.today)
    year = fields.Integer('İl', default=lambda self: datetime.now().year)
    month = fields.Integer('Ay', default=lambda self: datetime.now().month)

    def init(self):
        """Virtual cədvəl üçün view yaradır"""
        tools.drop_view_if_exists(self.env.cr, self._table)
        
    @api.model
    def get_dashboard_data(self, field_id, year=None, month=None):
        """Müəyyən sahə üçün dashboard məlumatlarını hesablayır"""
        if not year:
            year = datetime.now().year
        if not month:
            month = datetime.now().month
            
        field = self.env['farm.field'].browse(field_id)
        if not field.exists():
            return {}
            
        # Tarix filtri
        date_from = datetime(year, month, 1).date()
        if month == 12:
            date_to = datetime(year + 1, 1, 1).date() - timedelta(days=1)
        else:
            date_to = datetime(year, month + 1, 1).date() - timedelta(days=1)
            
        dashboard_data = {
            'field_id': field.id,
            'field_name': field.name,
            'field_code': field.code,
            'area_hectare': field.area_hectare,
            'total_parcels': field.total_parcel,
            'total_rows': field.total_rows,
            'total_trees': field.total_trees,
            'calculation_date': fields.Date.today(),
            'year': year,
            'month': month,
        }
        
        # Ağac sayı 0 olarsa, hesablama etmə
        trees_count = field.total_trees or 1
        
        # Gübrə xərcləri
        fertilizing_records = self.env['farm.fertilizing'].search([
            ('field_id', '=', field_id),
            ('fertilizing_date', '>=', date_from),
            ('fertilizing_date', '<=', date_to)
        ])
        
        total_fertilizer_cost = sum(fertilizing_records.mapped('total_cost'))
        dashboard_data.update({
            'total_fertilizer_cost': total_fertilizer_cost,
            'fertilizer_per_tree': total_fertilizer_cost / trees_count,
            'last_fertilizing_date': max(fertilizing_records.mapped('fertilizing_date')) if fertilizing_records else False,
        })
        
        # Sulama xərcləri
        irrigation_records = self.env['farm.irrigation'].search([
            ('field_id', '=', field_id),
            ('irrigation_date', '>=', date_from),
            ('irrigation_date', '<=', date_to)
        ])
        
        total_water_cost = sum(irrigation_records.mapped('total_cost'))
        dashboard_data.update({
            'total_water_cost': total_water_cost,
            'water_per_tree': total_water_cost / trees_count,
            'last_irrigation_date': max(irrigation_records.mapped('irrigation_date')) if irrigation_records else False,
            'total_irrigation_count': len(irrigation_records),
        })
        
        # İşçi xərcləri (bütün əməliyyatlardan)
        total_worker_cost = 0
        
        # Şumlama işçi xərcləri
        plowing_records = self.env['farm.plowing'].search([
            ('field_id', '=', field_id),
            ('operation_date', '>=', date_from),
            ('operation_date', '<=', date_to)
        ])
        total_worker_cost += sum(plowing_records.mapped('total_worker_cost'))
        last_plowing = max(plowing_records.mapped('operation_date')) if plowing_records else False
        
        # Gübrələmə işçi xərcləri
        total_worker_cost += sum(fertilizing_records.mapped('total_worker_cost'))
        
        # Sulama işçi xərcləri
        total_worker_cost += sum(irrigation_records.mapped('total_worker_cost'))
        
        # Müalicə işçi xərcləri
        treatment_records = self.env['farm.treatment'].search([
            ('field_id', '=', field_id),
            ('treatment_date', '>=', date_from),
            ('treatment_date', '<=', date_to)
        ])
        total_worker_cost += sum(treatment_records.mapped('total_worker_cost'))
        last_treatment = max(treatment_records.mapped('treatment_date')) if treatment_records else False
        
        # Budama işçi xərcləri
        pruning_records = self.env['farm.pruning'].search([
            ('field_id', '=', field_id),
            ('pruning_date', '>=', date_from),
            ('pruning_date', '<=', date_to)
        ])
        total_worker_cost += sum(pruning_records.mapped('total_worker_cost'))
        last_pruning = max(pruning_records.mapped('pruning_date')) if pruning_records else False
        
        # Məhsul yığımı işçi xərcləri
        harvest_records = self.env['farm.harvest'].search([
            ('field_id', '=', field_id),
            ('harvest_date', '>=', date_from),
            ('harvest_date', '<=', date_to)
        ])
        total_worker_cost += sum(harvest_records.mapped('total_worker_cost'))
        last_harvest = max(harvest_records.mapped('harvest_date')) if harvest_records else False
        
        dashboard_data.update({
            'total_worker_cost': total_worker_cost,
            'worker_cost_per_tree': total_worker_cost / trees_count,
            'last_plowing_date': last_plowing,
            'last_treatment_date': last_treatment,
            'last_pruning_date': last_pruning,
            'last_harvest_date': last_harvest,
        })
        
        # Material xərcləri
        material_expenses = self.env['farm.material.expense'].search([
            ('expense_date', '>=', date_from),
            ('expense_date', '<=', date_to)
        ])
        total_material_cost = sum(material_expenses.mapped('amount'))
        dashboard_data.update({
            'total_material_cost': total_material_cost,
            'material_cost_per_tree': total_material_cost / trees_count,
        })
        
        # Traktor xərcləri
        tractor_expenses = self.env['farm.tractor.expense'].search([
            ('expense_date', '>=', date_from),
            ('expense_date', '<=', date_to)
        ])
        total_tractor_cost = sum(tractor_expenses.mapped('amount'))
        dashboard_data.update({
            'total_tractor_cost': total_tractor_cost,
            'tractor_cost_per_tree': total_tractor_cost / trees_count,
        })
        
        # Diesel xərcləri
        diesel_expenses = self.env['farm.diesel.expense'].search([
            ('expense_date', '>=', date_from),
            ('expense_date', '<=', date_to)
        ])
        total_diesel_cost = sum(diesel_expenses.mapped('amount'))
        dashboard_data.update({
            'total_diesel_cost': total_diesel_cost,
            'diesel_cost_per_tree': total_diesel_cost / trees_count,
        })
        
        # Hotel xərcləri
        hotel_expenses = self.env['farm.hotel.expense'].search([
            ('expense_date', '>=', date_from),
            ('expense_date', '<=', date_to)
        ])
        total_hotel_cost = sum(hotel_expenses.mapped('amount'))
        dashboard_data.update({
            'total_hotel_cost': total_hotel_cost,
            'hotel_cost_per_tree': total_hotel_cost / trees_count,
        })
        
        # Kommunal xərcələr
        communal_expenses = self.env['farm.communal.expense'].search([
            ('expense_date', '>=', date_from),
            ('expense_date', '<=', date_to)
        ])
        total_communal_cost = sum(communal_expenses.mapped('amount'))
        dashboard_data.update({
            'total_communal_cost': total_communal_cost,
            'communal_cost_per_tree': total_communal_cost / trees_count,
        })
        
        # Ümumi xərclər
        total_expenses = (total_fertilizer_cost + total_water_cost + total_worker_cost + 
                         total_material_cost + total_tractor_cost + total_diesel_cost + 
                         total_hotel_cost + total_communal_cost)
        
        dashboard_data.update({
            'total_expenses': total_expenses,
            'cost_per_tree': total_expenses / trees_count,
        })
        
        # Xəstəlik məlumatları
        diseases = self.env['farm.disease'].search([
            ('field_id', '=', field_id),
            ('status', '=', 'active')
        ])
        active_diseases_text = ', '.join(diseases.mapped('disease_name')) if diseases else 'Xəstəlik yoxdur'
        
        dashboard_data.update({
            'disease_count': len(diseases),
            'active_diseases': active_diseases_text,
        })
        
        return dashboard_data

    @api.model
    def get_field_dashboard_action(self, field_id):
        """Sahə üçün dashboard action qaytarır"""
        return {
            'type': 'ir.actions.client',
            'tag': 'farm_dashboard',
            'context': {'field_id': field_id},
            'target': 'current',
        }
    
    def refresh_dashboard(self):
        """Dashboard məlumatlarını yenilə"""
        for record in self:
            dashboard_data = self.get_dashboard_data(record.field_id.id, record.year, record.month)
            record.write(dashboard_data)
        return True
