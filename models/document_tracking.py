# -*- coding: utf-8 -*-

from odoo import models, fields, api
from openerp.exceptions import ValidationError
import time

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


    def _get_default_group_id(self):
        group_id = self.env.sudo().ref('dts.group_dts_document_user').id

        return group_id

    def _get_username(self):
        self.user_name = self.user_id.name

    department_id = fields.Many2one('hr.department', string='Office')
    first_name = fields.Char(string="First Name")
    middle_name = fields.Char(string="Middle Name")
    last_name = fields.Char(string="Last Name")
    suffix = fields.Selection(SUFFIX, string="Suffix")
    prefix = fields.Many2one('res.partner.title', string="Prefix")
    user_name = fields.Char(string="User Name")
    group_id = fields.Many2one(comodel_name="res.groups", string="Access Level", required=True,
                               domain="[('category_id.name', '=','Document Tracking')]",related_sudo=True,
                               defalut=_get_default_group_id)

    state = fields.Selection(string="", selection=[('', ''), ('', ''), ], required=False, )

    _sql_constraints = [
        ('name_uniq', 'unique(name)', 'Employee already exists!'),
        ('user_id_uniq', 'unique(user_id)', 'User already in used!'),
    ]

    @api.model_cr
    def init(self):
        admin_id = self.env.ref('hr.employee_root').id
        group_id = self.env.ref('hr.group_hr_user').id
        self._cr.execute("""update hr_employee set user_name='admin', group_id = %s where id = %s;
    update resource_resource set active=False where user_id = %s""" % (group_id, admin_id, admin_id))
        self._cr.commit()

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
        flag = self.env['res.users'].has_group('hr.group_hr_user')
        if 'group_id' in values:
            g_res = self.env['res.groups'].browse(values['group_id'])

            if not flag and g_res.name in ('System Manager','Department Manager'):
                raise ValidationError('You are only allowed to add Access Level: User.')

        if 'suffix' in values:
            if values['suffix']:
                name = '%s %s' % (name, values['suffix'])
        values['name'] = '%s %s' % (name, values['middle_name'].title().strip())
        res = super(HrEmployee, self).create(values)

        if res.user_name:

            found = self.env['res.users'].search([('login','=',res.user_name)])
            if found:
                raise ValidationError('User Name Already Exists!')

            new_user_id = self.env['res.users'].sudo().create({
                'name': res.name,
                'login': res.user_name,
                'company_id': res.company_id.id,
                'state': 'active',
                'password': res.user_name,
                'active': res.active,
                'email': '%s@tboli.gov.ph' % res.user_name
            })
            res.write({'user_id': new_user_id.id,'new': 'new'})

            if res.group_id:
                #DTS Access
                gid = res.group_id.id
                new_uid = new_user_id.id
                # self._cr.execute('insert into res_groups_users_rel(gid,uid) values(%s,%s)' % (gid,new_uid))
                # self._cr.commit()

                #Delete the default Employees Access
                grp_default_user = self.env.ref('base.default_user').id
                self._cr.execute('select * from res_groups_users_rel where gid=%s and uid = %s' % (grp_default_user,new_uid))
                found = self._cr.fetchone()
                if found:
                    self._cr.execute('delete from res_groups_users_rel where gid=%s and uid = %s' % (grp_default_user,new_uid))
                    self._cr.commit()
                    
                g_res = self.env['res.groups'].browse(gid)
                if g_res.name == 'System Manager':
                    #Employees Access
                    grp_mgt_emp_id = self.env.ref('hr.group_hr_user').id
                    self._cr.execute('select * from res_groups_users_rel where gid=%s and uid = %s' % (grp_mgt_emp_id,new_uid))
                    found = self._cr.fetchone()
                    if not found:
                        self._cr.execute('insert into res_groups_users_rel(gid,uid) values(%s,%s)' % (grp_mgt_emp_id,new_uid))
                        self._cr.commit()

                    #Administration Access
                    grp_mgt_admin_id = self.env.ref('dts.group_dts_document_manager').id
                    self._cr.execute('select * from res_groups_users_rel where gid=%s and uid = %s' % (grp_mgt_admin_id,new_uid))
                    found = self._cr.fetchone()
                    if not found:
                        self._cr.execute('insert into res_groups_users_rel(gid,uid) values(%s,%s)' % (grp_mgt_admin_id,new_uid))
                        self._cr.commit()

                elif g_res.name == 'Department Head':
                    #Employees Access
                    grp_spr_emp_id = self.env.ref('hr.group_hr_user').id
                    self._cr.execute('select * from res_groups_users_rel where gid=%s and uid = %s' % (grp_spr_emp_id,new_uid))
                    found = self._cr.fetchone()
                    if not found:
                        self._cr.execute('insert into res_groups_users_rel(gid,uid) values(%s,%s)' % (grp_spr_emp_id,new_uid))
                        self._cr.commit()

                elif g_res.name == 'User':
                    #Employee Access
                    grp_emp_user_id = self.env.ref('base.group_user').id
                    self._cr.execute('select * from res_groups_users_rel where gid=%s and uid = %s' % (grp_emp_user_id,new_uid))
                    found = self._cr.fetchone()
                    if not found:
                        self._cr.execute('insert into res_groups_users_rel(gid,uid) values(%s,%s)' % (grp_emp_user_id,new_uid))
                        self._cr.commit()

        if 'department_id' in values:
            if values['department_id']:
                department = self.env['hr.department'].browse(values['department_id'])['name']
                vals['name'] = "%s \ %s" % (department,values['name'])
                vals['employee_id'] = res.id
                vals['department_id'] = values['department_id']
                vals['user_id'] = new_user_id.id
                vals['active'] = values['active']
                self.env['dts.document.recipient'].sudo().create(vals)

        return res

    @api.multi
    def write(self, values):
        flag = self.env['res.users'].has_group('hr.group_hr_user')
        if 'group_id' in values:
            g_res = self.env['res.groups'].browse(values['group_id'])

            if not flag and g_res.name in ('Manager','Supervisor'):
                raise ValidationError('You are not allowed to edit User Level.')

        if 'last_name' in values or 'first_name' in values or 'middle_name' in values or 'suffix' in values:
            last_name = values['last_name'].title().strip() if 'last_name' in values else self.last_name
            first_name = values['first_name'].title().strip() if 'first_name' in values else self.first_name
            middle_name = values['middle_name'].title().strip() if 'middle_name' in values else self.middle_name
            suffix = values['suffix'] if 'suffix' in values else self.suffix
            name = '%s, %s' % (last_name, first_name)
            if suffix:
                name = '%s %s' % (name, suffix)
            values['name'] = '%s %s' % (name, middle_name)

        add_user = not self.user_name and 'user_name' in values
        prev_g_res = self.env['res.groups'].browse(self.group_id.id)

        res = super(HrEmployee, self).write(values)

        if add_user:
            new_user_id = self.env['res.users'].sudo().create({
                'name': self.name,
                'login': self.user_name,
                'company_id': self.company_id.id,
                'state': 'active',
                'password': self.user_name,
                'active': self.active

            })
            self.write({'user_id': new_user_id.id})

        edit = True
        if 'new' in values:
            edit = False

        if 'group_id' in values and edit:
            #DTS Access
            gid = values['group_id']
            new_uid = new_user_id.id if 'user_id' in values else self.user_id.id

            #Delete Previous DTS Access
            self._cr.execute('delete from res_groups_users_rel where gid = %s and uid = %s' % (prev_g_res.id,new_uid))
            self._cr.commit()

            self._cr.execute('insert into res_groups_users_rel(gid,uid) values(%s,%s)' % (gid,new_uid))
            self._cr.commit()

            #Previous
            if prev_g_res.name == 'System Manager':
                #Delete Previous Employee Access
                del_id = self.env.ref('hr.group_hr_user').id
                self._cr.execute('delete from res_groups_users_rel where gid = %s and uid = %s' % (del_id,new_uid))
                self._cr.commit()

                #Delete Previous Administration Access
                del_id = self.env.ref('dts.group_dts_document_manager').id
                self._cr.execute('delete from res_groups_users_rel where gid = %s and uid = %s' % (del_id,new_uid))
                self._cr.commit()

            elif prev_g_res.name == 'Department Head':
                #Delete Previous Employee Access
                del_id = self.env.ref('hr.group_hr_user').id
                self._cr.execute('delete from res_groups_users_rel where gid = %s and uid = %s' % (del_id,new_uid))
                self._cr.commit()

            elif prev_g_res.name == 'User':
                #Delete Previous Employee Access
                del_id = self.env.ref('base.group_user').id
                self._cr.execute('delete from res_groups_users_rel where gid = %s and uid = %s' % (del_id,new_uid))
                self._cr.commit()

            #New Access
            g_res = self.env['res.groups'].browse(gid)
            if g_res.name == 'System Manager':
                #Employees Access
                grp_mgt_emp_id = self.env.ref('hr.group_hr_user').id
                self._cr.execute('select * from res_groups_users_rel where gid=%s and uid = %s' % (grp_mgt_emp_id,new_uid))
                found = self._cr.fetchone()
                if not found:
                    self._cr.execute('insert into res_groups_users_rel(gid,uid) values(%s,%s)' % (grp_mgt_emp_id,new_uid))
                    self._cr.commit()

                #Administration Access
                grp_mgt_admin_id = self.env.ref('dts.group_dts_document_manager').id
                self._cr.execute('select * from res_groups_users_rel where gid=%s and uid = %s' % (grp_mgt_admin_id,new_uid))
                found = self._cr.fetchone()
                if not found:
                    self._cr.execute('insert into res_groups_users_rel(gid,uid) values(%s,%s)' % (grp_mgt_admin_id,new_uid))
                    self._cr.commit()

            elif g_res.name == 'Department Manager':
                #Employees Access
                grp_spr_emp_id = self.env.ref('hr.group_hr_user').id
                self._cr.execute('select * from res_groups_users_rel where gid=%s and uid = %s' % (grp_spr_emp_id,new_uid))
                found = self._cr.fetchone()
                if not found:
                    self._cr.execute('insert into res_groups_users_rel(gid,uid) values(%s,%s)' % (grp_spr_emp_id,new_uid))
                    self._cr.commit()

            elif g_res.name == 'User':
                #Employee Access
                grp_emp_user_id = self.env.ref('base.group_user').id
                self._cr.execute('select * from res_groups_users_rel where gid=%s and uid = %s' % (grp_emp_user_id,new_uid))
                found = self._cr.fetchone()
                if not found:
                    self._cr.execute('insert into res_groups_users_rel(gid,uid) values(%s,%s)' % (grp_emp_user_id,new_uid))
                    self._cr.commit()

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

    # @api.onchange('dept_code')
    # def onchange_dept_code(self):
    #     dept_code = str(self.dept_code)
    #     if  dept_code:
    #         self.dept_code = dept_code.upper()


