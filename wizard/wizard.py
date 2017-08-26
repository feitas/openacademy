# -*- coding: utf-8 -*-
import logging,json
from odoo import models, fields, api


_logger = logging.getLogger(__name__)


class Wizard(models.TransientModel):
    _name = 'openacademy.wizard'


    def _default_sessions(self):
        # session_ids的默认值是触发当前wizard的openacademy.session
        return self.env['openacademy.session'].browse(self._context.get('active_ids'))

    session_ids = fields.Many2many('openacademy.session',
        string="Sessions", required=True, default=_default_sessions)
    attendee_ids = fields.Many2many('res.partner', string="Attendees")

    @api.multi
    def subscribe(self):
        # 给每个课程添加参与者，如果课程已经有要添加的参与者，不重复添加
        for session in self.session_ids:
            session.attendee_ids |= self.attendee_ids
        return {}