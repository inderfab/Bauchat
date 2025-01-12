import streamlit as st
import re
import hashlib
from deta import Deta
import dotenv
import os
import mail
from random import randint, sample
import time
import string
import store

st.session_state.update(st.session_state)

dotenv.load_dotenv()


def insert_user(user_dict):
    """Inserts the user into the bucket"""

    filepath = user_dict["username"] + '/userdata'
    file = user_dict
    store.s3_upload_pkl(filepath, file)
    print("User wurde hinzugefügt")
    return user_dict 


#@st.cache_data(ttl=0.1)
def get_user(username):
    """If not found, the function will return None"""
    try: 
        user = store.s3_download_pkl(username+'/userdata')
        print('userdaten heruntergeladen')
    except:
        user = None
        print('kein User mit dem Namen {} gefunden'.format(username))
    return user

    #TODO Userdata in Session State schreiben


def update_user(username, updates):

    filepath = username + '/userdata'
    userdata = get_user(username) #st.session_state.username
    
    for key in updates.keys():
        if key in userdata:
            userdata[key] = updates[key]

    store.s3_upload_pkl(filepath, userdata)
    print("Update wurde hochgeladen")
    
    #TODO Userdata in Session State schreiben



def user_update_message_and_tokens(updates):
    user_data = get_user(st.session_state.username)

    history = user_data["history"]
    history.insert(0,updates)
    update = {"history":history}

    token = update_user_tokens(user_data, updates["usage"]["total_tokens"] ) #{"prompt_tokens":2357"completion_tokens":121"total_tokens":2478}
    update.update(token)

    update_user(st.session_state.username,update)


def user_update_embedding_tokens(username):
    user_data = get_user(username)
    usage = st.session_state.token_usage
    st.session_state.token_usage = 0
    token = update_user_tokens(user_data, usage)
    update_user(username,token)


def update_user_tokens(user_data, token_update):
    date = time.strftime("%Y-%m")
    # wenn es schon einträge gibt
    token_month = user_data["token_month"] #verlauf pro monat
    if date in token_month:
        existing_tokens_month = token_month[date]
        existing_tokens_month += token_update
        token_month.update({date:existing_tokens_month}) #verlauf addieren
    else:
        token_month.update({date:token_update})

    token_total = user_data["token_total"] + token_update
   
    return {"token_month":token_month,"token_total":token_total}


def update_user_byte_size():
    if st.session_state["bytes_update"]!= 0:
        filesize_update = st.session_state["bytes_update"]
        user_data = get_user(st.session_state.username)
        date = time.strftime("%Y-%m")
        bytes_month = user_data["bytes_month"] #verlauf pro monat
        if date in bytes_month:
            existing_bytes_month = bytes_month[date]
            existing_bytes_month += filesize_update
            bytes_month.update({date:existing_bytes_month}) #verlauf addieren
        else:
            bytes_month.update({date:filesize_update})

        bytes_total = user_data["bytes_total"] + filesize_update

        update_user(st.session_state.username, {"bytes_month":bytes_month,"bytes_total":bytes_total})
        st.session_state["bytes_update"] = 0



# def delete_user(username):
#     """Always returns None, even if the key does not exist"""
#     return db_users.delete(username)


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
    with st.expander("Anmelden", expanded=True):
        user = st.text_input("Benutzername", key = "user_login")
        pwd = st.text_input("Passwort",type='password',key = "pwd")
        st.button("Anmelden", on_click=login_user, args=[user,pwd])  


def login_fast():
    if st.session_state.username == 'temp':
        user = "xx"
        pwd = "xx"
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
    with st.expander("Registrieren",expanded=st.session_state["registration_expandend"]):
        
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


        if st.button("Registrieren"):
            if get_user(user) != None: #Stimmt das?
                    st.write("Benutzername bereits vergeben")
                    username_free = False
            if email_filled and pwd_filled and username_free == True:
                hashed_pwd = make_hashes(pwd)
                verification_code = randint(100000,999999)
                data = {"username":user, "vorname":vorname, "nachname":nachname, "email":email, 
                        "password":hashed_pwd, "password_reset":False,
                        "verifikation":False,"verification_code":verification_code,
                        "history":[],
                        "token_month":{},"token_total":0, "token_available":100000,
                        "full_access":False, 
                        "bytes_month":{}, "bytes_total":0, "bytes_available":1000000000,
                        "pages":0, 
                        }
                
                mail.send_registration(email, verification_code)
                insert_user(data)
                insert_data(user,{'collections': []})
                st.session_state["registration_expandend"] = False
                    


def login_user(user,pwd):         
    pwd = make_hashes(pwd)
    u_data = get_user(user)
    
    if u_data != None: # and u_data["verifikation"] == True:
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
            load_data_user()
            st.switch_page("Startseite.py")
        else:
            st.session_state.username = 'temp'
            st.write("Falscher Benutzername oder Passwort")
    else:
        if u_data != None and u_data["password"] == pwd:
            st.write("Bitte bestätigen Sie ihre E-Mail Adresse um fortzufahren:")
            verification_code = st.number_input(label="Per Mail erhaltene Nummer eingeben",step=1,value=None,placeholder=" Nummer eingeben...")
            if u_data["verification_code"] == verification_code:
                update_user(user, {"verifikation":True, "verification_code":None})
                st.session_state.username = u_data["username"]
                st.session_state["u_data"] = u_data
                st.switch_page("Startseite.py")
        else:
            st.write("Benutzername oder Passwort falsch")