class DtsDocumentType(models.Model):
    _name = 'dts.document.type'

    name = fields.Char('Document Type', required=True)
    doc_code = fields.Char('Document Type Code', required=True)
    active = fields.Boolean(string="Active?", default=True)

class DtsDocumentDelivery(models.Model):
        _name = 'dts.document.delivery'

        name = fields.Char('Delivery Method', required=True)
        require_attachment = fields.Boolean(string="Require Attachment", default=True)
        active = fields.Boolean(string="Active", default=True)

class DtsDocumentRecipient(models.Model):
        _name = 'dts.document.recipient'

        name = fields.Char('Name', required=True)
        employee_id = fields.Many2one(comodel_name="hr.employee", string="Recipient", required=False, )
        department_id = fields.Many2one(comodel_name="hr.department", string="Department", required=False, )
        user_id = fields.Many2one(comodel_name="res.users", string="User", required=False, )
        active = fields.Boolean(string="Active", default=True, )

class DtsDocument(models.Model):
    _name = 'dts.document'
    # _inherit = 'mail.thread'
    # _mail_post_access = 'read'
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

    @api.depends('name')
    def _get_default_doc_type(self):
        ret = None
        rec = self.env['dts.config'].browse(1)
        if rec:
            if rec.document_type_id_default:
                ret = rec.document_type_id_default.id
        return ret

    @api.depends('name')
    def _get_show_doc_type(self):
        ret = False
        rec = self.env['dts.config'].browse(1)
        if rec:
            ret = rec.show_document_type
        return ret

    @api.depends('name')
    def _get_default_doc_delivery(self):
        ret = None
        rec = self.env['dts.config'].browse(1)
        if rec:
            if rec.show_delivery_method and rec.delivery_method_id_default:
                ret = rec.delivery_method_id_default.id
        return ret

    @api.depends('name')
    def _get_show_doc_delivery(self):
        ret = False
        rec = self.env['dts.config'].browse(1)
        if rec:
            ret = rec.show_delivery_method
        return ret

    @api.one
    @api.depends('document_no')
    def get_name(self):
        self.name = '%s: %s' % (self.document_type_id.name, self.document_no)

    name = fields.Char(string="Name", required=False, compute='get_name',store=False, default='New Document')
    document_no = fields.Char(string="Document Number", required=False, readonly=True)
    transaction_date = fields.Datetime(string="Transaction Date", required=False, default=fields.datetime.today(), readonly="1")
    send_date = fields.Datetime(string="Date Send", required=False, readonly="1")
    sender_id = fields.Many2one(comodel_name="hr.employee", string="Sender", default=_get_employee_id, readonly=True, related_sudo=True)
    sender_office_id = fields.Many2one(comodel_name="hr.department", string="Sender Office",
                                       related_sudo=True,related='sender_id.department_id',readonly="1",store=True)
    show_document_type = fields.Boolean(string="Show Document Type", default=_get_show_doc_type)
    document_type_id = fields.Many2one(comodel_name="dts.document.type", string="Document Type", required=False, domain="[('active', '=', True)]", default=_get_default_doc_type)
    subject = fields.Char(string="Subject", required=True, )
    message = fields.Text(string="Message", required=False, )
    recipient_id = fields.Many2many(comodel_name='dts.document.recipient', string="Recipient", required="1", domain="[('active','=',True),('user_id','!=',uid)]")
    attachment_number = fields.Integer(compute='_get_attachment_number', string="Number of Attachments")
    attachment_ids = fields.One2many('ir.attachment','res_id', domain=[('res_model', '=', 'dts.document')], string='Attachments')
    receive_date = fields.Datetime(string="Date Received", required=False, readonly="1")
    show_delivery_method = fields.Boolean(string="Show Delivery Method", default=_get_show_doc_delivery)
    delivery_method_id = fields.Many2one(comodel_name="dts.document.delivery",string="Delivery Method", required=False, domain="[('active', '=', True)]", default=_get_default_doc_delivery)
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
# require_reply = fields.Boolean(string="Needs Reply?", default=False)
    recipient_ids = fields.One2many(comodel_name="dts.employee.documents", inverse_name="document_id", string="Receiver", required=False, )

    @api.model
    def create(self, values):
        doc_code = None
        rec = self.env['dts.document.type'].browse(values['document_type_id'])
        if rec:
            doc_code = rec.doc_code
        seq_number = self.env['dts.sequence']._get_code_series(doc_code)
        if seq_number:
            values['document_no'] = seq_number
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
        action['search_view_id'] = (self.env.ref('dts.ir_attachment_view_search_dts_document').id, )
        return action

    @api.multi
    def action_send(self):
        if self.show_delivery_method and self.delivery_method_id:
            rec = self.env['dts.document.delivery'].browse(self.delivery_method_id.id)
            if rec.require_attachment and self.attachment_number < 1:
                raise ValidationError("Cannot proceed, Please provide an attachment First.")

        # tag the receiver
        vals = {'document_id': self.id}
        for recipient in self.recipient_id:
            found = self.env['dts.document.recipient'].sudo().browse(recipient.id)
            if found:
                vals['receiver_id'] = found.user_id.id
                vals['employee_id'] = found.employee_id.id
                # vals['receiver_office_id'] = found.department_id.id
                self.env['dts.employee.documents'].sudo().create(vals)
                self.send_to_channel('Hi! I send a <b>%s</b> with subject: <b>%s</b>.' % (self.name,self.subject), found.user_id.id)
        return self.write({'state': 'send', 'tracking_type': 'outgoing','send_date':fields.datetime.today()})


    def send_to_channel(self, body, to_user_id):
        to_user_rec = self.env['res.users'].browse(to_user_id)
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
    # _inherit = 'mail.thread'
    # _mail_post_access = 'read'
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
    receiver_office_id = fields.Many2one(comodel_name="hr.department", string="Receiver Office",store=True)
    sender_id = fields.Many2one(comodel_name="hr.employee", string="Sender", store=False, related="document_id.sender_id")
    sender_office_id = fields.Many2one(comodel_name="hr.department", string="Sender Office",
                                       related_sudo=True, store=False, related='document_id.sender_id.department_id')
    subject = fields.Char(string="Subject", required=True, store=False, related='document_id.subject')
    message = fields.Text(string="Message", required=False, store=False, related='document_id.message')
    name = fields.Char(string="Name", required=False, store=False, related='document_id.name')
    transaction_date = fields.Datetime(string="Transaction Date", store=False, related='document_id.transaction_date')
    send_date = fields.Datetime(string="Date Send", store=False, related='document_id.send_date')
    show_document_type = fields.Boolean(string="Show Document Type", related='document_id.show_document_type')
    document_type_id = fields.Many2one(comodel_name="dts.document.type", store=False, related='document_id.document_type_id')
    attachment_number = fields.Integer(compute='_get_attachment_number', store=False, related='document_id.attachment_number')
    attachment_ids = fields.One2many('ir.attachment','res_id', string='Attachments', store=False, related='document_id.attachment_ids')
    show_delivery_method = fields.Boolean(string="Show Document Type", related='document_id.show_delivery_method')
    delivery_method_id = fields.Many2one(comodel_name="dts.document.delivery",string="Delivery Method", store=False, related='document_id.delivery_method_id')
    state_date = fields.Datetime(string="Status Date", required=False, readonly="1")
    # require_reply = fields.Boolean(string="Require Reply", related='document_id.require_reply')
    # message_ids = fields.One2many(
    #     'mail.message', 'res_id', string='Messages', auto_join=True, related='document_id.message_ids')

    @api.multi
    def action_read(self):
        self.env['dts.document'].send_to_channel('Hi! I am reading the document <b>%s</b> with subject: <b>%s</b>.' % (self.name,self.subject), self.sender_id.user_id.id)
        return self.write({'state': 'read','state_date':fields.datetime.today()})

    @api.multi
    def action_none(self):
        ret = None
        if self.show_delivery_method and self.delivery_method_id:
            rec = self.env['dts.document.delivery'].browse(self.delivery_method_id.id)
            if rec.require_attachment:
                if self.attachment_number < 1:
                    raise ValidationError("Attachment is missing, please inform the sender.")
                raise ValidationError("You must click the Documents first to accept it")
            else:
               ret = self.action_accept()
        return ret

    @api.multi
    def action_accept(self):
        self.env['dts.document'].send_to_channel('Hi! I now accept the document <b>%s</b> with subject: <b>%s</b>.' % (self.name,self.subject), self.sender_id.user_id.id)
        return self.write({'state': 'receive','state_date':fields.datetime.today()})

    @api.multi
    def action_viewed_docs(self):
        self.env['dts.document'].send_to_channel('Hi! I am viewing the attachments of document <b>%s</b> with subject: <b>%s</b>.' % (self.name,self.subject), self.sender_id.user_id.id)
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
        action['search_view_id'] = (self.env.ref('dts.ir_attachment_view_search_dts_document').id, )
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
                                                            order="id desc", limit=1) or None
        if not res_resource and user_id != 1:
            raise ValidationError("No related employee assigned to current user. Please consult System Admin")
        else:
            resource_id = res_resource.id
            res_employee = self.env['hr.employee'].search([('resource_id', '=', resource_id)])
            if res_employee:
                if not res_employee.department_id:
                    raise ValidationError("Employee is not assigned to Department")
                else:
                    if res_employee.department_id.dept_code:
                        office_code = res_employee.department_id.dept_code or None

        rec = self.search([('company_id','=',company_id),('doc_code','=',doc_code),('office_code','=',office_code),('year','=',year),('active','=',True)])
        if not rec:
            res = self.create({'office_code':office_code,'doc_code':doc_code})
            if res:
                rec = self.search([('company_id', '=', company_id),('doc_code','=',doc_code), ('office_code', '=', office_code), ('year', '=', year),
                               ('active', '=', True)])

        if rec:
            seq_series = str(rec.next_number).zfill(rec.length)
            rec.write({'next_number':rec.next_number+1})
            ret = '%s-%s' % (rec.year,seq_series)
            if rec.office_code:
                ret = '%s-%s' % (rec.office_code,ret)
            # if doc_code:
            #     ret = '%s: %s' % (doc_code,ret)

        return ret

