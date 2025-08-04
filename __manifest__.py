# -*- coding: utf-8 -*-

{
    'name': 'Kənd Təsərrüfatı İdarəetmə Sistemi',
    'version': '18.0.1.0.0',
    'category': 'Agriculture',
    'summary': 'Sahə, Parsel, Cərgə və Ağac İdarəetmə Sistemi',
    'description': """
        Kənd təsərrüfatı üçün tam həll:
        - Sahələrin idarə edilməsi
        - Parsellərin və cərgələrin izlənilməsi
        - Ağacların nömrələnməsi və sort idarəetməsi
        - Xəstəlik və zərərvericilərin izlənilməsi
        - Palet və soyuducu idarəetməsi
    """,
    'website': 'https://www.example.com',
    'depends': ['base', 'stock', 'product','purchase'],
    'data': [
        'security/ir.model.access.csv',
        'data/farm_data.xml',
        'views/farm_field_views.xml',
        'views/farm_parcel_views.xml',
        'views/farm_row_views.xml',
        'views/farm_tree_views.xml',
        'views/farm_variety_views.xml',
        'views/farm_disease_views.xml',
        'views/farm_pallet_views.xml',
        'views/farm_cooler_views.xml',
        'views/farm_operations_views.xml',
        'views/farm_worker_views.xml',
        'views/farm_menu.xml',
        'views/purchase_order.xml',
    ],

    'installable': True,
    'auto_install': False,
    'application': True,
}