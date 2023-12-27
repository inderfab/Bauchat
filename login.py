import streamlit as st
import re
import hashlib
from streamlit_extras.switch_page_button import switch_page
from deta import Deta
import dotenv
import os
import mail
from random import randint, sample
import time
import string

dotenv.load_dotenv()
deta = Deta(os.getenv('DETA_KEY'))
db = deta.Base("bauchat_base")

def insert_user(user_dict):
    """Returns the user on a successful user creation, otherwise raises and error"""
    return db.put(data=user_dict, key= user_dict["username"])


def fetch_all_users():
    """Returns a dict of all users"""
    res = db.fetch()
    return res.items


def get_user(username):
    """If not found, the function will return None"""
    return db.get(username)


def update_user(username, updates):
    """If the item is updated, returns None. Otherwise, an exception is raised"""
    return db.update(updates, username)


def user_update_message_and_tokens(username, updates, usage):
    """If the item is updated, returns None. Otherwise, an exception is raised"""
    user_data = get_user(username)

    history = user_data["history"]
    history.insert(0,updates)

    token_month, token_total = update_user_tokens(user_data, usage)
    st.session_state.token_change = True
    db.update({"history":history,"token_month":token_month,"token_total":token_total}, username)


def update_user_tokens(user_data, usage):
    token_update = usage["total_tokens"] #{"prompt_tokens":2357"completion_tokens":121"total_tokens":2478}

    date = time.strftime("%Y-%m")


    # wenn es schon einträge gibt
    token_month = user_data["token_month"] #verlauf pro monat
    if date in token_month:
        existing_tokens_month = token_month[date]
        existing_tokens_month += token_update
        token_month.update({date:existing_tokens_month}) #verlauf addieren
    else:
        token_month.update({date:token_update})

    token_total = user_data["token_total"] 
    token_total += token_update
   
    return token_month, token_total



def delete_user(username):
    """Always returns None, even if the key does not exist"""
    return db.delete(username)


def make_hashes(password):
	return hashlib.sha256(str.encode(password)).hexdigest()


def reset_pw(user):
    char_set = string.ascii_uppercase + string.digits
    temp_pwd = ''.join(sample(char_set*6, 6))
    u_data = get_user(user)
    update_user(user, {"password":temp_pwd, "password_reset":True})
    mail.send_pwd_reset(u_data["email"],temp_pwd)
    st.write("Prüfen Sie ihr E-Mail um ihr Passwort zurückzusetzten")


def login():
    #with st.expander(label="Login",expanded=True):
    if "user_welcome" not in st.session_state:
        st.session_state.user_welcome = "Sie sind nicht eingeloggt"
    #st.write(st.session_state.user_welcome)

    user = st.text_input("Benutzername", key = "user_login")
    pwd = st.text_input("Passwort",type='password',key = "pwd")
    if st.button("Anmelden"):
        st.session_state["anmeldeversuch"] = True
    if st.session_state["anmeldeversuch"] == True:
        login_user(user,pwd)


def login_fast():
    if st.session_state.username == '':
        user ="fabioi"
        pwd = "dada3131"
        pwd = make_hashes(pwd)
        u_data = get_user(user)
        st.session_state.username = u_data["username"]
        st.session_state["u_data"] = u_data
        


def forget_pwd():      
    with st.expander("Passwort zurücksetzen"):
        user = st.text_input(label="Benutzername eingeben")
        but = st.button(label="Passwort zurücksetzen")
        if user and but:
            try:
                reset_pw(user)
            except:
                st.write("Email konnte nicht versendet werden, prüfen Sie ihre Eingabe")
        else:
            st.markdown('Korrekte E-Mail Adresse eingeben und Button drücken')
  

        
def registration():
    with st.expander("Registrieren",expanded=False):
        with st.form(key = "registration", clear_on_submit=False):
            username_free = True
            email_filled = False
            pwd_filled = False
            user = st.text_input("Benutzername", key = "user_re") 
            vorname = st.text_input("Vorname", key = "vorn_re")
            nachname = st.text_input("Nachname", key = "nachn_re")

            email = st.text_input("Email",key = "email_re")
            email_regex = re.compile(r"^[A-Za-z0-9\.\+_-]+@[A-Za-z0-9\._-]+\.[a-zA-Z]*$")

            if email_regex.match(email):
                 email_filled = True
                 
            pwd = st.text_input("Passwort",type='password',key="pwd_re")
            if len(pwd) <= 7:
                st.write("mindestens 8 Charakter eingeben")
            else:
                 pwd_filled = True


            if st.form_submit_button("Registrieren"):
                if get_user(user) != None:
                        st.write("Benutzername bereits vergeben")
                        username_free = False
                if email_filled and pwd_filled and username_free == True:
                    hashed_pwd = make_hashes(pwd)
                    verification_code = randint(100000,999999)
                    data = {"username":user, "vorname":vorname, "nachname":nachname, "email":email, 
                            "password":hashed_pwd, "password_reset":False,
                            "verifikation":False,"verification_code":verification_code,
                            "history":[],"token_month":{},"token_total":0, "token_available":10000}
                    mail.send_registration(email, verification_code)
                    insert_user(data)
                    

def user_reset_password(user):
    pass

def login_user(user,pwd):         
    pwd = make_hashes(pwd)
    u_data = get_user(user)
    
    if u_data != None and u_data["verifikation"] == True:
        if u_data["password_reset"] == True:
            new_pwd = st.text_input(label="Neues Passwort eingeben")
            if st.button("Passwort zurücksetzen", key="pwd_back"):
                hashed_pwd = make_hashes(new_pwd)
                update_user(user, {"password":hashed_pwd,"passwort text":new_pwd, "password_reset":False})
                u_data = get_user(user)
                #st.write("Passwort zurückgesetzt, neu anmelden")


        if u_data["password"] == pwd and u_data["password_reset"] != True:
            st.session_state.username = u_data["username"]
            del u_data["password"]
            st.session_state["u_data"] = u_data
            switch_page("startseite")
        else:
            st.session_state.username = ''
            st.write("Falscher Benutzername oder Passwort")
    else:
        if u_data != None and u_data["password"] == pwd:
            st.write("Bitte bestätigen Sie ihre E-Mail Adresse um fortzufahren:")
            verification_code = st.number_input(label="Per Mail erhaltene Nummer eingeben",step=1,value=None,placeholder=" Nummer eingeben...")
            if u_data["verification_code"] == verification_code:
                update_user(user, {"verifikation":True, "verification_code":None})
                st.session_state.username = u_data["username"]
                st.session_state["u_data"] = u_data
                switch_page("startseite")
        else:
            st.write("Benutzername oder Passwort falsch")