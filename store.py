import os
from st_files_connection import FilesConnection
import streamlit as st
import dotenv
dotenv.load_dotenv()
import os
import io
import datetime
import pickle
import db
import random
import ai
import uuid
import boto3
from streamlit_extras.no_default_selectbox import selectbox
import funcy



st.session_state.update(st.session_state)

try:
    AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
    AWS_DEFAULT_REGION = os.getenv("AWS_DEFAULT_REGION")
    AWS_BUCKET_NAME = os.getenv("AWS_BUCKET_NAME")
except:
    dotenv.load_dotenv()
    AWS_ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY")
    AWS_DEFAULT_REGION = os.environ.get("AWS_DEFAULT_REGION")
    AWS_BUCKET_NAME = os.environ.get("AWS_BUCKET_NAME")


#@st.cache_data(ttl=3600)
def load_data_temp():
    if st.session_state["u_folders"] == None: 
        
        timenow = datetime.datetime.now()
        timenow = timenow.strftime("%y-%m-%d_%H-%M-%S")

        st.session_state["u_folders"] = timenow


# ----- S3 Storage
def s3_boto_client():
    return boto3.client("s3")


def s3_uploader(filepath, file):
    # Binary Mode File
    client = s3_boto_client()
    bucket = "bauchatstorage"
    success = client.upload_fileobj(io.BytesIO(file), bucket,filepath)
    return success


def s3_reader(filepath):
    conn = st.experimental_connection('s3', type=FilesConnection)
    file = conn.open("bauchatstorage/"+filepath,mode="rb")
    return file


def s3_upload_pkl(key, data):
    
    data_pkl = pickle.dumps(data)
    success = s3_uploader(key, data_pkl)

    return success


def s3_download_pkl(key): 
    client = s3_boto_client()
    bucket = "bauchatstorage"
    
    file = client.get_object(Bucket=bucket,Key=key)
    file = file['Body'].read()
    file = pickle.loads(file)
    return file


def read_s3_contents_with_buffer(key) -> str :
    client = s3_boto_client()
    bucket = "bauchatstorage"
    bytes = io.BytesIO()
    client.download_fileobj(bucket, key, bytes)
    return bytes.getvalue()


#@st.cache_data(ttl=0.1, show_spinner = False)
def s3_download_files(path) :
    client = s3_boto_client()
    bucket = "bauchatstorage"
    path = os.path.join(path,"docs/")
    #st.write('path: ',path)
    response=client.list_objects_v2(Bucket=bucket,Prefix  = path)['Contents']
    #st.write('response:',response)
    files = []
    for f in response:
        key = f["Key"]
        if key.endswith(".pkl"):
            file = client.get_object(Bucket=bucket,Key=key)
            file = file['Body'].read()
            file = pickle.loads(file)
            files.append(file)
    return files


def s3_get_files(path) :
    client = s3_boto_client()
    bucket = "bauchatstorage"
    response = client.list_objects_v2(Bucket = bucket, Delimiter='/',Prefix =path)
    st.write("s3_get_ ",response)

    files = []
    for file in response:
        subpath = os.path.join(path,file)
        
        if os.path.isfile(subpath):
            file_name = subpath.split("/")[-1]
            files.append(file_name) 
    return files


def download_button_full_pdf(key):   
    keynr = random.randint(100000,999999)
    #Key ist save_loc
    key += "-full.pdf" 
    if st.button(label="Ganzes PDF herunterladen", key=keynr):
        with st.spinner("Das PDF wird vom Server geladen"):
            pdf = s3_download_pkl(key)
        st.download_button(
            label="PDF speichern",
            data=pdf,
            file_name=key,
            mime="application/octet-stream",
            help="Lade das gesamte PDF herunter", 
            use_container_width=False,
            )


def uploader():
    return st.file_uploader(label="Laden sie ihr PDF hoch oder suchen Sie in den Verzeichnissen", 
                            type='pdf',
                            accept_multiple_files=True, 
                            label_visibility="collapsed",
                            help="Ncht angemeldete Nutzer können nur 1 Dokument hochladen. Angemeldete Nutzer können bis zu 50 Dokumente gleichzeitig hochladen und in einer Sammlung speichern.")


