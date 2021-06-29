# -*- coding: utf-8 -*-
{
    'name': "po_luarprop",

    'summary': """
        Modul Surat Jalan Luar Modifikasi untuk Purchase Order""",

    'description': """ \
    UPDATE v10.0.2.0 (29/02/2020)\n
     - [NEW] Autofill Product Description field\n
     - [ADD] UoM field in TreeView
    """,

    'author': "Satusoft",
    'website': "https://satusoft.com/",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/10.0/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Apps',
    'version': '2.0',

    # any module necessary for this one to work correctly
    'depends': ['base',
                'purchase'
                ],

    # always loaded
    'data': [
        #'security/ir.model.access.csv',
        'views/views.xml',
        'views/stock.xml'
    ],

}