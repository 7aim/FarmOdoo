# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError

class FarmFounder(models.Model):
    _name = 'farm.founder'
    _description = 'Təsisçi'
    _order = 'name'

    name = fields.Char('Təsisçi Adı', required=True)
    active = fields.Boolean('Aktiv', default=True)
    debt_limit = fields.Float('Borc Limiti', default=0.0)
    current_investment = fields.Float('Cari İnvestisiya', compute='_compute_current_amounts', store=True)
    
    # One2many əlaqələr
    investment_records = fields.One2many('farm.founder.investment', 'founder_id', string='İnvestisiya Qeydləri')
    expense_records = fields.One2many('farm.founder.expense', 'founder_id', string='Xərc Qeydləri')
    
    # Hesablanmış sahələr
    current_expense = fields.Float('Cari Xərc', compute='_compute_current_amounts', store=True)
    available_balance = fields.Float('Mövcud Balans', compute='_compute_current_amounts', store=True)
    
    @api.depends()
    def _compute_current_amounts(self):
        for founder in self:
            # İnvestisiya məbləğləri  
            founder.current_investment = sum(founder.investment_records.mapped('amount'))
            # Xərc məbləğləri
            founder.current_expense = sum(founder.expense_records.mapped('amount'))
            # Mövcud balans
            founder.available_balance = founder.current_investment - founder.current_expense

# Temporary model for database cleanup
class FarmFounderDebt(models.Model):
    _name = 'farm.founder.debt'
    _description = 'Temporary model for cleanup'
    
    name = fields.Char('Name')
    founder_id = fields.Many2one('farm.founder', 'Founder')
    amount = fields.Float('Amount')
    date = fields.Date('Date')
    note = fields.Text('Note')
    reference = fields.Char('Reference')

class FarmFounderInvestment(models.Model):
    _name = 'farm.founder.investment'
    _description = 'Təsisçi İnvestisiya Qeydləri'
    _order = 'date desc'

    name = fields.Char('Açıqlama', required=True)
    founder_id = fields.Many2one('farm.founder', string='Təsisçi', required=True)
    amount = fields.Float('Məbləğ', required=True)
    date = fields.Date('Tarix', default=fields.Date.context_today, required=True)
    note = fields.Text('Qeyd')
    reference = fields.Char('Əsas')

