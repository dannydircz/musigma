__author__ = 'DannyDircz'

import config
#from config import MAIL_DEFAULT_SENDER

from flask.ext.mail import Message
from app import mail

def send_email(to, subject, template):
    msg = Message(
        subject,
        recipients=[to],
        html=template,
        sender= config.BaseConfig.MAIL_DEFAULT_SENDER
    )
    mail.send(msg)