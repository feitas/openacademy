# -*- coding: utf-8 -*-
import logging
from datetime import timedelta

from odoo import models, fields, api, exceptions
from odoo.exceptions import ValidationError


_logger = logging.getLogger(__name__)


# 授课计划
class Course_plan(models.Model):
    _name = 'openacademy.course.plan'


    name = fields.Char(string="内容", required=True)
    sequence = fields.Integer(string="节次", default=1)
    plan_type = fields.Selection([
        ('theory',"理论"),
        ('exercise',"实操"),
        ('exam',"考试"),
    ], string="类型")
    hours = fields.Integer(string="课时")
    course = fields.Many2one('openacademy.course', string="课程")


# 课程
class Course(models.Model):
    _name = 'openacademy.course'

    name = fields.Char(string="名称", required=True)
    description = fields.Html(string="简介")
    # 责任人
    responsible_id = fields.Many2one('res.users', ondelete='set null', string="责任人", index=True)
    taro_id = fields.Many2one('res.users', ondelete='set null', string="教研室主任", index=True, required=True)
    dean_id = fields.Many2one('res.users', ondelete='set null', string="院长", index=True, required=True)
    
    # 当前登录用户
    current_user = fields.Integer(default = 0, compute='who')

    max_hour_perday = fields.Integer(string="每日最大课时", default=2)
    plan_ids = fields.One2many('openacademy.course.plan', 'course', string="授课计划")

    def who(self):
        pass
        _logger.info("----plan_ids----")
        _logger.info(self.plan_ids)

        # mail_dict = {
        #     'subject': "开课通知",
        #     'author_id': self.env.user.id,
        #     'email_from': "	Administrator <zhao_yc@126.com>",
        #     'email_to': "1060737113@qq.com",
        #     'body_html': "<p>你好，感谢参加课程%s</p>" % ("lol")
        # }
        # mail = self.env['mail.mail'].sudo().create(mail_dict)
        # mail.send()

        # _logger.info(self.env['mail.mail'].browse(108).body_html)
        # _logger.info("---------uid:" + str(self.env.uid))
        # for r in self:
        #     _logger.info("---------------r.responsible_id.id:" + str(r.responsible_id.id))
        #     _logger.info(r.current_user)
        #     # 用户是课程负责人
        #     if r.responsible_id.id == self.env.uid and self.env.uid != 1:
        #         r.current_user = 1
        #     # elif r.responsible_id.id == self.env.uid and self.env.uid == 1:
        #     #     r.current_user = 4
        #     # 教研室主任登录
        #     elif self.env.user.partner_id.position == "taro":
        #         r.current_user = 2
        #     # 院长登录
        #     elif self.env.user.partner_id.position == "dean":
        #         r.current_user = 3

        # _logger.info("---------current_user:" + str(current_user))

    state = fields.Selection([
        ('draft', "草稿"),
        ('unexamined_taro', "待教研室审核"),
        ('unexamined_dean', "待院长审批"),
        ('passed', "审批通过")
    ], default = 'draft')

    @api.multi
    def action_submit_for_examine(self):
        # 提交审核
        # 获取记录的创建者
        # _logger.info('------create_uid.id-------')
        # _logger.info(self.create_uid.id)
        # _logger.info(self.create_uid.name)
        if self.env.user.id != self.create_uid.id:
            raise ValidationError("抱歉，您不是本课程的创建人，不能提交审核")
        self.state = 'unexamined_taro'

    @api.multi
    def action_examine_taro_permit(self):
        # 教研室主任审核通过
        self.state = 'unexamined_dean'
        # if self.env.user.id != self.taro_id.id:
        #     raise ValidationError("只有教研室主任才能审批")
        self.state = 'unexamined_dean'


    @api.multi
    def action_examine_taro_reject(self):
        # 教研室主任审核驳回
        self.state = 'unexamined_dean'
        # if self.env.user.id != self.taro_id.id:
        #     raise ValidationError("只有教研室主任才能审批")
        self.state = 'draft'

    @api.multi
    def action_examine_dean_permit(self):
        # 院长审批通过
        # if self.env.user.id != self.dean_id.id:
        #     raise ValidationError("只有院长才能审批")
        self.state = 'passed'
        values = {
            'name': self.name,
            'type': 'service'
        }
        self.env['product.product'].sudo().create(values)

    @api.multi
    def action_examine_dean_reject(self):
        # 院长审批驳回
        # if self.env.user.id != self.dean_id.id:
        #     raise ValidationError("只有院长才能审批")
        self.state = 'draft'


    @api.multi
    def copy(self, default=None):
        # 重写复制逻辑
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


