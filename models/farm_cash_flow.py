# -*- coding: utf-8 -*-

from odoo import models, fields, api

class FarmCashFlow(models.Model):
    _name = 'farm.cash.flow'
    _description = 'Kassa Hərəkatı'
    _order = 'date desc, id desc'

    name = fields.Char('Açıqlama', required=True)
    date = fields.Date('Tarix', default=fields.Date.context_today, required=True)
    transaction_type = fields.Selection([
        ('income', 'Mədaxil'),
        ('expense', 'Məxaric')
    ], string='Növ', required=True)
    amount = fields.Float('Məbləğ', required=True)
    note = fields.Text('Qeyd')
    reference = fields.Char('Əsas')

    @api.model
    def get_balance(self):
        """Cari kassanın balansını hesablayır"""
        income = sum(self.search([('transaction_type', '=', 'income')]).mapped('amount'))
        expense = sum(self.search([('transaction_type', '=', 'expense')]).mapped('amount'))
        return income - expense

class FarmCashBalance(models.TransientModel):
    _name = 'farm.cash.balance'
    _description = 'Kassa Balansı'

    total_income = fields.Float('Ümumi Mədaxil')
    total_expense = fields.Float('Ümumi Məxaric')
    current_balance = fields.Float('Cari Balans')

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        cash_flow = self.env['farm.cash.flow']
        
        income_records = cash_flow.search([('transaction_type', '=', 'income')])
        expense_records = cash_flow.search([('transaction_type', '=', 'expense')])
        
        total_income = sum(income_records.mapped('amount')) if income_records else 0
        total_expense = sum(expense_records.mapped('amount')) if expense_records else 0
        
        res.update({
            'total_income': total_income,
            'total_expense': total_expense + self._get_all_expenses(),
            'current_balance': total_income - total_expense - self._get_all_expenses(),
        })
        return res

    def _get_all_expenses(self):
        """Bütün xərclərin ümumi məbləğini hesablayır"""
        total = 0
        
        # Kommunal
        total += sum(self.env['farm.communal.expense'].search([]).mapped('amount'))
        # Dizel  
        total += sum(self.env['farm.diesel.expense'].search([]).mapped('amount'))
        # Traktor
        total += sum(self.env['farm.tractor.expense'].search([]).mapped('amount'))
        # Material
        total += sum(self.env['farm.material.expense'].search([]).mapped('amount'))
        # Otel
        total += sum(self.env['farm.hotel.expense'].search([]).mapped('amount'))
        # İşçi maaşları
        total += sum(self.env['farm.worker.payment'].search([]).mapped('amount'))
        # Satınalmalar
        purchase_orders = self.env['purchase.order'].search([('state', 'in', ['purchase', 'done'])])
        total += sum(purchase_orders.mapped('amount_total'))
        
        return total
