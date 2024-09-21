import random
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from time import sleep
import certifi
import logging

from django.contrib.auth.models import Group
from django.template.loader import render_to_string
from django.utils.crypto import get_random_string
from django.utils.html import strip_tags

logger = logging.getLogger('home')
from config import settings


def send_email(receiver_email, user, random_pass):
    sender_email = settings.EMAIL_HOST_USER
    password = settings.EMAIL_HOST_PASSWORD
    receiver_email = "contact.makeaton@gmail.com"

    message = MIMEMultipart("alternative")
    message["Subject"] = "Dashboard for Make-A-Ton 7.0"
    message["From"] = sender_email
    message["To"] = receiver_email

    # Render the email content using the HTML template
    email_content = render_to_string('emails/team_dashboard_login.html', {
        'full_name': user.full_name,
        'email': user.email,
        'password': random_pass,
    })

    # Strip HTML tags for the plain text alternative
    plain_message = strip_tags(email_content)

    part1 = MIMEText(plain_message, "plain")
    part2 = MIMEText(email_content, "html")

    # Add HTML/plain-text parts to MIMEMultipart message
    # The email client will try to render the last part first
    message.attach(part1)
    message.attach(part2)

    # Create secure connection with server and send email
    context = ssl.create_default_context(cafile=certifi.where())
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
        server.login(sender_email, password)
        server.sendmail(
            sender_email, receiver_email, message.as_string()
        )


def send_bulk_email(queryset):
    i = 0
    for user in queryset:
        # check user exists in a group
        if not Group.objects.get(name='Team Leader').user_set.filter(id=user.id).exists():
            logger.info(f'{user.email} is not a team leader so skipping')
            continue
        try:
            random_password = get_random_string(length=5)
            user.set_password(random_password)
            user.save()
            logger.info(f'Password reset for {user.email}')

            i += 1
            if i % 50 == 0:
                sleep(random.randint(200, 210))
            else:
                sleep(random.randint(4, 10))
            send_email(user.email, user, random_password)
            i += 1
            if i % 50 == 0:
                sleep(random.randint(200, 210))
            else:
                sleep(random.randint(4, 10))
        except Exception as e:
            logger.error(f"Error in sending email to {user.email}: {e}")