def file_uploader_container_user(stream):
    sammlung_empty = st.empty()
    with sammlung_empty.container():
        #if stream != []:

        #st.session_state["speicher_expander"] = True
        limit = 50
        stream = stream[:limit]

        sc1, sc2 = st.columns(2)
        
        with sc1:
            collection = st.text_input("Neue Sammlung anlegen:", max_chars=25, help="maximal 30 Buchstaben", value=None)                        
            if collection is not None:
                st.session_state["collection"] = collection

        db.load_data_user(st.session_state.username)
        try:
            user_l = [n["collection"] for n in st.session_state["u_folders"]["collections"]]
            if st.session_state["u_folders"] is not None:# and st.session_state["u_data_exists"] == True:
                with sc2:
                    update_collection = st.selectbox('Sammlung aktualisieren',user_l, index=None)
                    if update_collection != None:
                            st.session_state["collection"] = update_collection
        except:
            pass
            
        if st.button("Speichern"):
            #st.session_state["u_collections"].append(st.session_state["collection"])
            ai.submit_upload(stream)
            st.session_state["submitted"] = None
            #st.session_state["empty_stream"] = True
            sammlung_empty = st.empty()
            st.session_state.reload_store = True
            st.session_state.vector_store = None
            stream = []

        st.session_state["temp_upload"] = False 
        st.session_state["Temp_Stream"] = None
        st.session_state["Temp_Stream_IMG"] = None
        st.session_state["option5value"] = False
        st.session_state.vector_store = None


def file_uploader_container_temp(stream):
    sammlung_empty = st.empty()
    with sammlung_empty.container():
        if stream != []:
            stream = stream[0]
            st.write("Das erste Dokument wurden zwischengespeichert")

            #st.write("Ihr hochgeladenes Dokument wurde zwischengespeichert, auf laden klicken um mit dem Dokument zu chatten")
            st.session_state["temp_upload"] = True 
            st.session_state["Temp_Stream"] = stream
            st.session_state["Temp_Stream_IMG"] = stream.read()
            st.session_state["option5value"] = True
            st.session_state.vector_store = None
        
        else:
            st.session_state["temp_upload"] = False 
            st.session_state["Temp_Stream"] = None
            st.session_state["Temp_Stream_IMG"] = None
            st.session_state["option5value"] = False
            st.session_state.vector_store = None



def stream_uploader():
    # Lädt die Dokumente die in den Upload Container abgelegt wurden
    # in die Ablage auf dem Server des Users 

    st.subheader("Laden sie ihre PDF-Dokumente hoch oder suchen Sie in den Verzeichnissen")

    upload_container = st.container(border=True)
    option_upload = None 
    with upload_container:
        #st.write("Eigene Dokumente hochladen")
        if st.session_state.username == 'temp':
            temp_col1,temp_col2 = st.columns([3,1])
            with temp_col1:
                stream = uploader()
                file_uploader_container_temp(stream)
            
            with temp_col2:
                zu_anmeldung = st.button("Anmelden / Registrieren", help="Anmelden um bis zu 15 Dokumente gleichzeitig hochzuladen. Sonst nur in einem eigenen Dokument gesucht werden.")
                if zu_anmeldung:
                    st.switch_page("pages/3_Konto.py")
                zu_anleitung = st.button("Anleitung", help="Kurzanleitung wie man diese Webseite benutzen kann")
                if zu_anleitung:
                    st.switch_page("pages/4_Info.py")
        else:
            stream = uploader()
            if stream != []:
                file_uploader_container_user(stream)
                option_upload = True 
            try:
                db.load_data_user()
                st.session_state["u_collections"] = [n["collection"] for n in st.session_state["u_folders"]["collections"]]
            except:
                pass
    
    return option_upload



