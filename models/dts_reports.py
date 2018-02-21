from odoo import models, fields, api
from openerp.exceptions import ValidationError

class (models.TransientModel):
    _name = 'dts.document.reports'

    transaction_date = fields.Datetime(string="Transaction Date", required=False, )
    sender_name = fields.Char(string="Sender", required=False, )
    document_no = fields.Char(string="Document Number", required=False, )
    subject = fields.Char(string="Subject", required=False, )
    document_status = fields.Char(string="Document Status", required=False, )
    send_date = fields.Datetime(string="", required=False, )
    receiver_name = fields.Char(string="Reciever", required=False, )
    receiver_status  = fields.Char(string="Reciever Status", required=False, )
    receiver_status_date = fields.Datetime(string="Reciever Status Date", required=False, )

    def action_generate(self):

        base_sql = """
        select transaction_date, concat(sender_office.name,'\', sender_emp.name_related) as sender_name, 
        document_no, subject, doc.state as document_status, send_date, 
        concat(receiver_office.name,'\',receiver_emp.name_related) as receiver_name, emp.state as receiver_status, 
        state_date as receiver_status_date
        from dts_document doc left join dts_employee_documents emp on doc.id = emp.document_id
        inner join hr_employee sender_emp on doc.sender_id = sender_emp.id
        inner join hr_employee receiver_emp on doc.sender_id = receiver_emp.id
        left join hr_department sender_office on doc.sender_office_id = sender_office.id
        left join hr_department receiver_office on emp.receiver_office_id = receiver_office.id
        """

        if
