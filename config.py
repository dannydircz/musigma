import os

basedir = os.path.abspath(os.path.dirname(__file__))
class BaseConfig(object):
    SECRET_KEY = 'i am a baller'
    SECURITY_PASSWORD_SALT = 'mippy rox'
    DEBUG = True
    BCRYPT_LOG_ROUNDS = 13
    WTF_CSRF_ENABLED = True
    DEBUG_TB_ENABLED = False
    DEBUG_TB_INTERCEPT_REDIRECTS = False

    # mail settings
    MAIL_SERVER = 'smtp.googlemail.com'
    MAIL_PORT = 465
    MAIL_USE_TLS = False
    MAIL_USE_SSL = True

    # gmail authentication
    MAIL_USERNAME = 'musigmaapp@gmail.com'
    MAIL_PASSWORD = 'Cocacola16'

    # mail accounts
    MAIL_DEFAULT_SENDER = 'musigmaapp@gmail.com'
