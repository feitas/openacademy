# -*- coding: utf-8 -*-
import logging,json
from odoo import models, fields, api


_logger = logging.getLogger(__name__)


class Wizard_sheet(models.TransientModel):
    _name = 'openacademy.attendance.wizard'


    def _default_sessions(self):
        # session_ids的默认值，即触发当前wizard的openacademy.session
        return self.env['openacademy.session'].browse(self._context.get('active_ids'))

    def save_sheets(self):
        '''批量生成考勤表'''
        for session in self.session_ids:
            count = 1
            for partner in session.attendee_ids:
                partner_course_log = self.env['feitas.partner.course.log'].sudo().search([('session_id','=',session.id), ('partner_id','=',partner.id)])
                # _logger.info('-------89-------')
                # _logger.info(partner_course_log)
                if not partner_course_log:
                    val = {
                        'name': str(count),
                        'session_id': session.id,
                        'partner_id': partner.id
                    }
                    result = self.env['feitas.partner.course.log'].sudo().create(val)
                    _logger.info('---------create----------')
                    _logger.info(result)
                count += 1


    session_ids = fields.Many2many('openacademy.session',
        string="开课记录", required=True, default=_default_sessions)