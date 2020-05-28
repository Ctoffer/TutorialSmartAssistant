import os
from email.encoders import encode_base64
from email.mime.multipart import MIMEMultipart, MIMEBase
from email.mime.text import MIMEText
from smtplib import SMTP

import util.config

mail_account = util.config.load_config("../account_data.json").mail

my_name = "Christopher Schuster"
email_user = mail_account.user
email_password = mail_account.password
my_mail = mail_account.address

from_email = f'{my_name} <{my_mail}>'  # or simply the email address
to_emails = ['A <christopher.schuster@t-online.de>', 'B <schustrchr@gmail.com>']

# Create multipart MIME email
email_message = MIMEMultipart()
email_message.add_header('To', ', '.join(to_emails))
email_message.add_header('From', from_email)
email_message.add_header('CC', from_email)
email_message.add_header('Subject', '[IAD-20] Feedback zu Zettel')

# Create text and HTML bodies for email
text_part = MIMEText('Hello world plain text!', 'plain')

# Create file attachment
attachment = MIMEBase("application", "octet-stream")
with open(os.path.join("E:", "envir_new.yml"), 'rb') as fp:
    attachment.set_payload(fp.read())  # Raw attachment data
encode_base64(attachment)
attachment.add_header("Content-Disposition", "attachment; filename=envir_new.yml")

# Attach all the parts to the Multipart MIME email
email_message.attach(text_part)
email_message.attach(attachment)

# Connect, authenticate, and send mail
smtp_server = SMTP(mail_account.mail_server.outgoing.host, port=mail_account.mail_server.outgoing.port)
smtp_server.set_debuglevel(1)  # Show SMTP server interactions
smtp_server.starttls()
smtp_server.login(email_user, email_password)
to_emails = to_emails + [from_email]
smtp_server.sendmail(from_email, to_emails, email_message.as_bytes())

# Disconnect
smtp_server.quit()
