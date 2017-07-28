# -*- coding: utf-8 -*-
from odoo import fields, models


# 扩展res.partner
class Partner(models.Model):
    _inherit = 'res.partner'

    # Add a new column to the res.partner model, by default partners are not
    # instructors
    instructor = fields.Boolean("Instructor", default=False)
    position = fields.Selection([
        ('TARO', "教研室主任"),
        ('dean', "院长")
    ], string="职位", default=False)

    session_ids = fields.Many2many('openacademy.session',
        string="Attended Sessions", readonly=True)