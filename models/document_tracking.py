# -*- coding: utf-8 -*-

from odoo import models, fields, api
from openerp.exceptions import ValidationError

SUFFIX = [
    ('jr', 'JR'),
    ('sr', 'SR'),
    ('iii', 'III'),
    ('iv', 'IV'),
    ('v', 'V'),
    ('vi', 'VI'),
    ('vii', 'VII')
]

class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    department_id = fields.Many2one('hr.department', string='Office')
    first_name = fields.Char(string="First Name")
    middle_name = fields.Char(string="Middle Name")
    last_name = fields.Char(string="Last Name")
    suffix = fields.Selection(SUFFIX, string="Suffix")
    prefix = fields.Many2one('res.partner.title', string="Prefix")

    _sql_constraints = [
        ('name_uniq', 'unique(name)', 'Employee already exists!'),
        ('user_id_uniq', 'unique(user_id)', 'User already in used!'),
    ]

    @api.onchange('first_name', 'middle_name', 'last_name', 'suffix')
    def onchange_name(self):

        name = ''
        sep = ', '

        if self.last_name:
            lname = self.last_name.title().strip()
        else:
            lname = ''
            sep = ''

        if lname:
            name = '%s%s' % (lname, sep)

        if self.first_name:
            fname = self.first_name.title().strip()
        else:
            fname = ''

        if fname:
            name = '%s%s%s' % (name, ' ', fname)

        if self.suffix:
            suffix = self.suffix.title().strip()
        else:
            suffix = ''

        if suffix:
            name = '%s%s%s' % (name, ' ', suffix)

        if self.middle_name:
            mname = self.middle_name.title().strip()
        else:
            mname = ''

        if mname:
            name = '%s%s%s' % (name, ' ', mname)

        self.name = name

        self.first_name = fname.title().strip()
        self.middle_name = mname.title().strip()
        self.last_name = lname.title().strip()

    @api.model
    def create(self, values):
        vals = {}
        name = '%s, %s' % (values['last_name'].title().strip(), values['first_name'].title().strip())
        if values['suffix']:
            name = '%s %s' % (name, values['suffix'])
        values['name'] = '%s %s' % (name, values['middle_name'].title().strip())
        res = super(HrEmployee, self).create(values)
        if 'department_id' in values:
            if values['department_id']:
                department = self.env['hr.department'].browse(values['department_id'])['name']
                vals['name'] = "%s \ %s" % (department,values['name'])
                vals['employee_id'] = res.id
                vals['department_id'] = values['department_id']
                vals['user_id'] = values['user_id']
                vals['active'] = values['active']
                self.env['dts.document.recipient'].sudo().create(vals)

        if res.identification_id:
            user_id = self.env['res.users'].sudo().create({
                'name': res.name,
                'login': res.identification_id,
                'company_id': res.company_id.id,
                'state': 'active',
                'password': res.identification_id,
                'active': res.active
            })
            print 'user_id',user_id
            res.write({'user_id': user_id.id})

        return res

    @api.multi
    def write(self, values):
        if 'last_name' in values or 'first_name' in values or 'middle_name' in values or 'suffix' in values:
            last_name = 'last_name' in values if values['last_name'].title().strip() else self.last_name
            first_name = 'first_name' in values if values['first_name'].title().strip() else self.first_name
            middle_name = 'middle_name' in values if values['middle_name'].title().strip() else self.middle_name
            suffix = 'suffix' in values if values['suffix'] else self.suffix
            name = '%s, %s' % (last_name, first_name)
            if suffix:
                name = '%s %s' % (name, suffix)
            values['name'] = '%s %s' % (name, middle_name)

        add_user = not self.identification_id and 'identification_id' in values

        res = super(HrEmployee, self).write(values)

        if add_user:
            user_id = self.env['res.users'].sudo().create({
                'name': self.name,
                'login': self.identification_id,
                'company_id': self.company_id.id,
                'state': 'active',
                'password': self.identification_id,
                'active': self.active

            })
            print user_id
            self.write({'user_id': user_id.id})

        recipient_env = self.env['dts.document.recipient']
        if res:
            vals={}
            recipient_res = recipient_env.sudo().search([('employee_id', '=', self.id)])

            if recipient_res:
                if 'department_id' in values or 'active' in values or 'name' in values or 'user_id' in values:
                    vals['employee_id']=self.id
                    name = self.name
                    if 'name' in values:
                        name = values['name']

                    department = self.department_id.name
                    if 'department_id' in values:
                        vals['department_id'] = values['department_id']
                        department = self.env['hr.department'].browse(values['department_id'])['name']

                    vals['name'] = '%s \ %s' % (department,name)
                    if 'active' in values:
                        vals['active'] = values['active']

                    if 'user_id' in values:
                        vals['user_id'] = values['user_id']

                    recipient_res.sudo().write(vals)
            else:
                if 'department_id' in values:
                    if values['department_id']:
                        department = self.department_id.name
                        vals['name'] = "%s \ %s" % (department,self.name)
                        vals['employee_id'] = self.id
                        vals['department_id'] = values['department_id']
                        vals['user_id'] = self.user_id.id
                        vals['active'] = self.active
                        recipient_env.sudo().create(vals)
            return res

