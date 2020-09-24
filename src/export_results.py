import smtplib
from email.message import EmailMessage

smtp_server_dict = {'gmail': ('smtp.gmail.com', 587), 'outlook': ('smtp.office365.com', 587)}
cols = ['Job_Title', 'Location', 'Company', 'Date', 'Salary', 'Description', 'url']


def send_email(email: str, password: str, email_type: str, content):

    msg = EmailMessage()
    msg['Subject'] = "Indeed Job Search Results"
    msg['To'] = email
    msg['From'] = email
    msg.set_content(content)

    try:
        server = smtplib.SMTP(smtp_server_dict[email_type][0], smtp_server_dict[email_type][1])
        server.ehlo()
        server.starttls()
        server.login(email, password)
        text = msg.as_string()
        server.sendmail(email, email, text)
    except:
        print("Failed to connect to SMTP sever.")


def save_to_csv(data, filename: str):

    data.to_csv(filename, columns=cols)
