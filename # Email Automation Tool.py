# Email Automation Tool
# This script demonstrates bulk email sending, personalized templates, and scheduling.

import smtplib  # import the Simple Mail Transfer Protocol library to send emails
import ssl  # import Secure Sockets Layer support for encrypted connections
from email.message import EmailMessage  # import a helper class to build email messages
from string import Template  # import Template for simple text substitution
from datetime import datetime, timedelta  # import datetime utilities to schedule emails
import time  # import time for sleep and scheduling delays

# Define a template for the email body with placeholders for personalization
EMAIL_TEMPLATE = Template(
    """
    Hello $name,

    This is a personalized email sent through our automation tool.
    We are reaching out to share an important update with you.

    Best regards,
    Your Automation Team
    """
)

# Function to create an email message from the sender, recipient, subject, and body
def create_message(sender: str, recipient: str, subject: str, body: str) -> EmailMessage:
    message = EmailMessage()  # create a new EmailMessage object
    message["From"] = sender  # set the sender address
    message["To"] = recipient  # set the recipient address
    message["Subject"] = subject  # set the subject line
    message.set_content(body)  # set the plain-text body of the email
    return message  # return the constructed message object

# Function to send a single email using SMTP and TLS encryption
def send_email(smtp_server: str, smtp_port: int, username: str, password: str, message: EmailMessage):
    context = ssl.create_default_context()  # create a secure SSL context for the connection
    with smtplib.SMTP(smtp_server, smtp_port) as server:  # connect to the SMTP server
        server.starttls(context=context)  # upgrade the connection to TLS for security
        server.login(username, password)  # authenticate with the SMTP server
        server.send_message(message)  # send the email message

# Function to build a personalized email body for a recipient using the template
def personalize_email(name: str) -> str:
    return EMAIL_TEMPLATE.substitute(name=name)  # substitute the name into the template

# Function to send bulk emails to a list of recipients with personalized content
def send_bulk_emails(smtp_server: str, smtp_port: int, username: str, password: str, sender: str, recipients: list):
    for recipient_info in recipients:  # iterate over each recipient configuration
        recipient = recipient_info["email"]  # extract the email address
        name = recipient_info["name"]  # extract the recipient name
        body = personalize_email(name)  # build the personalized body
        subject = f"Personalized Update for {name}"  # create a subject line per recipient
        message = create_message(sender, recipient, subject, body)  # create the email message
        send_email(smtp_server, smtp_port, username, password, message)  # send the email

# Function to schedule an email to send at a later time
def schedule_email(send_time: datetime, callback, *args, **kwargs):
    now = datetime.now()  # get the current time
    delay = (send_time - now).total_seconds()  # compute delay in seconds until send_time
    if delay <= 0:
        callback(*args, **kwargs)  # if send_time is now or past, send immediately
    else:
        time.sleep(delay)  # wait until the scheduled send time
        callback(*args, **kwargs)  # send the email after the delay

if __name__ == "__main__":
    # Example configuration values that should be replaced with real credentials
    SMTP_SERVER = "smtp.example.com"  # SMTP server hostname
    SMTP_PORT = 587  # TLS port commonly used for SMTP
    USERNAME = "your_username@example.com"  # SMTP username for login
    PASSWORD = "your_password"  # SMTP password for login
    SENDER = "your_username@example.com"  # sender email address

    # Example recipients list for bulk email sending
    recipients = [
        {"email": "alice@example.com", "name": "Alice"},
        {"email": "bob@example.com", "name": "Bob"},
        {"email": "carol@example.com", "name": "Carol"},
    ]

    # Send bulk emails immediately to all recipients in the list
    # send_bulk_emails(SMTP_SERVER, SMTP_PORT, USERNAME, PASSWORD, SENDER, recipients)

    # Example scheduled email to send in 1 minute from now
    scheduled_time = datetime.now() + timedelta(minutes=1)  # choose a time in the future
    recipient_info = recipients[0]  # schedule email for the first recipient as an example
    scheduled_body = personalize_email(recipient_info["name"])  # build personalized content
    scheduled_subject = f"Scheduled Update for {recipient_info['name']}"  # subject for scheduled email
    scheduled_message = create_message(SENDER, recipient_info["email"], scheduled_subject, scheduled_body)

    # schedule_email(scheduled_time, send_email, SMTP_SERVER, SMTP_PORT, USERNAME, PASSWORD, scheduled_message)

    # The above example shows how to schedule an email in the future.
    # Uncomment the desired function call after updating SMTP credentials and recipient data.


