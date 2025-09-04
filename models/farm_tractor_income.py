from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import datetime


class FarmTractorIncome(models.Model):
    """Traktor Gəliri"""
    _name = 'farm.tractor.income'
    _description = 'Traktor Gəliri'
    _order = 'income_date desc'

    name = fields.Char('Gəlir Adı', required=True, default='Traktor Gəliri')
    income_date = fields.Date('Tarix', required=True, default=fields.Date.today)
    amount = fields.Float('Məbləğ', required=True)
    note = fields.Text('Qeyd')
    
    # Traktor məlumatları
    tractor_name = fields.Many2one('farm.tech', string='Texnika')
    income_type = fields.Selection([
        ('rental', 'Kirayə Gəliri'),
        ('service', 'Xidmət Gəliri'),
        ('transport', 'Daşıma Gəliri'),
        ('agricultural_work', 'Kənd Təsərrüfatı İşləri'),
        ('other', 'Digər')
    ], string='Gəlir Növü', default='rental')
    
    # Müştəri məlumatları
    customer_name = fields.Char('Müştəri Adı')
    customer_phone = fields.Char('Müştəri Telefonu')
    
    # Hesabat üçün
    year = fields.Integer('İl', compute='_compute_date_fields', store=True)
    month = fields.Integer('Ay', compute='_compute_date_fields', store=True)
    quarter = fields.Integer('Rüb', compute='_compute_date_fields', store=True)
    
    @api.depends('income_date')
    def _compute_date_fields(self):
        for record in self:
            if record.income_date:
                date = fields.Date.from_string(record.income_date)
                record.year = date.year
                record.month = date.month
                record.quarter = (date.month - 1) // 3 + 1
            else:
                record.year = 0
                record.month = 0
                record.quarter = 0
    
    @api.constrains('amount')
    def _check_amount(self):
        """Məbləğin müsbət olduğunu yoxlayır"""
        for record in self:
            if record.amount <= 0:
                raise ValidationError("Gəlir məbləği müsbət olmalıdır!")
