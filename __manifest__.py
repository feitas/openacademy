# -*- coding: utf-8 -*-
{
    'name': "openacademy",

    'summary': """
        这是摘要。
        这是摘要。
        """,

    'description': """
        Long description of module's purpose 1234
    """,
    # 'description': 'description html', #  错误
    # /static/description/index.html作为描述，覆盖上面的description

    'author': "My Company",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    # 'category': 'Uncategorized',
    'category': 'Test',
    'version': '0.1',

    # any module necessary for this one to work correctly
    # board是仪表板
    'depends': ['base', 'board'],

    # always loaded
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
        'views/openacademy.xml',
        'views/partner.xml',
        'views/session_workflow.xml',
        'views/session_board.xml',
        'views/openacademy_views.xml',
        'reports.xml',
        'data/data.xml'
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
    'installable': True,
    'auto_install': False
}