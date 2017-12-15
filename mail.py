# Import smtplib for the actual sending function
import smtplib

# Import the email modules we'll need
from email.mime.text import MIMEText
#server = smtplib.SMTP('smtp.gmail.com', 587, timeout = 60)
server = smtplib.SMTP('localhost', 457, timeout = 60)

#server.ehlo()

#server.starttls()

#Next, log in to the server
#server.login("amarpreetsaini27589@gmail.com", "27maypreet*")

# Open a plain text file for reading.  For this example, assume that
# the text file contains only ASCII characters.
# Create a text/plain message


def send_mail_notification(data, to, alert_type):
    msg = MIMEText('data')
    msg['Subject'] = 'Alert | {} usage is high and exceeding the limit set'.format(alert_type)
    msg['From'] = 'amarpreetsaini27589@gmail.com'
    msg['To'] = to
    try:
        server.sendmail(msg['From'], [msg['To']], msg.as_string())
    except Exception as exc:
        import pdb;pdb.set_trace()
    server.quit()
