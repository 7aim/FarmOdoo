# -*- coding: utf-8 -*-

from odoo import models, fields, api, tools
from datetime import datetime

class FarmExpenseReport(models.Model):
    _name = 'farm.expense.report'
    _description = 'Ümumi Xərc Hesabatı'
    _auto = False
    _order = 'date desc'

    name = fields.Char('Açıqlama', readonly=True)
    date = fields.Date('Tarix', readonly=True)
    amount = fields.Float('Məbləğ', readonly=True)
    expense_type = fields.Char('Xərc Növü', readonly=True)
    note = fields.Text('Qeyd', readonly=True)
    year = fields.Char('İl', readonly=True)
    month = fields.Char('Ay', readonly=True)
    quarter = fields.Char('Rüb', readonly=True)
    original_model = fields.Char('Orijinal Model', readonly=True)
    original_id = fields.Integer('Orijinal ID', readonly=True)
    field_id = fields.Many2one('farm.field', string='Sahə', readonly=True)

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW %s AS (
                -- Kommunal Xərclər
                SELECT 
                    row_number() OVER () AS id,
                    name,
                    expense_date AS date,
                    amount,
                    'Kommunal' AS expense_type,
                    COALESCE(note, '') AS note,
                    EXTRACT(year FROM expense_date)::text AS year,
                    EXTRACT(month FROM expense_date)::text AS month,
                    'Q' || EXTRACT(quarter FROM expense_date)::text AS quarter,
                    'farm.communal.expense' AS original_model,
                    id AS original_id,
                    field_id
                FROM farm_communal_expense
                WHERE expense_date IS NOT NULL
                
                UNION ALL
                
                -- Dizel Xərclər
                SELECT 
                    row_number() OVER () + 10000 AS id,
                    name,
                    expense_date AS date,
                    amount,
                    'Dizel' AS expense_type,
                    COALESCE(note, '') AS note,
                    EXTRACT(year FROM expense_date)::text AS year,
                    EXTRACT(month FROM expense_date)::text AS month,
                    'Q' || EXTRACT(quarter FROM expense_date)::text AS quarter,
                    'farm.diesel.expense' AS original_model,
                    id AS original_id,
                    field_id
                FROM farm_diesel_expense
                WHERE expense_date IS NOT NULL
                
                UNION ALL
                
                -- Traktor Xərclər
                SELECT 
                    row_number() OVER () + 20000 AS id,
                    name,
                    expense_date AS date,
                    amount,
                    'Traktor' AS expense_type,
                    COALESCE(note, '') AS note,
                    EXTRACT(year FROM expense_date)::text AS year,
                    EXTRACT(month FROM expense_date)::text AS month,
                    'Q' || EXTRACT(quarter FROM expense_date)::text AS quarter,
                    'farm.tractor.expense' AS original_model,
                    id AS original_id,
                    field_id
                FROM farm_tractor_expense
                WHERE expense_date IS NOT NULL
                
                UNION ALL
                
                -- Mal-Material Xərclər
                SELECT 
                    row_number() OVER () + 30000 AS id,
                    name,
                    expense_date AS date,
                    amount,
                    'Mal-material' AS expense_type,
                    COALESCE(note, '') AS note,
                    EXTRACT(year FROM expense_date)::text AS year,
                    EXTRACT(month FROM expense_date)::text AS month,
                    'Q' || EXTRACT(quarter FROM expense_date)::text AS quarter,
                    'farm.material.expense' AS original_model,
                    id AS original_id,
                    field_id
                FROM farm_material_expense
                WHERE expense_date IS NOT NULL
                
                UNION ALL
                
                -- Otel Xərclər
                SELECT 
                    row_number() OVER () + 40000 AS id,
                    name,
                    expense_date AS date,
                    amount,
                    'Otel' AS expense_type,
                    COALESCE(note, '') AS note,
                    EXTRACT(year FROM expense_date)::text AS year,
                    EXTRACT(month FROM expense_date)::text AS month,
                    'Q' || EXTRACT(quarter FROM expense_date)::text AS quarter,
                    'farm.hotel.expense' AS original_model,
                    id AS original_id,
                    field_id
                FROM farm_hotel_expense
                WHERE expense_date IS NOT NULL
                
                UNION ALL
                
                -- Maaş Ödənişləri (salary, bonus, advance, other)
                SELECT 
                    row_number() OVER () + 50000 AS id,
                    'Maaş Ödənişi - ' || fw.name AS name,
                    fwp.payment_date AS date,
                    fwp.amount,
                    'Maaş' AS expense_type,
                    COALESCE(fwp.description, '') AS note,
                    EXTRACT(year FROM fwp.payment_date)::text AS year,
                    EXTRACT(month FROM fwp.payment_date)::text AS month,
                    'Q' || EXTRACT(quarter FROM fwp.payment_date)::text AS quarter,
                    'farm.worker.payment' AS original_model,
                    fwp.id AS original_id,
                    fw.field_id AS field_id
                FROM farm_worker_payment fwp
                JOIN farm_worker fw ON fwp.worker_id = fw.id
                WHERE fwp.payment_date IS NOT NULL 
                AND fwp.payment_type != 'daily'
                
                UNION ALL
                
                -- Günlük Ödənişlər (daily - fəhlə kateqoriyasında)
                SELECT 
                    row_number() OVER () + 51000 AS id,
                    'Günlük Ödəniş - ' || fw.name AS name,
                    fwp.payment_date AS date,
                    fwp.amount,
                    'Fəhlə' AS expense_type,
                    COALESCE(fwp.description, '') AS note,
                    EXTRACT(year FROM fwp.payment_date)::text AS year,
                    EXTRACT(month FROM fwp.payment_date)::text AS month,
                    'Q' || EXTRACT(quarter FROM fwp.payment_date)::text AS quarter,
                    'farm.worker.payment' AS original_model,
                    fwp.id AS original_id,
                    fw.field_id AS field_id
                FROM farm_worker_payment fwp
                JOIN farm_worker fw ON fwp.worker_id = fw.id
                WHERE fwp.payment_date IS NOT NULL 
                AND fwp.payment_type = 'daily'
                
                UNION ALL
                
                -- Əlavə Fəhlə Xərcləri (farm_additional_expense - yalnız skilled_worker növü)
                SELECT 
                    row_number() OVER () + 60000 AS id,
                    fae.name,
                    fae.expense_date AS date,
                    fae.amount,
                    'Fəhlə' AS expense_type,
                    COALESCE(fae.description, '') AS note,
                    EXTRACT(year FROM fae.expense_date)::text AS year,
                    EXTRACT(month FROM fae.expense_date)::text AS month,
                    'Q' || EXTRACT(quarter FROM fae.expense_date)::text AS quarter,
                    'farm.additional.expense' AS original_model,
                    fae.id AS original_id,
                    CASE 
                        WHEN fae.plowing_id IS NOT NULL THEN fp.field_id
                        WHEN fae.planting_id IS NOT NULL THEN fpl.field_id
                        WHEN fae.irrigation_id IS NOT NULL THEN fi.field_id
                        WHEN fae.fertilizing_id IS NOT NULL THEN ff.field_id
                        WHEN fae.treatment_id IS NOT NULL THEN ft.field_id
                        WHEN fae.pruning_id IS NOT NULL THEN fpr.field_id
                        WHEN fae.harvest_id IS NOT NULL THEN fh.field_id
                        ELSE NULL
                    END AS field_id
                FROM farm_additional_expense fae
                LEFT JOIN farm_plowing fp ON fae.plowing_id = fp.id
                LEFT JOIN farm_planting fpl ON fae.planting_id = fpl.id
                LEFT JOIN farm_irrigation fi ON fae.irrigation_id = fi.id
                LEFT JOIN farm_fertilizing ff ON fae.fertilizing_id = ff.id
                LEFT JOIN farm_treatment ft ON fae.treatment_id = ft.id
                LEFT JOIN farm_pruning fpr ON fae.pruning_id = fpr.id
                LEFT JOIN farm_harvest fh ON fae.harvest_id = fh.id
                WHERE fae.expense_date IS NOT NULL AND fae.expense_type = 'skilled_worker'
                
                UNION ALL
                
                -- Digər Digər Xərclər (farm_additional_expense - skilled_worker xaricində bütün növlər)
                SELECT 
                    row_number() OVER () + 61000 AS id,
                    fae.name,
                    fae.expense_date AS date,
                    fae.amount,
                    'Digər Xərclər' AS expense_type,
                    COALESCE(fae.description, '') AS note,
                    EXTRACT(year FROM fae.expense_date)::text AS year,
                    EXTRACT(month FROM fae.expense_date)::text AS month,
                    'Q' || EXTRACT(quarter FROM fae.expense_date)::text AS quarter,
                    'farm.additional.expense' AS original_model,
                    fae.id AS original_id,
                    CASE 
                        WHEN fae.plowing_id IS NOT NULL THEN fp.field_id
                        WHEN fae.planting_id IS NOT NULL THEN fpl.field_id
                        WHEN fae.irrigation_id IS NOT NULL THEN fi.field_id
                        WHEN fae.fertilizing_id IS NOT NULL THEN ff.field_id
                        WHEN fae.treatment_id IS NOT NULL THEN ft.field_id
                        WHEN fae.pruning_id IS NOT NULL THEN fpr.field_id
                        WHEN fae.harvest_id IS NOT NULL THEN fh.field_id
                        ELSE NULL
                    END AS field_id
                FROM farm_additional_expense fae
                LEFT JOIN farm_plowing fp ON fae.plowing_id = fp.id
                LEFT JOIN farm_planting fpl ON fae.planting_id = fpl.id
                LEFT JOIN farm_irrigation fi ON fae.irrigation_id = fi.id
                LEFT JOIN farm_fertilizing ff ON fae.fertilizing_id = ff.id
                LEFT JOIN farm_treatment ft ON fae.treatment_id = ft.id
                LEFT JOIN farm_pruning fpr ON fae.pruning_id = fpr.id
                LEFT JOIN farm_harvest fh ON fae.harvest_id = fh.id
                WHERE fae.expense_date IS NOT NULL AND fae.expense_type != 'skilled_worker'
                
                UNION ALL
                
                -- Əməliyyatlardakı İşçi Xərcləri (Fəhlə kateqoriyasında)
                SELECT 
                    row_number() OVER () + 65000 AS id,
                    'Şumlama - ' || fw.name AS name,
                    fp.operation_date::date AS date,
                    fpw.amount,
                    'Fəhlə' AS expense_type,
                    COALESCE(fp.notes, '') AS note,
                    EXTRACT(year FROM fp.operation_date)::text AS year,
                    EXTRACT(month FROM fp.operation_date)::text AS month,
                    'Q' || EXTRACT(quarter FROM fp.operation_date)::text AS quarter,
                    'farm.plowing' AS original_model,
                    fp.id AS original_id,
                    fp.field_id
                FROM farm_plowing_worker fpw
                JOIN farm_plowing fp ON fpw.plowing_id = fp.id
                JOIN farm_worker fw ON fpw.worker_id = fw.id
                WHERE fp.operation_date IS NOT NULL
                
                UNION ALL
                
                SELECT 
                    row_number() OVER () + 66000 AS id,
                    'Əkin - ' || fw.name AS name,
                    fpl.planting_date::date AS date,
                    fplw.amount,
                    'Fəhlə' AS expense_type,
                    COALESCE(fpl.notes, '') AS note,
                    EXTRACT(year FROM fpl.planting_date)::text AS year,
                    EXTRACT(month FROM fpl.planting_date)::text AS month,
                    'Q' || EXTRACT(quarter FROM fpl.planting_date)::text AS quarter,
                    'farm.planting' AS original_model,
                    fpl.id AS original_id,
                    fpl.field_id
                FROM farm_planting_worker fplw
                JOIN farm_planting fpl ON fplw.planting_id = fpl.id
                JOIN farm_worker fw ON fplw.worker_id = fw.id
                WHERE fpl.planting_date IS NOT NULL
                
                UNION ALL
                
                SELECT 
                    row_number() OVER () + 67000 AS id,
                    'Sulama - ' || fw.name AS name,
                    fi.irrigation_date::date AS date,
                    fiw.amount,
                    'Fəhlə' AS expense_type,
                    COALESCE(fi.notes, '') AS note,
                    EXTRACT(year FROM fi.irrigation_date)::text AS year,
                    EXTRACT(month FROM fi.irrigation_date)::text AS month,
                    'Q' || EXTRACT(quarter FROM fi.irrigation_date)::text AS quarter,
                    'farm.irrigation' AS original_model,
                    fi.id AS original_id,
                    fi.field_id
                FROM farm_irrigation_worker fiw
                JOIN farm_irrigation fi ON fiw.irrigation_id = fi.id
                JOIN farm_worker fw ON fiw.worker_id = fw.id
                WHERE fi.irrigation_date IS NOT NULL
                
                UNION ALL
                
                SELECT 
                    row_number() OVER () + 68000 AS id,
                    'Gübrələmə - ' || fw.name AS name,
                    ff.fertilizing_date::date AS date,
                    ffw.amount,
                    'Fəhlə' AS expense_type,
                    COALESCE(ff.notes, '') AS note,
                    EXTRACT(year FROM ff.fertilizing_date)::text AS year,
                    EXTRACT(month FROM ff.fertilizing_date)::text AS month,
                    'Q' || EXTRACT(quarter FROM ff.fertilizing_date)::text AS quarter,
                    'farm.fertilizing' AS original_model,
                    ff.id AS original_id,
                    ff.field_id
                FROM farm_fertilizing_worker ffw
                JOIN farm_fertilizing ff ON ffw.fertilizing_id = ff.id
                JOIN farm_worker fw ON ffw.worker_id = fw.id
                WHERE ff.fertilizing_date IS NOT NULL
                
                UNION ALL
                
                SELECT 
                    row_number() OVER () + 69000 AS id,
                    'Dərmanlama - ' || fw.name AS name,
                    ft.treatment_date::date AS date,
                    ftw.amount,
                    'Fəhlə' AS expense_type,
                    COALESCE(ft.notes, '') AS note,
                    EXTRACT(year FROM ft.treatment_date)::text AS year,
                    EXTRACT(month FROM ft.treatment_date)::text AS month,
                    'Q' || EXTRACT(quarter FROM ft.treatment_date)::text AS quarter,
                    'farm.treatment' AS original_model,
                    ft.id AS original_id,
                    ft.field_id
                FROM farm_treatment_worker ftw
                JOIN farm_treatment ft ON ftw.treatment_id = ft.id
                JOIN farm_worker fw ON ftw.worker_id = fw.id
                WHERE ft.treatment_date IS NOT NULL
                
                UNION ALL
                
                SELECT 
                    row_number() OVER () + 69500 AS id,
                    'Budama - ' || fw.name AS name,
                    fpr.pruning_date::date AS date,
                    fprw.amount,
                    'Fəhlə' AS expense_type,
                    COALESCE(fpr.notes, '') AS note,
                    EXTRACT(year FROM fpr.pruning_date)::text AS year,
                    EXTRACT(month FROM fpr.pruning_date)::text AS month,
                    'Q' || EXTRACT(quarter FROM fpr.pruning_date)::text AS quarter,
                    'farm.pruning' AS original_model,
                    fpr.id AS original_id,
                    fpr.field_id
                FROM farm_pruning_worker fprw
                JOIN farm_pruning fpr ON fprw.pruning_id = fpr.id
                JOIN farm_worker fw ON fprw.worker_id = fw.id
                WHERE fpr.pruning_date IS NOT NULL
                
                UNION ALL
                
                SELECT 
                    row_number() OVER () + 69700 AS id,
                    'Yığım - ' || fw.name AS name,
                    fh.harvest_date::date AS date,
                    fhw.amount,
                    'Fəhlə' AS expense_type,
                    COALESCE(fh.notes, '') AS note,
                    EXTRACT(year FROM fh.harvest_date)::text AS year,
                    EXTRACT(month FROM fh.harvest_date)::text AS month,
                    'Q' || EXTRACT(quarter FROM fh.harvest_date)::text AS quarter,
                    'farm.harvest' AS original_model,
                    fh.id AS original_id,
                    fh.field_id
                FROM farm_harvest_worker fhw
                JOIN farm_harvest fh ON fhw.harvest_id = fh.id
                JOIN farm_worker fw ON fhw.worker_id = fw.id
                WHERE fh.harvest_date IS NOT NULL
                
                UNION ALL
                
                SELECT 
                    row_number() OVER () + 69800 AS id,
                    'Soyuducu - ' || fw.name AS name,
                    fcs.storage_date::date AS date,
                    fcsw.amount,
                    'Fəhlə' AS expense_type,
                    COALESCE(fcs.notes, '') AS note,
                    EXTRACT(year FROM fcs.storage_date)::text AS year,
                    EXTRACT(month FROM fcs.storage_date)::text AS month,
                    'Q' || EXTRACT(quarter FROM fcs.storage_date)::text AS quarter,
                    'farm.cold.storage' AS original_model,
                    fcs.id AS original_id,
                    NULL AS field_id
                FROM farm_cold_storage_worker fcsw
                JOIN farm_cold_storage fcs ON fcsw.cold_storage_id = fcs.id
                JOIN farm_worker fw ON fcsw.worker_id = fw.id
                WHERE fcs.storage_date IS NOT NULL
                
                UNION ALL
                
                -- Gübrə Satınalmaları
                SELECT 
                    row_number() OVER () + 70000 AS id,
                    'Gübrə Satınalması - ' || po.name AS name,
                    po.date_order::date AS date,
                    po.amount_total,
                    'Gübrələr' AS expense_type,
                    'Gübrə satın alışı' AS note,
                    EXTRACT(year FROM po.date_order)::text AS year,
                    EXTRACT(month FROM po.date_order)::text AS month,
                    'Q' || EXTRACT(quarter FROM po.date_order)::text AS quarter,
                    'purchase.order' AS original_model,
                    po.id AS original_id,
                    po.farm_field_id AS field_id
                FROM purchase_order po
                JOIN purchase_order_line pol ON po.id = pol.order_id
                JOIN product_product pp ON pol.product_id = pp.id
                JOIN product_template pt ON pp.product_tmpl_id = pt.id
                JOIN product_category pc ON pt.categ_id = pc.id
                WHERE po.state IN ('purchase', 'done') 
                AND po.date_order IS NOT NULL
                AND pc.name = 'Fertilizer'
                
                UNION ALL
                
                -- Dərman Satınalmaları
                SELECT 
                    row_number() OVER () + 71000 AS id,
                    'Dərman Satınalması - ' || po.name AS name,
                    po.date_order::date AS date,
                    po.amount_total,
                    'Dərmanlar' AS expense_type,
                    'Dərman satın alışı' AS note,
                    EXTRACT(year FROM po.date_order)::text AS year,
                    EXTRACT(month FROM po.date_order)::text AS month,
                    'Q' || EXTRACT(quarter FROM po.date_order)::text AS quarter,
                    'purchase.order' AS original_model,
                    po.id AS original_id,
                    po.farm_field_id AS field_id
                FROM purchase_order po
                JOIN purchase_order_line pol ON po.id = pol.order_id
                JOIN product_product pp ON pol.product_id = pp.id
                JOIN product_template pt ON pp.product_tmpl_id = pt.id
                JOIN product_category pc ON pt.categ_id = pc.id
                WHERE po.state IN ('purchase', 'done') 
                AND po.date_order IS NOT NULL
                AND pc.name = 'Pestisid'
                
                UNION ALL
                
                -- Digər Satınalmalar
                SELECT 
                    row_number() OVER () + 72000 AS id,
                    'Digər Satınalma - ' || po.name AS name,
                    po.date_order::date AS date,
                    po.amount_total,
                    'Digər Satınalmalar' AS expense_type,
                    'Digər məhsul satın alışı' AS note,
                    EXTRACT(year FROM po.date_order)::text AS year,
                    EXTRACT(month FROM po.date_order)::text AS month,
                    'Q' || EXTRACT(quarter FROM po.date_order)::text AS quarter,
                    'purchase.order' AS original_model,
                    po.id AS original_id,
                    po.farm_field_id AS field_id
                FROM purchase_order po
                LEFT JOIN purchase_order_line pol ON po.id = pol.order_id
                LEFT JOIN product_product pp ON pol.product_id = pp.id
                LEFT JOIN product_template pt ON pp.product_tmpl_id = pt.id
                LEFT JOIN product_category pc ON pt.categ_id = pc.id
                WHERE po.state IN ('purchase', 'done') 
                AND po.date_order IS NOT NULL
                AND (pc.name IS NULL OR pc.name NOT IN ('Fertilizer', 'Pestisid'))
            )
        """ % self._table)

    @api.model
    def add_total_expense_to_cash(self):
        """Ümumi xərci kassaya əlavə edir"""
        # Bütün xərclərin ümumi məbləğini hesabla
        total_expenses = sum(self.search([]).mapped('amount'))
        
        if total_expenses > 0:
            # Kassaya məxaric əlavə et
            self.env['farm.cash.flow'].create({
                'name': f'Ümumi Xərclər - {fields.Date.today()}',
                'amount': total_expenses,
                'transaction_type': 'expense',
                'date': fields.Date.today(),
                'reference': 'total_expense_report',
                'note': f'Xərc hesabatından ümumi məbləğ: {total_expenses:.2f} AZN'
            })
            
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Uğurlu!',
                'message': f'Ümumi xərc ({total_expenses:.2f} AZN) kassaya əlavə edildi.',
                'sticky': False,
                'type': 'success'
            }
        }

    def open_original_record(self):
        """Orijinal əməliyyatı açır"""
        self.ensure_one()
        if not self.original_model or not self.original_id:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Xəta!',
                    'message': 'Orijinal əməliyyat tapılmadı.',
                    'type': 'danger',
                    'sticky': False,
                }
            }
        
        return {
            'type': 'ir.actions.act_window',
            'res_model': self.original_model,
            'res_id': self.original_id,
            'view_mode': 'form',
            'target': 'new',
            'context': {'form_view_initial_mode': 'edit'},
        }