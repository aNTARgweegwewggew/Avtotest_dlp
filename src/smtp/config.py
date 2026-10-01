import os
from dotenv import load_dotenv

load_dotenv()

MAIL_HOST = os.environ["HOST_MAIL"]
MAIL_USERNAME = os.environ["USERNAME"]
MAIL_PASSWORD = os.environ["PASSWORD_MAIL"]

SMTP_PORT = 25