class HrDepartment(models.Model):
    _inherit = 'hr.department'

    name = fields.Char('Office Name', required=True)
    parent_id = fields.Many2one('hr.department', string='Office Department', index=True)
    dept_code = fields.Char(string="Office Code", required=False, help="Will be use for Document Code.")

    _sql_constraints = [
        ('name_uniq', 'unique(name)', 'Office already exists!'),
        ('dept_code_uniq', 'unique(dept_code)', 'Office Code already exists!'),
    ]

class DtsDocumentType(models.Model):
    _name = 'dts.document.type'

    name = fields.Char('Document Type', required=True)
    doc_code = fields.Char('Document Type Code', required=True)
    active = fields.Boolean(string="Active?", default=True)

class DtsDocumentDelivery(models.Model):
        _name = 'dts.document.delivery'

        name = fields.Char('Delivery Method', required=True)
        active = fields.Boolean(string="Active", default= True )

class DtsDocumentRecipient(models.Model):
        _name = 'dts.document.recipient'

        name = fields.Char('Name', required=True)
        employee_id = fields.Many2one(comodel_name="hr.employee", string="Recipient", required=False, )
        department_id = fields.Many2one(comodel_name="hr.department", string="Department", required=False, )
        user_id = fields.Many2one(comodel_name="res.users", string="User", required=False, )
        active = fields.Boolean(string="Active", default=True, )

class DtsDocument(models.Model):
    _name = 'dts.document'
    _description = 'Memo Document'
    _order = 'transaction_date desc, send_date desc'

    @api.depends()
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

    name = fields.Char(string="Name", required=False, default='New Document', readonly=True)
    transaction_date = fields.Datetime(string="Transaction Date", required=False, default=fields.datetime.today(), readonly="1")
    send_date = fields.Datetime(string="Send Date", required=False, readonly="1")
    sender_id = fields.Many2one(comodel_name="hr.employee", string="Sender", default=_get_employee_id, readonly=True, related_sudo=True)
    sender_office_id = fields.Many2one(comodel_name="hr.department", string="Sender Office", required=True, related_sudo=True,related='sender_id.department_id', readonly="1")
    # # Recipient
    document_type_id = fields.Many2one(comodel_name="dts.document.type", string="Document Type", required=True, domain="[('active', '=', True)]")
    subject = fields.Char(string="Subject", required=True, )
    message = fields.Text(string="Message", required=False, )

    recipient_id = fields.Many2many(comodel_name='dts.document.recipient', string="Recipient", required="1", domain="[('active','=',True),('user_id','!=',uid)]")
    attachment_number = fields.Integer(compute='_get_attachment_number', string="Number of Attachments")
    attachment_ids = fields.One2many('ir.attachment','res_id', domain=[('res_model', '=', 'dts.document')], string='Attachments')
    receive_date = fields.Datetime(string="Received Date", required=False, readonly="1")
    delivery_method_id = fields.Many2one(comodel_name="dts.document.delivery",string="Delivery Method", required=True, domain="[('active', '=', True)]")

    tracking_type = fields.Selection(string="Tracking Type",
                                           selection=[
                                               ('incoming', 'Incoming'),
                                               ('outgoing', 'Outgoing'),
                                           ], default='outgoing')

    state = fields.Selection(string="state",
                                     selection=[
                                         ('draft', 'Draft'),
                                         ('send', 'Sent'),
                                     ], default='draft')

    recipient_ids = fields.One2many(comodel_name="dts.employee.documents", inverse_name="document_id", string="Receiver", required=False, )

    @api.model
    def create(self, values):
        doc_code = None
        rec = self.env['dts.document.type'].browse(values['document_type_id'])
        if rec:
            doc_code = rec.doc_code
        seq_number = self.env['dts.sequence']._get_code_series(doc_code)
        if seq_number:
            values['name'] = seq_number
        res = super(DtsDocument, self).create(values)
        return res

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

    @api.multi
    def action_send(self):
        if self.attachment_number < 1:
            raise ValidationError("Cannot proceed, Please provide an attachment First.")

        # tag the receiver
        vals = {'document_id': self.id}
        for recipient in self.recipient_id:
            found = self.env['dts.document.recipient'].sudo().browse(recipient.id)
            if found:
                vals['receiver_id'] = found.user_id.id
                vals['employee_id'] = found.employee_id.id
                self.env['dts.employee.documents'].sudo().create(vals)
                self.send_to_channel('Hi! I send '+self.name+' with subject: '+self.subject, found.user_id.id)
        return self.write({'state': 'send', 'tracking_type': 'outgoing','send_date':fields.datetime.today()})


    def send_to_channel(self, body, to_user_id):
        to_user_rec = self.env['res.users'].browse(to_user_id)
        fr_user_rec = self.env['res.users'].browse(self.env.user.id)
        ch_obj = self.env['mail.channel']
        ch_partner_obj = self.env['mail.channel.partner']
        vals = {}

        if to_user_rec:
            to_partner_id = to_user_rec.partner_id.id
            to_partner_name = to_user_rec.partner_id.name
            fr_partner_id = self.env.user.partner_id.id
            fr_partner_name = self.env.user.partner_id.name

            ch_name = '%s, %s' % (to_partner_name, fr_partner_name)

            sql = """select a.channel_id
            from mail_channel_partner a, (
            select channel_id, partner_id 
            from mail_channel_partner
            where partner_id = %s) b
            where a.partner_id = %s
            and a.channel_id = b.channel_id""" % (to_partner_id, fr_partner_id)

            self.env.cr.execute(sql)

            res = self.env.cr.dictfetchone()
            if res:
                channel_id = res['channel_id']

            else:
                vals['public'] = 'private'
                vals['name'] = ch_name
                vals['channel_type'] = 'chat'
                vals['group_public_id'] = 1
                ch_rec = ch_obj.sudo().create(vals)
                if ch_rec:
                    channel_id = ch_rec.id
                    ch_partner_obj.create({'channel_id':channel_id,'partner_id':to_partner_id})
                    ch_partner_obj.create({'channel_id':channel_id,'partner_id':fr_partner_id})

            ch = ch_obj.sudo().search([('id', '=', channel_id)])

            if ch:
                ch.message_post(attachment_ids=[], body=body, content_subtype='html',
                                message_type='comment', partner_ids=[], subtype='mail.mt_comment',
                                email_from=self.env.user.partner_id.email, author_id=self.env.user.partner_id.id)

        return True