class DtsReports(models.TransientModel):
    _name = 'dts.reports'

    report_name = fields.Many2one('ir.actions.report.xml',string="Report Name", domain="[('model', 'like', 'dts.%')]")
    document_type_id = fields.Many2one('dts.document.type',string="Document Type")
    document_delivery_id = fields.Many2one('dts.document.delivery',string="Delivery Method")
    office_id = fields.Many2one('hr.department',string="Department")
    date_from = fields.Date(string="From"
                             ,default = lambda *a: time.strftime('%Y-%m-%d'))
    date_to = fields.Date(string="To"
                           , default = lambda *a: time.strftime('%Y-%m-%d'))
    state = fields.Selection(string="State",
                             selection=[('choose', ''), ('get', ''), ],
                             required=False,
                             default='choose')
    msg = fields.Char(String="Message")

    @api.multi
    def action_back(self):
        self.write({'state':'choose','msg':None})
        return {"type": "ir.actions.do_nothing",}

    # @api.multi
    # def action_download(self):
    #     self.write({'state':'get','msg':None})
    #     return {"type": "ir.actions.do_nothing",}

    @api.multi
    def action_print(self):

        self.ensure_one()
        data = {}
        data['ids'] = self.env.context.get('active_ids', [])
        data['model'] = self.env.context.get('active_model', 'ir.ui.menu')
        data['form'] = self.read(['date_from','date_to','document_type_id','document_delivery_id','office_id','report_name'])[0]
        self.write({'state':'get','msg':None})
        return {"type": "ir.actions.do_nothing",}

        return self._print_report(data)

    def _print_report(self, data):
        print 'test handler'

        return self.env['report'].sudo().get_action(self, 'dts.document_report_template',
                                                        data=data)