from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import datetime


class FarmDieselExpense(models.Model):
    """Dizel Xərcləri"""
    _name = 'farm.diesel.expense'
    _description = 'Dizel Xərcləri'
    _order = 'expense_date desc'

    name = fields.Char('Xərc Adı', required=True, default='Dizel Xərci')
    expense_date = fields.Date('Tarix', required=True, default=fields.Date.today)
    field_id = fields.Many2one('farm.field', string='Sahə', required=True, ondelete='cascade')
    amount = fields.Float('Məbləğ', required=True)
    note = fields.Text('Qeyd')
    
    # Dizel məlumatları
    liters = fields.Float('Litr Miqdarı')
    price_per_liter = fields.Float('Litr Qiyməti')
    fuel_station = fields.Char('Yanacaq Stansiyası')

    @api.constrains('amount')
    def _check_balance_limit(self):
        """Xərc etməzdən əvvəl balansı yoxlayır"""
        for record in self:
            if record.amount > 0:
                cash_flow = self.env['farm.cash.flow']
                cash_flow.check_expense_balance(record.amount, 'farm.diesel.expense', record.id)
    
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
                
    @api.onchange('liters', 'price_per_liter')
    def _onchange_fuel_calculation(self):
        if self.liters and self.price_per_liter:
            self.amount = self.liters * self.price_per_liter
