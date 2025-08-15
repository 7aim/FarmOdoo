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
        """Təsisçi xərci üçün ümumi kassa balansından yoxlayır"""
        for record in self:
            if record.amount > 0:
                cash_flow = self.env['farm.cash.flow']
                cash_flow.check_expense_balance(record.amount, 'farm.founder.expense', record.id)

class FarmCashFlow(models.Model):
    _name = 'farm.cash.flow'
    _description = 'Kassa Hərəkatı'
    _order = 'date desc, id desc'

    name = fields.Char('Açıqlama', required=True)
    date = fields.Date('Tarix', default=fields.Date.context_today, required=True)
    transaction_type = fields.Selection([
        ('income', 'Mədaxil'),
        ('expense', 'Məxaric'),
        ('subsidy', 'Subsidiya'),
        ('debt', 'Borc')
    ], string='Növ', required=True)
    
    amount = fields.Float('Məbləğ', required=True)
    note = fields.Text('Qeyd')
    reference = fields.Char('Əsas')

    @api.constrains('amount', 'transaction_type')
    def _check_balance_limit_expense(self):
        """Məxaric üçün balans yoxlanışı"""
        for record in self:
            if record.transaction_type == 'expense' and record.amount > 0:
                # Cari balansı hesabla (bu qeydsiz)
                current_balance = self._get_current_balance()
                
                if record.amount > current_balance:
                    raise ValidationError(
                        f"Kifayət qədər balans yoxdur!\n"
                        f"Cari balans: {current_balance:.2f} AZN\n"
                        f"Çıxarılmaq istənən: {record.amount:.2f} AZN\n"
                        f"Çatışmayan məbləğ: {record.amount - current_balance:.2f} AZN"
                    )

    def _get_current_balance(self):
        """Cari balansı hesabla (bu qeydi çıxaraq)"""
        total_income = self._get_total_income()
        total_expense = self._get_total_expense_excluding_current()
        return total_income - total_expense
    
    def _get_total_expense_excluding_current(self):
        """Ümumi xərc hesabla (cari qeydi istisna etməklə)"""
        # Bu qeydi istisna etmək üçün ID-ni götürürük
        exclude_id = self.id if self.id else 0
        
        # Kassa xərcləri (cari qeydsiz)
        cash_expense = sum(self.env['farm.cash.flow'].search([
            ('transaction_type', '=', 'expense'),
            ('id', '!=', exclude_id)
        ]).mapped('amount'))
        
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

    def _get_total_income(self):
        """Ümumi gəlir hesabla"""
        # Kassa gəlirləri (mədaxil, subsidiya, borc)
        income_records = self.env['farm.cash.flow'].search([('transaction_type', 'in', ['income', 'subsidy', 'debt'])])
        cash_income = sum(income_records.mapped('amount'))
        
        # Təsisçi investisiyaları
        founder_investments = sum(self.env['farm.founder.investment'].search([]).mapped('amount'))
        
        # Traktor gəlirləri
        tractor_income = sum(self.env['farm.tractor.income'].search([]).mapped('amount'))
        
        return cash_income + founder_investments + tractor_income
    
    def _get_total_expense(self):
        """Ümumi xərc hesabla"""
        # Kassa xərcləri
        cash_expense = sum(self.env['farm.cash.flow'].search([('transaction_type', '=', 'expense')]).mapped('amount'))
        
        # Digər xərc modellərindən (artıq farm.expense.report-da daxildir, təkrarlamaq olmaz)
        total = cash_expense
        
        # Bağ xərcləri (farm.expense.report-dakı bütün xərclər)
        bag_expenses = sum(self.env['farm.expense.report'].search([]).mapped('amount'))
        total += bag_expenses
        
        # Təsisçi xərcləri
        total += sum(self.env['farm.founder.expense'].search([]).mapped('amount'))
        
        return total

    @api.model
    def check_expense_balance(self, amount, expense_model=None, record_id=None):
        """Universal balans yoxlaması bütün xərc növləri üçün"""
        if amount <= 0:
            return True
            
        # Cari balansı hesabla
        total_income = self._get_total_income()
        total_expense = self._get_total_expense()
        
        # Əgər qeyd yenilənir və köhnə məbləği varsa çıxar
        if expense_model and record_id:
            try:
                old_record = self.env[expense_model].browse(record_id)
                if old_record.exists():
                    total_expense -= old_record.amount
            except:
                pass
        
        current_balance = total_income - total_expense
        
        if amount > current_balance:
            raise ValidationError(
                f"Kifayət qədər balans yoxdur!\n"
                f"Cari balans: {current_balance:.2f} AZN\n"
                f"Xərc məbləği: {amount:.2f} AZN\n"
                f"Çatışmayan: {amount - current_balance:.2f} AZN"
            )
        
        return True

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
            'tractor_income': 0,
            'total_income': 0
        }
        
        # Subsidiya qeydləri
        subsidy_records = self.search([('transaction_type', '=', 'subsidy')])
        result['subsidy_income'] = sum(subsidy_records.mapped('amount'))
        
        # Borc qeydləri
        debt_records = self.search([('transaction_type', '=', 'debt')])
        result['debt_income'] = sum(debt_records.mapped('amount'))
        
        # Digər gəlir qeydləri
        other_records = self.search([('transaction_type', '=', 'income')])
        result['other_income'] = sum(other_records.mapped('amount'))
        
        # Təsisçi investisiyaları
        result['founder_investments'] = sum(self.env['farm.founder.investment'].search([]).mapped('amount'))
        
        # Traktor gəlirləri
        result['tractor_income'] = sum(self.env['farm.tractor.income'].search([]).mapped('amount'))
        
        result['total_income'] = (result['subsidy_income'] + result['debt_income'] + result['other_income'] + 
                                result['founder_investments'] + result['tractor_income'])
        
        return result

