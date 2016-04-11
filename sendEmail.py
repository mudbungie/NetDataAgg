#!/usr/local/bin/python3.4


def sendEmail(authUser, authPass, recipient, subject, body, fromAddress=''):
	import smtplib
	from email.mime.multipart import MIMEMultipart
	from email.mime.text import MIMEText
	smtpServer = 'smtp.sendgrid.net'
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

	# Send the message via local SMTP server.
	s = smtplib.SMTP(smtpServer, smtpPort)
	s.ehlo()
	s.starttls()
	s.ehlo()
	s.login(authUser, authPass)

	# sendmail function takes 3 arguments: sender's address, recipient's address, message
	s.sendmail(fromAddress, recipient, msg.as_string())
	s.quit()
