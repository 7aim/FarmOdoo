# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta

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
    expense_records = fields.One2many('farm.founder.expense', 'founder_id', string='Ödəmə Qeydləri')
    
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
    _description = 'Təsisçi Ödəmələri'
    _order = 'date desc'

    name = fields.Char('Açıqlama', required=True)
    founder_id = fields.Many2one('farm.founder', string='Təsisçi', required=True)
    amount = fields.Float('Məbləğ', required=True)
    date = fields.Date('Tarix', default=fields.Date.context_today, required=True)
    expense_type = fields.Selection([
        ('treatment', 'Dərmanlama'),
        ('fertilizing', 'Gübrələmə'),
        ('water', 'Su'),
        ('electricity', 'Elektrik'),
        ('gas', 'Qaz'),
        ('fuel', 'Yanacaq'),
        ('materials', 'Mal material'),
        ('fixed_assets', 'Əsas vəsaitlər'),
        ('low_value_items', 'Azqiymətlilər'),
        ('founder_payments', 'Təsisçi ödəmələri'),
        ('other', 'Digər')
    ], string='Xərc Növü', default='founder_payments', required=True)
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

    # Tarix filtr sahələri
    date_filter = fields.Selection([
        ('all', 'Bütün Tarixlər'),
        ('year', 'İl üzrə'),
        ('month', 'Ay üzrə'),
        ('custom', 'Özel Tarix')
    ], string='📅 Tarix Filtri', default='all', required=True)
    
    year = fields.Integer('İl', default=lambda self: fields.Date.today().year)
    month = fields.Selection([
        ('1', 'Yanvar'), ('2', 'Fevral'), ('3', 'Mart'), ('4', 'Aprel'),
        ('5', 'May'), ('6', 'İyun'), ('7', 'İyul'), ('8', 'Avqust'),
        ('9', 'Sentyabr'), ('10', 'Oktyabr'), ('11', 'Noyabr'), ('12', 'Dekabr')
    ], string='Ay', default=lambda self: str(fields.Date.today().month))
    
    date_from = fields.Date('📅 Başlanğıc Tarix')
    date_to = fields.Date('📅 Bitmə Tarix')

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
        # İlkin yükləmədə filtrsiz hesabla
        self._calculate_balance_data(res)
        return res

    def _get_date_domain(self):
        """Tarix filtrinə əsasən domain qaytarır"""
        if self.date_filter == 'all':
            return []
        elif self.date_filter == 'custom' and self.date_from and self.date_to:
            return [('date', '>=', self.date_from), ('date', '<=', self.date_to)]
        elif self.date_filter == 'year' and self.year:
            date_from = fields.Date.from_string(f'{self.year}-01-01')
            date_to = fields.Date.from_string(f'{self.year}-12-31')
            return [('date', '>=', date_from), ('date', '<=', date_to)]
        elif self.date_filter == 'month' and self.year and self.month:
            month_int = int(self.month)
            date_from = fields.Date.from_string(f'{self.year}-{month_int:02d}-01')
            # Ayın son günü
            if month_int == 12:
                date_to = fields.Date.from_string(f'{self.year + 1}-01-01') - timedelta(days=1)
            else:
                date_to = fields.Date.from_string(f'{self.year}-{month_int + 1:02d}-01') - timedelta(days=1)
            return [('date', '>=', date_from), ('date', '<=', date_to)]
        return []

    def _calculate_balance_data(self, res=None):
        """Balans məlumatlarını tarix filtrinə əsasən hesablayır"""
        if res is None:
            res = {}
            
        cash_flow_obj = self.env['farm.cash.flow']
        date_domain = self._get_date_domain()
        
        # Gəlir məlumatları (tarix filtri ilə)
        income_data = self._get_filtered_income_summary(date_domain)
        
        # Xərc məlumatları (tarix filtri ilə)  
        total_expense = self._get_filtered_total_expense(date_domain)
        founder_expenses = self._get_filtered_founder_expenses(date_domain)
        
        # Yalnız kassa məxarici (cash flow-dakı expense)
        cash_expense_domain = [('transaction_type', '=', 'expense')] + date_domain
        cash_expense_only = sum(cash_flow_obj.search(cash_expense_domain).mapped('amount'))
        
        # Xərc hesabatındakı xərclər (bağ xərcləri) - tarix filtri ilə
        expense_report_expenses = self._get_filtered_expense_report_total(date_domain)
        
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

    def _get_filtered_income_summary(self, date_domain):
        """Tarix filtrinə əsasən gəlir xülasəsi"""
        cash_flow_obj = self.env['farm.cash.flow']
        
        # Subsidiya gəlirləri
        subsidies_domain = [('transaction_type', '=', 'subsidy')] + date_domain
        subsidy_income = sum(cash_flow_obj.search(subsidies_domain).mapped('amount'))
        
        # Borc gəlirləri  
        debt_domain = [('transaction_type', '=', 'debt')] + date_domain
        debt_income = sum(cash_flow_obj.search(debt_domain).mapped('amount'))
        
        # Digər gəlirlər
        income_domain = [('transaction_type', '=', 'income')] + date_domain
        other_income = sum(cash_flow_obj.search(income_domain).mapped('amount'))
        
        # Təsisçi investisiyaları (tarix filtri ilə)
        founder_investments = self._get_filtered_founder_investments(date_domain)
        
        # Traktor gəlirləri (tarix filtri ilə)
        tractor_income = self._get_filtered_tractor_income(date_domain)
        
        total_income = subsidy_income + debt_income + other_income + founder_investments + tractor_income
        
        return {
            'subsidy_income': subsidy_income,
            'debt_income': debt_income,
            'other_income': other_income,
            'founder_investments': founder_investments,
            'tractor_income': tractor_income,
            'total_income': total_income,
        }

    def _get_filtered_founder_investments(self, date_domain):
        """Tarix filtrinə əsasən təsisçi investisiyalarını hesablayır"""
        try:
            domain = date_domain.copy()
            # date sahəsini uyğun sahə ilə əvəz et
            filtered_domain = []
            for condition in domain:
                if condition[0] == 'date':
                    filtered_domain.append(('date', condition[1], condition[2]))
                else:
                    filtered_domain.append(condition)
            
            investments = self.env['farm.founder.investment'].search(filtered_domain)
            return sum(investments.mapped('amount'))
        except Exception:
            return 0

    def _get_filtered_tractor_income(self, date_domain):
        """Tarix filtrinə əsasən traktor gəlirlərini hesablayır"""
        try:
            domain = date_domain.copy()
            # date sahəsini income_date ilə əvəz et
            filtered_domain = []
            for condition in domain:
                if condition[0] == 'date':
                    filtered_domain.append(('income_date', condition[1], condition[2]))
                else:
                    filtered_domain.append(condition)
            
            tractor_incomes = self.env['farm.tractor.income'].search(filtered_domain)
            return sum(tractor_incomes.mapped('amount'))
        except Exception:
            return 0

    def _get_filtered_total_expense(self, date_domain):
        """Tarix filtrinə əsasən ümumi xərci hesablayır"""
        cash_flow_obj = self.env['farm.cash.flow']
        
        # Cash flow xərcləri
        expense_domain = [('transaction_type', '=', 'expense')] + date_domain
        cash_expenses = sum(cash_flow_obj.search(expense_domain).mapped('amount'))
        
        # Digər xərc növləri (expense_date sahəsi olan)
        expense_models = [
            'farm.diesel.expense',
            'farm.tractor.expense', 
            'farm.hotel.expense',
            'farm.material.expense',
            'farm.communal.expense'
        ]
        
        other_expenses = 0
        for model_name in expense_models:
            try:
                if model_name in self.env:
                    domain = self._convert_date_domain_for_model(date_domain, 'expense_date')
                    expenses = self.env[model_name].search(domain)
                    other_expenses += sum(expenses.mapped('amount'))
            except Exception:
                # Model mövcud deyilsə burax
                pass
        
        # Bağ xərcləri (farm.expense.report)
        try:
            expense_reports = self._get_filtered_expense_report_total(date_domain)
        except Exception:
            expense_reports = 0
        
        return cash_expenses + other_expenses + expense_reports

    def _get_filtered_founder_expenses(self, date_domain):
        """Tarix filtrinə əsasən təsisçi xərclərini hesablayır"""
        try:
            domain = self._convert_date_domain_for_model(date_domain, 'date')
            founder_expenses = self.env['farm.founder.expense'].search(domain)
            return sum(founder_expenses.mapped('amount'))
        except Exception:
            return 0

    def _get_filtered_expense_report_total(self, date_domain):
        """Tarix filtrinə əsasən xərc hesabatı xərclərini hesablayır"""
        try:
            domain = self._convert_date_domain_for_model(date_domain, 'date')
            expense_reports = self.env['farm.expense.report'].search(domain)
            return sum(expense_reports.mapped('amount'))
        except Exception:
            return 0

    def _convert_date_domain_for_model(self, date_domain, date_field):
        """Date domain-ini müxtəlif modellər üçün uyğun sahə adı ilə çevirir"""
        converted_domain = []
        for condition in date_domain:
            if condition[0] == 'date':
                converted_domain.append((date_field, condition[1], condition[2]))
            else:
                converted_domain.append(condition)
        return converted_domain

    def action_refresh(self):
        """Balansı yenilə düyməsi"""
        values = {}
        self._calculate_balance_data(values)
        self.write(values)
        # Sadəcə True qaytarmaq formu yenilənməyə məcbur edir
        return True

    @api.onchange('date_filter', 'year', 'month', 'date_from', 'date_to')
    def _onchange_date_filter(self):
        """Tarix filtri dəyişəndə balansı yenilə"""
        values = {}
        self._calculate_balance_data(values)
        for field, value in values.items():
            setattr(self, field, value)

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
