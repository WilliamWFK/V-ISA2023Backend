# app.py
#
# Use this sample code to handle webhook events in your integration.
#
# 1) Paste this code into a new file (app.py)
#
# 2) Install dependencies
#   pip3 install flask
#   pip3 install stripe
#
# 3) Run the server on http://localhost:80

import json
import os
import stripe
import base64
import qrcode
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email.utils import formataddr
from email import encoders
from email.mime.text import MIMEText
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from requests import HTTPError
from PIL import Image
from flask import Flask, jsonify, request
import requests

# The library needs to be configured with your account's secret key.
# Ensure the key is kept out of any version control system you might be using.
stripe.api_key = 

# This is your Stripe CLI webhook secret for testing your endpoint locally.
endpoint_secret = 

# SCOPES = [
# "https://www.googleapis.com/auth/gmail.send"
# ]
# flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
# creds = flow.run_local_server(port=0)
# service = build('gmail', 'v1', credentials=creds)

app = Flask(__name__)

@app.route('/webhook', methods=['POST'])
def webhook():
    event = None
    payload = request.data
    sig_header = request.headers['STRIPE_SIGNATURE']

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
    except ValueError as e:
        # Invalid payload
        raise e
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        raise e

    # Handle the event
    if event['type'] == 'checkout.session.completed':
      session = event['data']['object']
      print("New Checkout completed")
      actions(session)
    # ... handle other event types
    else:
      print('Unhandled event type {}'.format(event['type']))

    return jsonify(success=True)

def extract_data(data):
    email = data["customer_details"]["email"]
    full_name = data["custom_fields"][0]["text"]["value"]
    drink_choice = data["custom_fields"][1]["dropdown"]["value"]
    return full_name, email, drink_choice

def encode_data(full_name, email, drink_choice):
    """Turns the data into a string and encodes it into base64."""
    data = f"{full_name} {email} {drink_choice}"
    data_bytes = data.encode("ascii")
    data_base64 = base64.b64encode(data_bytes)
    return data_base64

def decode_data(data_base64):
    """Decodes the data from base64 and turns it into full_name, email and drink choice."""
    data_bytes = base64.b64decode(data_base64)
    data = data_bytes.decode("ascii")
    full_name, email, drink_choice = data.split(" ")
    return full_name, email, drink_choice

def generate_qr_code(data_base64):
    """Generates a QR code from the data."""
    qr = qrcode.QRCode(
        version=1,
        box_size=10,
        border=5
    )
    qr.add_data(data_base64)
    qr.make(fit=True)
    img = qr.make_image(fill="black", back_color="white")
    img.save("qrcode.png")
    return img

def qr_code_inserter(img):
    """Inserts qr code into ticket.png and saves it as qrcode.png."""
    ticket = Image.open("Ticket.png")
    ticket.paste(img, (1510, 160))
    ticket.save("qrcode.png")

def send_email(full_name, email, drink_choice):
    """Sends an email with the QR code to the customer."""

    fromaddr = "williamfrederickkho+visa@gmail.com"
    toaddr = email
    # subject should be <fullname> V-ISA International Ball Ticket
    SUBJECT = f"{full_name} V-ISA International Ball Ticket"
    TEXT = f"Dear {full_name},\n\nThank you for supporting V-ISA, we’re very excited to see you at the International Ball!\nPlease find your ticket attached below. If you have any concerns kindly reply to this email or send an email to williamfrederickkho@gmail.com\n\nPlease do not forget to bring your Student ID and Valid ID Card (passport, drivers license, 18+ card)\n\nChosen beverage:\n{drink_choice}\n\nKind Regards,\nV-ISA"

    msg = MIMEMultipart()
    msg['From'] = formataddr(('William Kho (V-ISA)', fromaddr))
    msg['To'] = toaddr
    msg['Subject'] = SUBJECT
    body = TEXT
    msg.attach(MIMEText(body, 'plain'))
    filename = "qrcode.png"
    attachment = open("qrcode.png", "rb")
    p = MIMEBase('application', 'octet-stream')
    p.set_payload((attachment).read())
    encoders.encode_base64(p)
    p.add_header('Content-Disposition', f"attachment; filename= {filename}")
    msg.attach(p)
    s = smtplib.SMTP('smtp.gmail.com', 587)
    s.starttls()
    s.login(fromaddr, "") # add in app password
    text = msg.as_string()
    s.sendmail(fromaddr, toaddr, text)
    s.quit()


def add_to_csv(full_name, email, drink_choice):
    """Adds the data to a csv file."""
    csv_location = "tickets.csv"
    no = "no"
    with open(csv_location, "a") as csv_file:
        csv_file.write(f"{full_name},{email},{drink_choice},{no}\n")

def actions(data):
    full_name, email, drink_choice = extract_data(data)
    print(full_name, email, drink_choice)
    data_base64 = encode_data(full_name, email, drink_choice)
    print("Encoded: ", data_base64)
    img = generate_qr_code(data_base64)
    print("Generated QR")
    qr_code_inserter(img)
    print("Inserted QR")
    send_email(full_name, email, drink_choice)
    print("Sent Email")
    add_to_csv(full_name, email, drink_choice)
    print("Added to CSV")

if __name__ == '__main__':
    app.run(port=80, host="0.0.0.0")  # Replace with your desired port