class FarmFounderExpense(models.Model):
    _name = 'farm.founder.expense'
    _description = 'Təsisçi Xərcləri'
    _order = 'date desc'

    name = fields.Char('Açıqlama', required=True)
    founder_id = fields.Many2one('farm.founder', string='Təsisçi', required=True)
    amount = fields.Float('Məbləğ', required=True)
    date = fields.Date('Tarix', default=fields.Date.context_today, required=True)
    expense_type = fields.Selection([
        ('personal', 'Şəxsi Xərc'),
        ('business', 'İş Xərci'),
        ('farm_material', 'Təsərrüfat Materialı'),
        ('equipment', 'Avadanlıq'),
        ('other', 'Digər')
    ], string='Xərc Növü', default='personal')
    note = fields.Text('Qeyd')
    reference = fields.Char('Əsas')
    
    @api.constrains('amount', 'founder_id')
    def _check_founder_balance(self):
        """Təsisçinin xərc edə biləcəyini yoxlayır"""
        for record in self:
            if record.amount > 0 and record.founder_id:
                # Təsisçinin ümumi gəliri (yalnız investisiya)
                founder_income = record.founder_id.current_investment
                
                # Təsisçinin ümumi xərci (mövcud + yeni)
                founder_expenses = sum(record.founder_id.expense_records.mapped('amount')) + record.amount
                
                if founder_expenses > founder_income:
                    raise ValidationError(
                        f"{record.founder_id.name} üçün kifayət qədər vəsait yoxdur!\n"
                        f"Ümumi gəlir: {founder_income} AZN\n"
                        f"Ümumi xərc: {founder_expenses} AZN\n"
                        f"Əlavə edilə bilən maksimum: {founder_income - (founder_expenses - record.amount)} AZN"
                    )

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
    
    # Sadələşdirilmiş gəlir növləri - subsidiya və borc ümumi
    income_type = fields.Selection([
        ('subsidy', 'Subsidiya (Ümumi)'),
        ('debt', 'Borc (Ümumi)'),
        ('other', 'Digər Gəlir')
    ], string='Gəlir Növü')
    
    amount = fields.Float('Məbləğ', required=True)
    note = fields.Text('Qeyd')
    reference = fields.Char('Əsas')

    @api.constrains('amount')
    def _check_balance_limit_expense(self):
        """Yalnız məxaric üçün balans yoxlanışı"""
        for record in self:
            if record.transaction_type == 'expense' and record.amount > 0:
                # Ümumi gəlir hesabla
                total_income = self._get_total_income()
                total_expense = self._get_total_expense() + record.amount
                
                if total_income < total_expense:
                    raise ValidationError(
                        f"Kifayət qədər balans yoxdur!\n"
                        f"Ümumi gəlir: {total_income} AZN\n"
                        f"Ümumi xərc: {total_expense} AZN"
                    )

    def _get_total_income(self):
        """Ümumi gəlir hesabla"""
        # Kassa gəlirləri (subsidiya, borc, digər)
        cash_income = sum(self.env['farm.cash.flow'].search([('transaction_type', '=', 'income')]).mapped('amount'))
        
        # Təsisçi investisiyaları
        founder_investments = sum(self.env['farm.founder.investment'].search([]).mapped('amount'))
        
        return cash_income + founder_investments
    
    def _get_total_expense(self):
        """Ümumi xərc hesabla"""
        # Kassa xərcləri
        cash_expense = sum(self.env['farm.cash.flow'].search([('transaction_type', '=', 'expense')]).mapped('amount'))
        
        # Digər xərc modellərindən
        total = cash_expense
        total += sum(self.env['farm.communal.expense'].search([]).mapped('amount'))
        total += sum(self.env['farm.diesel.expense'].search([]).mapped('amount'))
        total += sum(self.env['farm.tractor.expense'].search([]).mapped('amount'))
        total += sum(self.env['farm.material.expense'].search([]).mapped('amount'))
        total += sum(self.env['farm.hotel.expense'].search([]).mapped('amount'))
        
        # Təsisçi xərcləri
        total += sum(self.env['farm.founder.expense'].search([]).mapped('amount'))
        
        return total

    @api.onchange('transaction_type')
    def _onchange_transaction_type(self):
        """Gəlir növünü sıfırla"""
        if self.transaction_type != 'income':
            self.income_type = False

    @api.model
    def get_balance(self):
        """Cari kassanın balansını hesablayır"""
        return self._get_total_income() - self._get_total_expense()

    @api.model
    def get_income_summary(self):
        """Gəlir xülasəsi"""
        result = {
            'subsidy_income': 0,
            'debt_income': 0,
            'other_income': 0,
            'founder_investments': 0,
            'total_income': 0
        }
        
        # Kassa gəlirləri
        cash_records = self.search([('transaction_type', '=', 'income')])
        for record in cash_records:
            if record.income_type == 'subsidy':
                result['subsidy_income'] += record.amount
            elif record.income_type == 'debt':
                result['debt_income'] += record.amount
            else:
                result['other_income'] += record.amount
        
        # Təsisçi investisiyaları
        result['founder_investments'] = sum(self.env['farm.founder.investment'].search([]).mapped('amount'))
        
        result['total_income'] = (result['subsidy_income'] + result['debt_income'] + result['other_income'] + 
                                result['founder_investments'])
        
        return result

class FarmCashBalance(models.TransientModel):
    _name = 'farm.cash.balance'
    _description = 'Kassa Balansı'

    # Gəlir növləri
    subsidy_income = fields.Float('Subsidiya Gəlirləri')
    debt_income = fields.Float('Borc Gəlirləri')
    other_income = fields.Float('Digər Gəlir')
    founder_investments_total = fields.Float('Təsisçi İnvestisiyaları')
    total_income = fields.Float('Ümumi Mədaxil')
    
    # Xərc məlumatları
    total_expense = fields.Float('Ümumi Məxaric')
    current_balance = fields.Float('Cari Balans')

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        cash_flow_obj = self.env['farm.cash.flow']
        
        # Gəlir məlumatları
        income_data = cash_flow_obj.get_income_summary()
        
        # Xərc məlumatları
        dummy_record = cash_flow_obj.browse()
        total_expense = dummy_record._get_total_expense()
        
        res.update({
            'subsidy_income': income_data['subsidy_income'],
            'debt_income': income_data['debt_income'],
            'other_income': income_data['other_income'],
            'founder_investments_total': income_data['founder_investments'],
            'total_income': income_data['total_income'],
            'total_expense': total_expense,
            'current_balance': income_data['total_income'] - total_expense,
        })
        return res

    def check_expense_limit(self, expense_amount):
        """Xərc limitini yoxlayır"""
        current_balance = self.current_balance
        if current_balance < expense_amount:
            raise ValidationError(
                f"Xərc məbləği ({expense_amount}) mövcud balansdan ({current_balance}) çoxdur!"
            )

    @api.model
    def can_afford_expense(self, amount):
        """Xərc edə bilmə qabiliyyətini yoxlayır"""
        balance_obj = self.create({})
        return balance_obj.current_balance >= amount
