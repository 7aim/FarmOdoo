from odoo import models, fields, api
from datetime import datetime, timedelta


class FarmDashboardWizard(models.TransientModel):
    """Sahə Dashboard Wizard - Real vaxtda məlumat göstərmək üçün"""
    _name = 'farm.dashboard.wizard'
    _description = 'Sahə Dashboard Wizard'

    field_id = fields.Many2one('farm.field', string='Sahə', required=True)
    year = fields.Integer('İl', default=lambda self: datetime.now().year, required=True)
    month = fields.Selection([
        (1, 'Yanvar'), (2, 'Fevral'), (3, 'Mart'), (4, 'Aprel'),
        (5, 'May'), (6, 'İyun'), (7, 'İyul'), (8, 'Avqust'),
        (9, 'Sentyabr'), (10, 'Oktyabr'), (11, 'Noyabr'), (12, 'Dekabr')
    ], string='Ay', default=lambda self: datetime.now().month, required=True)
    
    # Əsas statistikalar
    total_parcels = fields.Integer('Parsel Sayı', readonly=True)
    total_rows = fields.Integer('Cərgə Sayı', readonly=True)
    total_trees = fields.Integer('Ağac Sayı', readonly=True)
    area_hectare = fields.Float('Sahə Ölçüsü (Hektar)', readonly=True)
    
    # Ağac başına xərclər
    cost_per_tree = fields.Float('Ağac Başına Xərc (AZN)', readonly=True)
    total_expenses = fields.Float('Ümumi Xərclər (AZN)', readonly=True)
    
    # Gübrə məlumatları
    total_fertilizer_cost = fields.Float('Gübrə Xərci (AZN)', readonly=True)
    fertilizer_per_tree = fields.Float('Ağac Başına Gübrə (AZN)', readonly=True)
    last_fertilizing_date = fields.Date('Son Gübrələmə Tarixi', readonly=True)
    
    # Su / Sulama məlumatları
    total_water_cost = fields.Float('Su Xərci (AZN)', readonly=True)
    water_per_tree = fields.Float('Ağac Başına Su (AZN)', readonly=True)
    last_irrigation_date = fields.Date('Son Sulama Tarixi', readonly=True)
    total_irrigation_count = fields.Integer('Sulama Sayı', readonly=True)
    
    # İşçi xərcləri
    total_worker_cost = fields.Float('İşçi Xərci (AZN)', readonly=True)
    worker_cost_per_tree = fields.Float('Ağac Başına İşçi Xərci (AZN)', readonly=True)
    
    # Material xərcləri
    total_material_cost = fields.Float('Material Xərci (AZN)', readonly=True)
    material_cost_per_tree = fields.Float('Ağac Başına Material Xərci (AZN)', readonly=True)
    
    # Traktor xərcləri
    total_tractor_cost = fields.Float('Traktor Xərci (AZN)', readonly=True)
    tractor_cost_per_tree = fields.Float('Ağac Başına Traktor Xərci (AZN)', readonly=True)
    
    # Diesel xərcləri
    total_diesel_cost = fields.Float('Diesel Xərci (AZN)', readonly=True)
    diesel_cost_per_tree = fields.Float('Ağac Başına Diesel Xərci (AZN)', readonly=True)
    
    # Hotel xərcləri
    total_hotel_cost = fields.Float('Hotel Xərci (AZN)', readonly=True)
    hotel_cost_per_tree = fields.Float('Ağac Başına Hotel Xərci (AZN)', readonly=True)
    
    # Kommunal xərclər
    total_communal_cost = fields.Float('Kommunal Xərc (AZN)', readonly=True)
    communal_cost_per_tree = fields.Float('Ağac Başına Kommunal Xərc (AZN)', readonly=True)
    
    # Son əməliyyatlar
    last_plowing_date = fields.Date('Son Şumlama', readonly=True)
    last_treatment_date = fields.Date('Son Müalicə', readonly=True)
    last_pruning_date = fields.Date('Son Budama', readonly=True)
    last_harvest_date = fields.Date('Son Məhsul Yığımı', readonly=True)
    
    # Təhlükəsizlik məlumatları
    disease_count = fields.Integer('Aktiv Xəstəlik Sayı', readonly=True)
    active_diseases = fields.Text('Aktiv Xəstəliklər', readonly=True)
    
    # Qiymətləndirmə tarixi
    calculation_date = fields.Datetime('Hesablama Tarixi', readonly=True, default=fields.Datetime.now)

    @api.onchange('field_id', 'year', 'month')
    def _onchange_field_data(self):
        """Sahə, il və ya ay dəyişəndə məlumatları yenilə"""
        if self.field_id:
            self._calculate_dashboard_data()

    def _calculate_dashboard_data(self):
        """Dashboard məlumatlarını hesabla"""
        if not self.field_id:
            return
            
        # Dashboard servisindən məlumatları al
        dashboard_data = self.env['farm.dashboard'].get_dashboard_data(
            self.field_id.id, self.year, self.month
        )
        
        # Məlumatları wizard-a yaz
        for field_name, value in dashboard_data.items():
            if hasattr(self, field_name):
                setattr(self, field_name, value)

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
