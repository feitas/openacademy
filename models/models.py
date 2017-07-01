# -*- coding: utf-8 -*-

from datetime import timedelta
from odoo import models, fields, api, exceptions, _

# 课程
class Course(models.Model):
    _name = 'openacademy.course'

    name = fields.Char(string="名称", required=True)
    description = fields.Html(string="简介")
    # 责任人
    responsible_id = fields.Many2one('res.users', ondelete='set null', string="责任人", index=True)

    # 重写复制逻辑
    @api.multi
    def copy(self, default=None):
        default = dict(default or {})

        copied_count = self.search_count(
            [('name', '=like', u"Copy of {}%".format(self.name))])
        if not copied_count:
            new_name = u"Copy of {}".format(self.name)
        else:
            new_name = u"Copy of {} ({})".format(self.name, copied_count)

        default['name'] = new_name
        return super(Course, self).copy(default)

    # 不符合限制条件时阻止操作并给出警告
    _sql_constraints = [
        ('name_description_check',
         'CHECK(name != description)',
         "科目名和简介不能相同"),

        ('name_unique',
         'UNIQUE(name)',
         "科目名重复"),
    ]


# 学期
class Session(models.Model):
    _name = 'openacademy.session'

    name = fields.Char(string="名称", required=True)
    start_date = fields.Date(string="开始日期", default=fields.Date.today)
    # 持续天数
    duration = fields.Float(digits=(6, 2), help="持续天数")
    # 座位数
    seats = fields.Integer(string="座位数")
    active = fields.Boolean(string="有效", default=True)
    color = fields.Integer()
    # 教导员
    instructor_id = fields.Many2one('res.partner', string="教导员",
        domain=['|', ('instructor', '=', True),
                     ('category_id.name', 'ilike', "Teacher")])

    # instructor_id = fields.Many2one('res.partner', string="Instructor")
    # 学科
    course_id = fields.Many2one('openacademy.course',
        ondelete='cascade', string="科目", required=True)
    # 参与者
    attendee_ids = fields.Many2many('res.partner', string="参与者")
    # 一预约人数占满额人数的比例
    taken_seats = fields.Float(string="已分配座位", compute='_taken_seats')
    # 学期结束日期
    end_date = fields.Date(string="结束日期", store=True,
        compute='_get_end_date', inverse='_set_end_date')
    # 小时数
    hours = fields.Float(string="小时数",
                         compute='_get_hours', inverse='_set_hours')
    # 已参加/预约人数
    attendees_count = fields.Integer(
        string="已参加人数", compute='_get_attendees_count', store=True)

    state = fields.Selection([
        ('draft', "Draft"),
        ('confirmed', "Confirmed"),
        ('done', "Done"),
    ])

    # 设置状态：draft confirmed done
    @api.multi
    def action_draft(self):
        self.state = 'draft'

    @api.multi
    def action_confirm(self):
        self.state = 'confirmed'

    @api.multi
    def action_done(self):
        self.state = 'done'

    # 根据参与者计算已被预约的席位的比例
    @api.depends('seats', 'attendee_ids')
    def _taken_seats(self):
        for r in self:
            if not r.seats:
                r.taken_seats = 0.0
            else:
                r.taken_seats = 100.0 * len(r.attendee_ids) / r.seats

    # 'seats'和'attendee_ids'变化时执行
    @api.onchange('seats', 'attendee_ids')
    def _verify_valid_seats(self):
        if self.seats < 0:
            return {
                'warning': {
                    'title': "Incorrect 'seats' value",
                    'message':"座位数不能小于零",
                },
            }
        if self.seats < len(self.attendee_ids):
            return {
                'warning': {
                    'title': "Too many attendees",
                    # 翻译--改po文件无效
                    'message': _("Increase seats or remove excess attendees"),
                },
            }

    # start_date和duration发生变化时触发函数
    @api.depends('start_date', 'duration')
    def _get_end_date(self):
        for r in self:
            if not (r.start_date and r.duration):
                r.end_date = r.start_date
                continue

            # Add duration to start_date, but: Monday + 5 days = Saturday, so
            # subtract one second to get on Friday instead
            start = fields.Datetime.from_string(r.start_date)
            duration = timedelta(days=r.duration, seconds=-1)
            r.end_date = start + duration

    def _set_end_date(self):
        for r in self:
            if not (r.start_date and r.end_date):
                continue

            # Compute the difference between dates, but: Friday - Monday = 4 days,
            # so add one day to get 5 days instead
            start_date = fields.Datetime.from_string(r.start_date)
            end_date = fields.Datetime.from_string(r.end_date)
            r.duration = (end_date - start_date).days + 1

    @api.depends('duration')
    def _get_hours(self):
        for r in self:
            r.hours = r.duration * 24

    def _set_hours(self):
        for r in self:
            r.duration = r.hours / 24

    @api.depends('attendee_ids')
    def _get_attendees_count(self):
        for r in self:
            r.attendees_count = len(r.attendee_ids)

    @api.constrains('instructor_id', 'attendee_ids')
    def _check_instructor_not_in_attendees(self):
        for r in self:
            # 导师不能同时是这个课的学生
            if r.instructor_id and r.instructor_id in r.attendee_ids:
                raise exceptions.ValidationError("教导员不能同时是参与者")