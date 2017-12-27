# -*- coding: utf-8 -*-

from odoo import models, fields, api

class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    department_id = fields.Many2one('hr.department', string='Office')

class HrDepartment(models.Model):
    _inherit = 'hr.department'

    name = fields.Char('Office Name', required=True)
    parent_id = fields.Many2one('hr.department', string='Office Department', index=True)
    dept_code = fields.Char(string="Office Code", required=False, help="Will be use for Document Code.")

class DtsDocumentType(models.Model):
    _name = 'dts.document.type'

    name = fields.Char('Document Type', required=True)
    active = fields.Boolean(string="Active?", default=True)

class DtsDocument(models.Model):
    _name = 'dts.document'
    _description = 'Memo Document'
    _order = 'transaction_date desc'

    def _get_employee_id(self):
        user_id = self.env.user.id
        res_resource = self.env['resource.resource'].search([('user_id', '=', user_id),('active', '=', True)],order="id desc",limit=1)
        if not res_resource and user_id != 1:
            raise ValidationError("No related employee assigned to current user. Please consult System Admin")
        else:
            resource_id = res_resource.id
            res_employee = self.env['hr.employee'].search([('resource_id', '=', resource_id),('active', '=', True)])
            employee_id = res_employee.id

        return employee_id

    name = fields.Char(string="Name", required=False, default='New Document')
    transaction_date = fields.Datetime(string="Transaction Date", required=False, default=fields.datetime.today(), readonly="1")
    sender_id = fields.Many2one(comodel_name="hr.employee", string="Sender", default=_get_employee_id, readonly=True, related_sudo=True)
    sender_office_id = fields.Many2one(comodel_name="hr.department", string="Sender Office", required=True, related_sudo=True,related='sender_id.department_id', readonly="1")
    # # Recipient
    document_type_id = fields.Many2one(comodel_name="dts.document.type", string="Document Type", required=True, domain=[('active', '=', True)])
    subject = fields.Char(string="Subject", required=True, )
    message = fields.Text(string="Message", required=False, )
    recipient_office_id = fields.Many2one(comodel_name="hr.department", string="Recipient Office", required=True)
    recipient_id = fields.Many2one(comodel_name="hr.employee", string="Recipient", required=True, domain="[('department_id','=',recipient_office_id)]")

    attachment_number = fields.Integer(compute='_get_attachment_number', string="Number of Attachments")
    attachment_ids = fields.One2many('ir.attachment','res_id', domain=[('res_model', '=', 'dts.document')], string='Attachments')
    receive_date = fields.Datetime(string="Received Date", required=False, readonly="1")

    tracking_type = fields.Selection(string="Tracking Type",
                                           selection=[
                                               ('incoming', 'Incoming'),
                                               ('outgoing', 'Outgoing'),
                                           ], default='outgoing')

    state = fields.Selection(string="state",
                                     selection=[
                                         ('draft', 'Draft'),
                                         ('cancel', 'Cancelled'),
                                         ('send', 'Sent'),
                                         ('read', 'Read'),
                                         ('receive', 'Received'),
                                     ], default='draft')

    recipient_user_id = fields.Many2one(comodel_name="res.users", string="Recipient User", readonly=True, related="recipient_id.user_id", store=False)
    current_user = fields.Many2one(comodel_name="res.users", string="Current User", compute="_get_current_user", store=False)

    @api.depends()
    def _get_current_user(self):
        self.update({'current_user':self.env.user.id})

    @api.depends()
    def _hide_accept(self):
        ret = self.recipient_id.user_id.id - self.env.user.id
        self.update({'hide_accept': ret})

    @api.multi
    def _get_attachment_number(self):
        read_group_res = self.env['ir.attachment'].read_group(
            [('res_model', '=', 'dts.document'), ('res_id', 'in', self.ids)],
            ['res_id'], ['res_id'])
        attach_data = dict((res['res_id'], res['res_id_count']) for res in read_group_res)
        for record in self:
            record.attachment_number = attach_data.get(record.id, 0)


    @api.multi
    def action_get_attachment_tree_view(self):
        attachment_action = self.env.ref('base.action_attachment')
        action = attachment_action.read()[0]
        action['context'] = {'default_res_model': self._name, 'default_res_id': self.ids[0]}
        action['domain'] = str(['&', ('res_model', '=', self._name), ('res_id', 'in', self.ids)])
        action['search_view_id'] = (self.env.ref('dts.ir_attachment_view_search_inherit_dts_document').id, )
        return action

    # @api.model
    # def create(self, values):
    #     values['name'] = 'Documents: '+ self.document_type_id.name
    #
    #     return super(DtsDocument, self).write(values)


    @api.multi
    def action_send(self):
        self.send_to_channel('Hi! Please see '+self.document_type_id.name+' with subject: '+self.subject, self.recipient_id.user_id)
        return self.write({'state': 'send', 'tracking_type': 'outgoing'})

    @api.multi
    def action_received(self):
        self.send_to_channel('Hi! I accepted your '+self.document_type_id.name+' with subject: '+self.subject, self.sender_id.user_id)
        return self.write({'state': 'receive','receive_date':fields.datetime.today()})

    def send_to_channel(self, body, to_user):
        users = to_user
        ch_obj = self.env['mail.channel']
        if users:
            for user in users:
                ch_name = user.name + ', ' + self.env.user.name
                ch = ch_obj.sudo().search([('name', 'ilike', str(ch_name))])
                if not ch:
                    ch = ch_obj.sudo().search([('name', 'ilike', str(self.env.user.name + ', ' + user.name))])
                ch.message_post(attachment_ids=[], body=body, content_subtype='html',
                message_type='comment', partner_ids=[], subtype='mail.mt_comment',
                email_from=self.env.user.partner_id.email, author_id=self.env.user.partner_id.id)

        return True

