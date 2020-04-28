import email
import imaplib
import re
from email.header import decode_header

import util.config


def decode_stuff(stuff):
    parts = decode_header(stuff)
    result = list()
    for part, encoding in parts:
        if encoding is not None:
            part = part.decode(encoding)
        if type(part) is bytes:
            part = part.decode()
        part = part.replace("\r\n", "").replace("\t", " ")
        result.append(part)

    return "".join(result)


mail_config = util.config.load_config("../config.json").mail
mail_account = util.config.load_config("../account_data.json").mail

email_user = mail_account.user
email_password = mail_account.password
inbox_host, inbox_port = mail_account.mail_server.incoming.host, mail_account.mail_server.incoming.port
group_registration_subject = mail_config.group_registration.subject

mail = imaplib.IMAP4_SSL(inbox_host, inbox_port)
mail.login(email_user, email_password)
mail.select("Inbox")
response_code, data = mail.search(None, 'SUBJECT', f'"{group_registration_subject}"')
print("Search:", response_code)

for mail_id in data[0].split()[::-1]:
    print("Mail-Id:", mail_id)
    response_code, data = mail.fetch(mail_id, '(RFC822)')
    raw_email = data[0][1]
    raw_email_string = raw_email.decode('utf-8')
    email_message = email.message_from_string(raw_email_string)

    subject = decode_stuff(email_message["Subject"])

    e_mail_combined = decode_stuff(email_message["From"])
    from_e_mail = re.search(r'.*<(.*@.*)>|(.*@.*)', e_mail_combined)
    from_e_mail = [entry for entry in from_e_mail.groups() if entry is not None][0]
    print(e_mail_combined)
    print(from_e_mail)
    print(subject)
    print(email_message["Date"])

    if email_message.is_multipart():
        first_part = email_message.get_payload()[0]

        content = first_part.get_payload(decode=True).decode(errors='ignore').strip()
    else:
        content = email_message.get_payload(decode=True).decode(errors='ignore').strip()

    print(content)
    print()

mail.logout()

