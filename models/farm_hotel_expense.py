from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import datetime


class FarmHotelExpense(models.Model):
    """Otel Xərcləri"""
    _name = 'farm.hotel.expense'
    _description = 'Otel Xərcləri'
    _order = 'expense_date desc'

    name = fields.Char('Xərc Adı', required=True, default='Otel Xərci')
    expense_date = fields.Date('Tarix', required=True, default=fields.Date.today)
    amount = fields.Float('Məbləğ', required=True)
    note = fields.Text('Qeyd')
    
    # Otel məlumatları
    hotel_name = fields.Char('Otel Adı')
    
    # Hesabat üçün
    year = fields.Integer('İl', compute='_compute_date_fields', store=True)
    month = fields.Integer('Ay', compute='_compute_date_fields', store=True)
    quarter = fields.Integer('Rüb', compute='_compute_date_fields', store=True)

    @api.constrains('amount')
    def _check_balance_limit(self):
        """Xərc etməzdən əvvəl balansı yoxlayır"""
        for record in self:
            if record.amount > 0:
                cash_flow = self.env['farm.cash.flow']
                cash_flow.check_expense_balance(record.amount, 'farm.hotel.expense', record.id)
    
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
                
    @api.onchange('nights', 'price_per_night', 'guest_count')
    def _onchange_hotel_calculation(self):
        if self.nights and self.price_per_night:
            self.amount = self.nights * self.price_per_night * (self.guest_count or 1)