### Data DB

#@st.cache_data(ttl=0.1)
def get_data(username):
    """If not found, the function will return None"""
    try: 
        data = store.s3_download_pkl(username+'/collections')
        print('user data heruntergeladen')
        if isinstance(data, tuple):
            data = data[0]
    except:
        data = {"collections":[]}
        print('kein User mit dem Namen {} gefunden'.format(username))
    return data


def insert_data(username, data_dict):
    """Inserts the data into the user bucket"""

    filepath = username + '/collections'
    file = data_dict
    store.s3_upload_pkl(filepath, file)
    print("User Collections wurde hinzugefügt")
    return data_dict 

def update_data(username, updates):

    filepath = username + '/collections'
    userdata = get_data(username) #st.session_state.username
    
    for key in updates.keys():
        if key in userdata:
            userdata[key] = updates[key]

    store.s3_upload_pkl(filepath, userdata)
    print("Update Collection wurde hochgeladen")
    
    #TODO Userdata in Session State schreiben



def update_collection(metadata):
    if st.session_state.preload_active:
        key = st.session_state.preload_key
    else:
        key = st.session_state.username

    if st.session_state["metadata_preloaded"] != None:
        metadata.update(st.session_state["metadata_preloaded"])

    data = get_data(key)
    date = time.strftime("%Y-%m-%d")

    file = {"titel": metadata["title"],
                  "typ": metadata["type"],
                  "up_date": date,
                  "name": metadata.get("name",None),
                  "sprache": metadata.get("language",None),
                  "herausgabedatum": metadata.get("printdate",None),
                  "firma_id":metadata.get("firma_id",None),
                  "link":metadata.get("link",None),
                  "save_loc":metadata["save_loc"],
                  "num_pages":metadata["num_pages"], 
                  "file_size":metadata["file_size"],
                  }
    
    update = {"collection": metadata["collection"], 
             "filenames" :[file],
             "tags":metadata.get("tags")
             }

    existing_collection = False

    # if data is None:
    #     #wird als Liste in DB geschrieben
    #     return update_data(key,{"collections":[update]})
    
    # else:
    data = data["collections"]
    st.write("data: ", data)
    for col in data:
        if col["collection"] == metadata["collection"]:
            filenames = col["filenames"]
            filenames.append(file)
            col["filenames"] = filenames
            existing_collection = True
            break
    if existing_collection == True:
        return update_data(key,{"collections":data})
    else:
        data.append(update)
        return update_data(key,{"collections":data})
    
    #metadata von ai pickle store = {"collection":collection,"save_loc":save_loc,"title":title}


#@st.cache_data(ttl=0.1, show_spinner="Lädt Benutzerdaten")
def load_data_user(user=None):
    #alle 10 sek cache löschen um immer aktuell zu sein, 
    #streamlit cloud macht automatisch cache, deshalb muss man es steuern
    if user == None:
        user = st.session_state.username
    folders = get_data(user)
    st.session_state["u_folders"] = folders
    return folders


#@st.cache_data(ttl=0.1, show_spinner="Lädt vorgefertigte Sammlungen")
def load_data_preloaded():
    keys = ["baugesetz", "normen", "richtlinien", "produkte"]
    for key in keys:
        st.session_state[key] = get_data(key)
    st.session_state["preload_data_loaded"] = True


# ### Firma DB

@st.cache_data(ttl=0.1)
def get_firmas():
    """If not found, the function will return None"""
    data = store.s3_download_pkl('firma')
    print('Alle Firmen heruntergeladen')    
    return data


def insert_firma(firma_dict):
    """Inserts the data into the firma bucket"""
    firmas = get_firmas() 
    firmas[firma_dict['key']] = firma_dict
    upload_firmas(firmas)


def upload_firmas(firmas):
    filepath = 'firma'
    store.s3_upload_pkl(filepath, firmas)
    print("Firmas wurden hochgeladen")

def update_firma(firma_id, updates):

    firmas = get_firmas() 
    firma = firmas[firma_id]

    for key in updates.keys():
        firma[key] = updates[key]
    
    firmas.update({'id':firma})
    upload_firmas(firmas)
    
    #TODO Userdata in Session State schreiben

def remove_firma(firma_id):
    """Inserts the data into the firma bucket"""
    firmas = get_firmas() 
    del firmas[firma_id]
    upload_firmas(firmas)
    

#@st.cache_data(ttl=0.1, show_spinner="Lädt Firmennamen")
def fetch_all_firmas():
    firmas = get_firmas()
    firmenliste = []
    for key in firmas:
        firmenliste.append(firmas[key]['firma_name'])
    st.session_state["firmas"] = firmenliste
    print(firmenliste)
    

