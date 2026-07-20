import resend
from django.conf import settings

def send_email(subject, to, html_content):
    resend.api_key = settings.RESEND_API_KEY
    return resend.Emails.send({
        "from": "IELTSPro <noreply@ielts-pro.uz>",
        "to": [to],
        "subject": subject,
        "html": html_content,
    })