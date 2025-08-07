from odoo import models, fields, api
from datetime import datetime


class FarmTractorExpense(models.Model):
    """Traktor Xərcləri"""
    _name = 'farm.tractor.expense'
    _description = 'Traktor Xərcləri'
    _order = 'expense_date desc'

    name = fields.Char('Xərc Adı', required=True, default='Traktor Xərci')
    expense_date = fields.Date('Tarix', required=True, default=fields.Date.today)
    amount = fields.Float('Məbləğ', required=True)
    note = fields.Text('Qeyd')
    
    # Traktor məlumatları
    tractor_name = fields.Char('Traktor Adı')
    expense_type = fields.Selection([
        ('fuel', 'Yanacaq'),
        ('repair', 'Təmir'),
        ('maintenance', 'Texniki Baxım'),
        ('parts', 'Ehtiyat Hissələri'),
        ('service', 'Xidmət'),
        ('other', 'Digər')
    ], string='Xərc Növü', default='fuel')
    
    # Hesabat üçün
    year = fields.Integer('İl', compute='_compute_date_fields', store=True)
    month = fields.Integer('Ay', compute='_compute_date_fields', store=True)
    quarter = fields.Integer('Rüb', compute='_compute_date_fields', store=True)
    
    @api.depends('expense_date')
    def _compute_date_fields(self):
        for record in self:
            if record.expense_date:
                date = fields.Date.from_string(record.expense_date)
                record.year = date.year
                record.month = date.month
                record.quarter = (date.month - 1) // 3 + 1
            else:
                record.year = 0
                record.month = 0
                record.quarter = 0
