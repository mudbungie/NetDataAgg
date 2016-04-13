#!/usr/local/bin/python3.4

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

def sendEmail(authUser, authPass, recipient, subject, body):
    
    fromAddress = authUser
    
    smtpServer = 'smtp.gmail.com'
    smtpPort = 587
    
    # Create message container - the correct MIME type is multipart/alternative.
    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = fromAddress
    msg['To'] = recipient
    
    # Record the MIME types of both parts - text/plain and text/html.
    message = MIMEText(body, 'html')
    
    # Attach into message container.
    msg.attach(message)
    
    try:
        # Send the message via local SMTP server.
        s = smtplib.SMTP(smtpServer, smtpPort)
        s.ehlo()
        s.starttls()
        s.ehlo()
        s.login(authUser, authPass)
        
        # sendmail function takes 3 arguments: sender's address, recipient's address, message
        s.sendmail(fromAddress, recipient, msg.as_string())
        s.quit()
        return True
    except:
        # I've gotten a lot of errors; easier not to crash anything else, and handle
        # that logic outside the function, than to dive smtplib code
        print('SendEmail message send failure')
        return False
