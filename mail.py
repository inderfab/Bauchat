import streamlit as st
import os

import smtplib
 
import dotenv

st.session_state.update(st.session_state)



def send_mail(to,subject,msg):
    dotenv.load_dotenv()

    MAIL_USER = os.getenv('MAIL_USER')
    MAIL_PWD = os.getenv("MAIL_PWD")
    SMTP_ADDRESS = os.getenv("SMTP_ADDRESS")

    smtpserver = smtplib.SMTP(SMTP_ADDRESS,587)
    smtpserver.ehlo()
    smtpserver.starttls()
    smtpserver.ehlo()
    smtpserver.login(MAIL_USER, MAIL_PWD)
    header = 'To:' + to + '\n' + 'From: ' + MAIL_USER + '\n' +  'Subject:' + subject
    msg = "{header} \n\n {msg} \n\n".format(header=header,msg=msg).encode('utf-8')
    smtpserver.sendmail(MAIL_USER, to, msg)
    st.write('Mail verschickt an ', to)
    smtpserver.quit()


def send_registration(to,verification_code):
    subject = "Bauchat - E-Mail verifizieren"
    msg = "Bitte geben Sie die folgende Nummer bei Ihrer nächsten Anmeldung ein um Ihre Anmeldung bei Bauchat zu verifizieren:\n"+str(verification_code)
    send_mail(to,subject,msg)


def send_pwd_reset(to,temp_pwd):
    subject = "Bauchat - Passwort zurückgesetzt"
    msg = "Melden Sie sich mit dem folgenden Passwort an, um ihr Passwort zu ändern\n"+str(temp_pwd)
    send_mail(to,subject,msg)