class DtsEmployeeDocuments(models.Model):
    _name = 'dts.employee.documents'
    _order = 'id desc'

    receiver_id = fields.Many2one(comodel_name="res.users", string="User", required=False, )
    document_id = fields.Many2one(comodel_name="dts.document", string="Document", required=False, )
    state = fields.Selection(string="Status",
                                     selection=[
                                         ('unread', 'Unread'),
                                         ('read', 'Read Message'),
                                         ('view', 'Viewed Documents'),
                                         ('receive', 'Accepted'),
                                     ], default='unread')
    employee_id = fields.Many2one(comodel_name="hr.employee", string="Recipient", required=False)
    receiver_office_id = fields.Many2one(comodel_name="hr.department", string="Receiver Office", store=False, related='employee_id.department_id')
    sender_id = fields.Many2one(comodel_name="hr.employee", string="Sender", store=False, related="document_id.sender_id")
    sender_office_id = fields.Many2one(comodel_name="hr.department", string="Sender Office", store=False, related='document_id.sender_id.department_id')
    subject = fields.Char(string="Subject", required=True, store=False, related='document_id.subject')
    message = fields.Text(string="Message", required=False, store=False, related='document_id.message')
    name = fields.Char(string="Name", required=False, store=False, related='document_id.name')
    transaction_date = fields.Datetime(string="Transaction Date", store=False, related='document_id.transaction_date')
    send_date = fields.Datetime(string="Send Date", store=False, related='document_id.send_date')
    document_type_id = fields.Many2one(comodel_name="dts.document.type", store=False, related='document_id.document_type_id')
    attachment_number = fields.Integer(compute='_get_attachment_number', store=False, related='document_id.attachment_number')
    attachment_ids = fields.One2many('ir.attachment','res_id', string='Attachments', store=False, related='document_id.attachment_ids')
    delivery_method_id = fields.Many2one(comodel_name="dts.document.delivery",string="Delivery Method", store=False, related='document_id.delivery_method_id')
    state_date = fields.Datetime(string="Status Date", required=False, readonly="1")

    @api.multi
    def action_read(self):
        self.env['dts.document'].send_to_channel('Hi! I am reading the document '+self.name+' with subject: '+self.subject, self.sender_id.user_id.id)
        return self.write({'state': 'read','state_date':fields.datetime.today()})

    @api.multi
    def action_none(self):
        raise ValidationError("You must click the Documents first to accept it")
        return None

    @api.multi
    def action_accept(self):
        self.env['dts.document'].send_to_channel('Hi! I now accept the document '+self.name+' with subject: '+self.subject, self.sender_id.user_id.id)
        return self.write({'state': 'receive','state_date':fields.datetime.today()})

    @api.multi
    def action_viewed_docs(self):
        self.env['dts.document'].send_to_channel('Hi! I am viewing the attachments of document '+self.name+' with subject: '+self.subject, self.sender_id.user_id.id)
        return self.write({'state': 'view','state_date':fields.datetime.today()})

    @api.multi
    def _get_attachment_number(self):
        read_group_res = self.env['ir.attachment'].read_group(
            [('res_model', '=', 'dts.document'), ('res_id', 'in', self.document_id.ids)],
            ['res_id'], ['res_id'])
        attach_data = dict((res['res_id'], res['res_id_count']) for res in read_group_res)
        for record in self:
            record.attachment_number = attach_data.get(record.id, 0)

    @api.multi
    def action_get_attachment_tree_view(self):
        if self.state == 'read':
            self.action_viewed_docs()
        attachment_action = self.env.ref('base.action_attachment')
        action = attachment_action.read()[0]
        action['context'] = {'default_res_model': self.document_id._name, 'default_res_id': self.document_id.ids[0]}
        action['domain'] = str(['&', ('res_model', '=', self.document_id._name), ('res_id', 'in', self.document_id.ids)])
        action['search_view_id'] = (self.env.ref('dts.ir_attachment_view_search_inherit_dts_document').id, )
        return action


