# Import smtplib for the actual sending function
import smtplib

# Import the email modules we'll need
from email.mime.text import MIMEText
server = smtplib.SMTP('smtp.gmail.com', 587)
server.ehlo()

server.starttls()

#Next, log in to the server
server.login("amarpreetsaini27589@gmail.com", "27maypreet*")

# Open a plain text file for reading.  For this example, assume that
# the text file contains only ASCII characters.
# Create a text/plain message
def send_mail_notification():

	msg = MIMEText("Helo workd")
	msg['Subject'] = 'The contents'
	msg['From'] = 'amarpreetsaini27589@gmail.com'
	msg['To'] = 'preetpal.singh@trantorinc.com'
	server.sendmail(msg['From'], [msg['To']], msg.as_string())
	server.quit()

send_mail_notification()