__author__ = 'DannyDircz'


from config import MAIL_DEFAULT_SENDER

from flask.ext.mail import Message
from app import mail

def send_email(to, subject, template):
    msg = Message(
        subject,
        recipients=["musigmaapp@gmail.com"],
        html=template,
        sender= MAIL_DEFAULT_SENDER
    )
    mail.send(msg)