class DtsSequence(models.Model):
    _name = 'dts.sequence'
    _description = 'Sequence'

    def _get_employee_office_code(self):
        user_id = self.env.user.id
        code = ''
        res_resource = self.env['resource.resource'].search([('user_id', '=', user_id),('active', '=', True)],order="id desc",limit=1)
        if not res_resource and user_id != 1:
            raise ValidationError("No related employee assigned to current user. Please consult System Admin")
        else:
            resource_id = res_resource.id
            res_employee = self.env['hr.employee'].search([('resource_id', '=', resource_id),('active', '=', True)])
            if res_employee:
                if not res_employee.department_id:
                    raise ValidationError("Employee is not assigned to Department")
                else:
                    code = res_employee.department_id.dept_code

        return code

    # name = fields.Char(string="Name", required=False, )
    doc_code = fields.Char(string="Document Type Code", required=False,)
    office_code = fields.Char(string="Office Code", required=False, default=_get_employee_office_code)
    company_id = fields.Many2one(comodel_name="res.company", string="Company", required=False, default=lambda self: self.env.user.company_id.id)
    next_number = fields.Integer(string="Next Number", required=False, default=1)
    length = fields.Integer(string="Series Length", required=False, default=4)
    year = fields.Char(string="Year", required=False, default=fields.date.today().strftime('%Y'))
    active = fields.Boolean(string="Active", default=True)

    def _get_code_series(self, doc_code):
        ret = None
        office_code = None
        user_id = self.env.user.id
        year = fields.date.today().strftime('%Y-%m-%d')[:4]
        company_id = self.env.user.company_id.id
        res_resource = self.env['resource.resource'].search([('user_id', '=', user_id), ('active', '=', True)],
                                                            order="id desc", limit=1)
        if not res_resource and user_id != 1:
            raise ValidationError("No related employee assigned to current user. Please consult System Admin")
        else:
            resource_id = res_resource.id
            res_employee = self.env['hr.employee'].search([('resource_id', '=', resource_id), ('active', '=', True)])
            if res_employee:
                if not res_employee.department_id:
                    raise ValidationError("Employee is not assigned to Department")
                else:
                    if res_employee.department_id.dept_code:
                        office_code = res_employee.department_id.dept_code

        rec = self.search([('company_id','=',company_id),('office_code','=',office_code),('year','=',year),('active','=',True)])
        if not rec:
            res = self.create({'office_code':office_code})
            if res:
                rec = self.search([('company_id', '=', company_id), ('office_code', '=', office_code), ('year', '=', year),
                               ('active', '=', True)])

        if rec:
            seq_series = str(rec.next_number).zfill(rec.length)
            rec.write({'next_number':rec.next_number+1})
            ret = '%s-%s' % (rec.year,seq_series)
            if rec.office_code:
                ret = '%s-%s' % (rec.office_code,ret)
            if doc_code:
                ret = '%s: %s' % (doc_code,ret)

        return ret