# 开课
class Session(models.Model):
    _name = 'openacademy.session'
    _inherit = ['mail.thread', 'ir.needaction_mixin']

    name = fields.Char(string="名称", required=True)
    start_date = fields.Date(string="开始日期", default=fields.Date.today)
    # 持续天数
    duration = fields.Float(digits=(6, 2), string="持续天数")
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
    # 已预约人数占满额人数的比例
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
        ('draft', "草稿"),
        ('confirmed', "已确认"),
        ('done', "完成"),
    ])
    course_log_ids = fields.One2many('openacademy.session.course.log', 'session', string="授课记录")
    # 关联的销售订单
    sale_order_count = fields.Integer(string='订单数', compute='compute_sale_order_count')
    # sale_order_count = fields.Integer(string='订单数')


    @api.multi
    def compute_sale_order_count(self):
        '''
        计算关联的订单数
        '''
        sale_orders = self.env['sale.order'].sudo().search([('partner_id', 'in', [attendee_id.id for attendee_id in self.attendee_ids]), ('product_id', '=', self.course_id.name)])
        # _logger.info('----------------------------886')
        # _logger.info(len(sale_orders))
        self.sale_order_count = len(sale_orders)

    @api.model
    def create(self, values):
        # 重写create方法
        # plans = self.course_id.plan_ids
        # return super(Course, self).create({'course_log_ids':plans})
        _logger.info('----------22222222---------')
        _logger.info(values['course_id'])
        # _logger.info(values['course_id'].plan_ids)
        # _logger.info(self.env['openacademy.course'].browse(values['course_id']).plan_ids)
        plans = self.env['openacademy.course'].browse(values['course_id']).plan_ids
        session = super(Session, self).create(values)
        for plan in plans:
            value = {
                'name': plan.name,
                'session': session.id
            }
            self.env['openacademy.session.course.log'].create(value)

        return session


    # 设置状态：draft confirmed done
    @api.multi
    def action_draft(self):
        # 学期的状态设为draft
        self.state = 'draft'

    @api.multi
    def action_confirm(self):
        """
        开课状态设为confirmed，确认开课
        """
        self.state = 'confirmed'
        # _logger.info(self.course_id.id)
        course_name = self.course_id.name
        # _logger.info('-------course_name:' + str(course_name))
        product = self.env['product.product'].sudo().search([('name', '=', course_name)])
        # _logger.info(product)
        for attendee_id in self.attendee_ids:
            # self.env['res.partner']
            # _logger.info(attendee_id.id)
            sale_order = self.env['sale.order'].sudo().create({'partner_id': attendee_id.id})
            # _logger.info(sale_order)
            # _logger.info('-------******-------')
            line_values = {
                'product_id': product.id,
                'price_unit': product.list_price,
                # 'product_uom_qty': qty,
                'order_id': sale_order.id
            }
            # tax_id
            # _logger.info(line_values)
            self.env['sale.order.line'].sudo().create(line_values)
            # TODO: 销售订单直接改状态这种方式是不可以的。复杂的单据一般有一定的业务逻辑
            sale_order.state = 'sale'

            mail_dict = {
                'subject': "开课通知",
                'author_id': self.env.user.id,
                'email_from': "	Administrator <zhao_yc@126.com>",
                'email_to': attendee_id.email,
                'body_html': u"<p>你好，感谢参加课程%s！</p>" % (course_name)
            }
            mail = self.env['mail.mail'].sudo().create(mail_dict)
            mail.send()

    @api.multi
    def action_done(self):
        # 学期的状态设为done
        self.state = 'done'

    @api.depends('seats', 'attendee_ids')
    def _taken_seats(self):
        # 根据参与者计算已被预约的席位的比例
        for r in self:
            if not r.seats:
                r.taken_seats = 0.0
            else:
                r.taken_seats = 100.0 * len(r.attendee_ids) / r.seats

    # 'seats'和'attendee_ids'变化时执行
    @api.onchange('seats', 'attendee_ids')
    def _verify_valid_seats(self):
        # 特定条件下显示警告
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
                    'message': "Increase seats or remove excess attendees",
                },
            }

    # start_date和duration发生变化时触发函数
    @api.depends('start_date', 'duration')
    def _get_end_date(self):
        # 计算截止日期
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
        # 计算持续天数
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
        # 计算小时数
        for r in self:
            r.hours = r.duration * 24

    def _set_hours(self):
        # 计算天数
        for r in self:
            r.duration = r.hours / 24

    @api.depends('attendee_ids')
    def _get_attendees_count(self):
        # 计算参与人数
        for r in self:
            r.attendees_count = len(r.attendee_ids)

    # @api.multi
    def to_related_sale_orders(self):
        # 以下两行错误，要用sale.order的视图
        # tree_id = self.env.ref('openacademy.session_tree_view').id
        # form_id = self.env.ref('openacademy.session_form_view').id
        return {
            'type': 'ir.actions.act_window',
            'name': 'see orders',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'sale.order',
            #注意此处m2m字段attendee_ids的用法
            'domain': str([('partner_id', 'in', [attendee_id.id for attendee_id in self.attendee_ids]), ('product_id', '=', self.course_id.name)]),
            # 'domain': str([('id', 'in', values)]),
            # 'views': [(tree_id, 'tree'), (form_id, 'form')],
            # 'search_view_id': search_id,
        }

    @api.constrains('instructor_id', 'attendee_ids')
    def _check_instructor_not_in_attendees(self):
        for r in self:
            # 导师不能同时是这个课的学生
            if r.instructor_id and r.instructor_id in r.attendee_ids:
                raise ValidationError("教导员不能同时是参与者")

# 班级授课记录
class Session_course_log(models.Model):
    _name = 'openacademy.session.course.log'

    date = fields.Date(string="日期")
    name = fields.Char(string="内容")
    # TODO: many2one类型的字段命名必须用_id为后缀，例如 session_id, 同样，one2many类型的字段要用_ids为后缀
    # TODO: 没有string属性
    session = fields.Many2one('openacademy.session')