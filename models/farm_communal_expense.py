from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import datetime


class FarmCommunalExpense(models.Model):
    """Kommunal Xərcləri"""
    _name = 'farm.communal.expense'
    _description = 'Kommunal Xərcləri'
    _order = 'expense_date desc'

    name = fields.Char('Xərc Adı', required=True, default='Kommunal Xərci')
    expense_date = fields.Date('Tarix', required=True, default=fields.Date.today)
    amount = fields.Float('Məbləğ', required=True)
    note = fields.Text('Qeyd')
    
    # Kommunal növləri
    communal_type = fields.Selection([
        ('electricity', 'Elektrik'),
        ('water', 'Su'),
        ('gas', 'Qaz'),
        ('internet', 'İnternet'),
        ('phone', 'Telefon'),
        ('other', 'Digər')
    ], string='Kommunal Növü', default='electricity')

    @api.constrains('amount')
    def _check_balance_limit(self):
        """Xərc etməzdən əvvəl balansı yoxlayır"""
        for record in self:
            if record.amount > 0:
                cash_flow = self.env['farm.cash.flow']
                total_income = cash_flow._get_total_income()
                total_expense = cash_flow._get_total_expense() + record.amount
                
                if total_income < total_expense:
                    raise ValidationError(
                        f"Kifayət qədər balans yoxdur!\n"
                        f"Ümumi gəlir: {total_income} AZN\n"
                        f"Ümumi xərc: {total_expense} AZN"
                    )
    
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
