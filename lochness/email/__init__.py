import os
import string
import smtplib
from email.mime.text import MIMEText

__dir__ = os.path.dirname(__file__)

def send(recipients, sender, subject, message):
    '''send an email'''
    email_template = os.path.join(__dir__, 'template.html')
    with open(email_template, 'r') as fo:
        template = string.Template(fo.read())
    message = template.safe_substitute(message=str(message))
    msg = MIMEText(message, 'html')
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = ', '.join(recipients)
    s = smtplib.SMTP('localhost')
    s.sendmail(sender, recipients, msg.as_string())
    s.quit()

def attempts_error(Lochness, attempt):
    msg = '\n'.join(attempt.warnings)
    send(Lochness['admins'], Lochness['sender'], 'error report', msg)

def metadata_error(Lochness, message):
    send(Lochness['admins'], Lochness['sender'], 'bad metadata', message)