def user_choice():

    sammlung_container = st.container(border=True)
    with sammlung_container:

        col1, col2, col3, col4, col5 = st.columns(5)
        docs_to_load = []

        #if st.session_state["preload_data_loaded"] == True:
        ### Baugesetz
        with col1:
            option_1 = st.checkbox("Baugesetz", value=False)
            if option_1 == True:
                kanton_liste = [n["collection"] for n in st.session_state["baugesetz"]["collections"]]
                kanton_titel = "Kanton und Gemeinde wählen"
                kanton_sel = selectbox(kanton_titel, kanton_liste)
                if kanton_sel is not None:
                    docs_to_load.append( os.path.join("baugesetz",kanton_sel,"") )

        ### Normen
        with col2:
            option_2 = st.checkbox("Normen", value=False)
            if option_2 == True:
                if st.session_state["u_data"] is not None:
                    if st.session_state["u_data"].get("full_access", None):
                    
                        normen_liste = [n["collection"] for n in st.session_state["normen"]["collections"]]
                        st.write("N Liste", normen_liste)
                        normen_title = "Normen wählen"
                        norm_sel = st.multiselect(normen_title, normen_liste)
                        if norm_sel != []:
                            for u_sel in norm_sel:
                                docs_to_load.append( os.path.join("normen",u_sel,"") )
                    else:
                        st.write("Normen sind aus rechtlichen Gründen zur Zeit noch nicht freigeschaltet")
                else:
                    st.write("Normen sind aus rechtlichen Gründen zur Zeit noch nicht freigeschaltet")
                    
        ### Richtlinien
        with col3:
            option_3 = st.checkbox("Richtlinien", value=False)
            if option_3 == True:
                richtlinie_liste = [n["collection"] for n in st.session_state["richtlinien"]["collections"]]
                richtlinie_title = "Richtlinien wählen"
                richtlinie_sel = st.multiselect(richtlinie_title, richtlinie_liste)

                if richtlinie_sel != []:
                    for u_sel in richtlinie_sel:
                        docs_to_load.append( os.path.join("richtlinien",u_sel,"") )

        ### Produkte
        with col4:
            option_4 = st.checkbox("Produkte", value=False)
            
            if option_4 == True:
                
                unternehmen_liste = [n["collection"] for n in st.session_state["produkte"]["collections"]]
                unternehmen_title = "Unternehmerprodukte wählen"
                unternehmen_sel = st.multiselect(unternehmen_title, unternehmen_liste)

                if unternehmen_sel != []:
                    for u_sel in unternehmen_sel:
                        docs_to_load.append( os.path.join("produkte",u_sel,"") )

        ### Benutzer
        with col5:
            if st.session_state.username != 'temp':
                sammlung_checkbox = "Eigene Sammlungen"
            else:
                sammlung_checkbox = "Hochgeladenes Dokument"

            opt_5 = st.checkbox(sammlung_checkbox,value=st.session_state["option5value"])
            if opt_5 == True and st.session_state.username != 'temp':
                
                if st.session_state["u_collections"] != []:

                    option_upload = True
                    
                    user_choice = st.multiselect('Sammlungen',st.session_state["u_collections"], default=st.session_state["user_choice_default"])
                    if user_choice != []:
                        for c in user_choice:
                            docs_to_load.append(f"{st.session_state.username}/{c}/")

            if opt_5 == True and st.session_state.username == 'temp' and st.session_state["Temp_Stream"]:
                option_upload = True


            
        if any([option_1,option_2,option_3,option_4,option_upload]) or st.session_state["temp_upload"] == True:
            st.session_state.show_chat = True
        else:
            show_chat=False

    return show_chat, docs_to_load


def load_merge_store(docs_to_load):
    st.session_state["docs_to_load"] = docs_to_load
    stores = ai.load_store(docs_to_load)

    if st.session_state["temp_upload"] == True:
        temp_store = ai.store_temp(st.session_state["Temp_Stream"])
        if temp_store is not None:
            stores.append(temp_store)

    store_list = funcy.lflatten(stores)
    
    if len(store_list)>1:
        st.session_state.vector_store = ai.merge_faiss_stores(store_list)
    else:
        st.session_state.vector_store = store_list[0]
    
