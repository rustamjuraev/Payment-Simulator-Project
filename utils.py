import random
from email.message import EmailMessage
from smtplib import SMTP
import os
from datetime import date

def generate_security_code():
    string =""
    for x in range(0, 6):
        string += str(random.randint(0,9))
    return string

def send_verification_code(recipient_email,security_code):
    try:
        with SMTP("smtp.gmail.com", port=587) as server:

            msg = EmailMessage()
            msg["Subject"] = "Verification Code"
            msg["From"] = os.environ["ADMIN_EMAIL"]
            msg["To"] = recipient_email
            msg.set_content(security_code)
            server.starttls()
            server.login(os.environ["ADMIN_EMAIL"],os.environ["PASSWORD"])
            server.send_message(msg)
    except Exception as e:
        print("Failed to send email, check connection and try again")
        return -1

def generate_card_number():
    card_number = "8600"
    for x in range(0,12):
        card_number += str(random.randint(0,9))
    return card_number

def generate_expiry_date():
    today = date.today()
    year = str(today).split("-")[0]
    month = str(today).split("-")[1]
    exp_year = int(year) + 5
    exp_date = str(exp_year) + "/" + month
    return exp_date

def generate_cvc():
    cvc = ""
    for x in range(0,3):
        cvc += str(random.randint(0,9))
    return cvc