class FarmCashBalance(models.TransientModel):
    _name = 'farm.cash.balance'
    _description = 'Kassa Balansı'

    # Gəlir növləri
    subsidy_income = fields.Float('Subsidiya Gəlirləri')
    debt_income = fields.Float('Borc Gəlirləri')
    other_income = fields.Float('Digər Gəlir')
    founder_investments_total = fields.Float('Təsisçi İnvestisiyaları')
    tractor_income_total = fields.Float('Traktor Gəlirləri')
    total_income = fields.Float('Ümumi Mədaxil')
    
    # Xərc məlumatları
    cash_expense_only = fields.Float('Kassa Məxarici')
    founder_expenses_total = fields.Float('Təsisçi Xərcləri')
    expense_report_total = fields.Float('Xərc Hesabatındakı Xərcləri')
    all_expenses_total = fields.Float('Bütün Xərclər')
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
        founder_expenses = sum(cash_flow_obj.env['farm.founder.expense'].search([]).mapped('amount'))
        
        # Yalnız kassa məxarici (cash flow-dakı expense)
        cash_expense_only = sum(cash_flow_obj.env['farm.cash.flow'].search([('transaction_type', '=', 'expense')]).mapped('amount'))
        
        # Xərc hesabatındakı xərclər (bağ xərcləri)
        expense_report_expenses = sum(self.env['farm.expense.report'].search([]).mapped('amount'))
        
        # Bütün xərclər
        all_expenses = total_expense
        
        res.update({
            'subsidy_income': income_data['subsidy_income'],
            'debt_income': income_data['debt_income'],
            'other_income': income_data['other_income'],
            'founder_investments_total': income_data['founder_investments'],
            'tractor_income_total': income_data['tractor_income'],
            'cash_expense_only': cash_expense_only,
            'founder_expenses_total': founder_expenses,
            'expense_report_total': expense_report_expenses,
            'all_expenses_total': all_expenses,
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
