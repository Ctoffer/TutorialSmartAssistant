from email.encoders import encode_base64
from email.header import Header
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from os.path import basename
from smtplib import SMTP


class EMailSender:
    def __init__(self, mail_account, my_name):
        self._email_user = mail_account.user
        self._email_password = mail_account.password
        self._my_mail = mail_account.address

        self._host = mail_account.mail_server.outgoing.host
        self._port = mail_account.mail_server.outgoing.port

        self._my_name = my_name
        self._smtp_server = None

    def __enter__(self):
        self._smtp_server = SMTP(self._host, self._smtp_server)
        self._smtp_server.starttls()
        # self._smtp_server.set_debuglevel(1)
        self._smtp_server.login(self._email_user, self._email_password)
        return self

    def send_feedback(self, students, message, feedback_path, exercise_prefix, exercise_number, debug=False):
        def normalize_mail(name, mail):
            name = Header(f'{name}'.encode('utf-8'), 'utf-8').encode()
            return f'{name} <{mail}>'

        from_email = normalize_mail(self._my_name, self._my_mail)

        to_emails = [normalize_mail(student.muesli_name, student.muesli_mail) for student in students]

        email_message = MIMEMultipart()
        email_message.add_header('From', from_email)
        email_message.add_header('To', ', '.join(to_emails))
        email_message.add_header('CC', from_email)
        email_message.add_header('Subject', f'[IAD-20] Feedback zu {exercise_prefix} {exercise_number}')

        text_part = MIMEText(message, 'plain')
        attachment = create_file_attachment(feedback_path)

        email_message.attach(text_part)
        email_message.attach(attachment)

        if debug:
            to_emails = [from_email]
        else:
            to_emails = to_emails + [from_email]

        self._smtp_server.sendmail(
            from_addr=from_email,
            to_addrs=to_emails,
            msg=email_message.as_bytes()
        )

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._smtp_server.quit()


def create_file_attachment(feedback_path):
    file_name = basename(feedback_path)

    attachment = MIMEBase("application", "octet-stream")
    with open(feedback_path, 'rb') as fp:
        attachment.set_payload(fp.read())
    encode_base64(attachment)
    attachment.add_header("Content-Disposition", f"attachment; filename={file_name}")

    return attachment
