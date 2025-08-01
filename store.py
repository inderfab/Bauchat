import os
from st_files_connection import FilesConnection
import streamlit as st
import dotenv
import os
import io
import datetime
import pickle
import db
import random
import ai
import boto3
from streamlit_extras.no_default_selectbox import selectbox
import funcy
import display as d

dotenv.load_dotenv()

st.session_state.update(st.session_state)

# Standardmodus: cloud
MODE = os.getenv("STORAGE_MODE", "cloud")
LOCAL_STORAGE_PATH = os.getenv("LOCAL_STORAGE_PATH", "./local_storage")

def use_local():
    return os.getenv("STORAGE_MODE", "local") == "local"
    

if MODE == "cloud":
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


# ----- S3 Storage und Lokal ---


def s3_boto_client():
    return boto3.client("s3")


def upload_file(filepath, file_bytes, is_pickle=False):
    if is_pickle and not filepath.endswith(".pkl"):
        filepath += ".pkl"

    if use_local():
        full_path = os.path.join(LOCAL_STORAGE_PATH, filepath)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, "wb") as f:
            f.write(file_bytes)
    
    else:
        # Binary Mode File
        client = s3_boto_client()
        client.upload_fileobj(io.BytesIO(file_bytes), AWS_BUCKET_NAME,filepath)


def upload_pickle(key, data):
    
    data_pkl = pickle.dumps(data)
    return upload_file(key, data_pkl, is_pickle = True)


def download_pickle(key):

    if use_local():
        full_path = os.path.join(LOCAL_STORAGE_PATH, key)
        with open(full_path, "rb") as f:
            return pickle.load(f)
    else:
        client = s3_boto_client()
        file = client.get_object(Bucket=AWS_BUCKET_NAME, Key=key)['Body'].read()
        return pickle.loads(file)
        
def read_contents_with_buffer(key):
    if use_local():
        full_path = os.path.join(LOCAL_STORAGE_PATH, key)
        with open(full_path, "rb") as f:
            return f.read()
    else:
        client = s3_boto_client()
        bytes_io = io.BytesIO()
        client.download_fileobj(AWS_BUCKET_NAME, key, bytes_io)
        return bytes_io.getvalue()


def download_all_pickles(path):
    files = []

    if use_local():
        doc_path = os.path.join(LOCAL_STORAGE_PATH, path, "docs")
        if not os.path.exists(doc_path):
            return []
        for file_name in os.listdir(doc_path):
            if file_name.endswith(".pkl"):
                full_path = os.path.join(doc_path, file_name)
                with open(full_path, "rb") as f:
                    files.append(pickle.load(f))
    else:
        client = s3_boto_client()
        prefix = os.path.join(path, "docs/")
        response = client.list_objects_v2(Bucket=AWS_BUCKET_NAME, Prefix=prefix).get('Contents', [])
        for f in response:
            key = f["Key"]
            if key.endswith(".pkl"):
                file = client.get_object(Bucket=AWS_BUCKET_NAME, Key=key)['Body'].read()
                files.append(pickle.loads(file))
    
    return files



# Alte Funktionen für Debug

def get_files(path):
    files = []

    if use_local():
        local_path = os.path.join(LOCAL_STORAGE_PATH, path)
        if not os.path.exists(local_path):
            return []
        for file_name in os.listdir(local_path):
            full_path = os.path.join(local_path, file_name)
            if os.path.isfile(full_path):
                files.append(file_name)
    else:
        client = s3_boto_client()
        response = client.list_objects_v2(Bucket=AWS_BUCKET_NAME, Delimiter='/', Prefix=path)
        st.write("s3_get_ ",response)

        for item in response.get("Contents", []):
            file_name = item["Key"].split("/")[-1]
            if file_name:  # nur echte Dateien, keine leeren Keys
                files.append(file_name)

    return files

def s3_reader(filepath):
   conn = st.experimental_connection('s3', type=FilesConnection)
   file = conn.open("bauchatstorage/"+filepath,mode="rb")
   return file


#-------


def download_button_full_pdf(key):   
    keynr = random.randint(100000,999999)
    #Key ist save_loc
    key += "-full.pdf" 
    if st.button(label="Ganzes PDF herunterladen", key=keynr):
        with st.spinner("Das PDF wird vom Server geladen"):
            pdf = download_pickle(key)
        st.download_button(
            label="PDF speichern",
            data=pdf,
            file_name=key,
            mime="application/octet-stream",
            help="Lade das gesamte PDF herunter", 
            use_container_width=False
            )


def uploader():
    if st.session_state.username == 'temp':
        label = "Anmelden um mehr als ein füngseitiges Dokument zu durchsuchen"
    else:
        label = "Maximal 20 Dokumente gleichzeitig hochladen und in Sammlung speichern"

    return st.file_uploader(label=label, 
                            type='pdf',
                            accept_multiple_files=True, 
                            label_visibility="visible")


def file_uploader_container_user(stream):
    sammlung_empty = st.empty()
    with sammlung_empty.container():
        #if stream != []:

        #st.session_state["speicher_expander"] = True
        limit = st.session_state.upload_limit
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
            sammlung_empty.empty()
            st.session_state.reload_store = True
            st.session_state.vector_store = None
            stream = []
            st.session_state["option5value"] = True
            st.rerun()
            
        st.session_state["temp_upload"] = False 
        st.session_state["Temp_Stream"] = None
        st.session_state["Temp_Stream_IMG"] = None
        st.session_state.vector_store = None


def file_uploader_container_temp(stream):
    sammlung_empty = st.empty()
    with sammlung_empty.container():
        if stream != []:
            if len(stream) > st.session_state.upload_limit:
                st.error(f"Dokumente: {len(stream)} / Max: {st.session_state.upload_limit} Nur das erste Dokument wurde verarbeitet, bitte anmelden")
            
            stream = stream[0]
            

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

    st.subheader("PDF hochladen oder in Verzeichnissen suchen")

    upload_container = st.container(border=True)
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
                st.session_state.option_upload = True 
            try:
                db.load_data_user()
                st.session_state["u_collections"] = [n["collection"] for n in st.session_state["u_folders"]["collections"]]
            except:
                pass
    


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

                    st.session_state.option_upload = True
                    
                    user_choice = st.multiselect('Sammlungen',st.session_state["u_collections"], default=st.session_state["user_choice_default"])
                    if user_choice != []:
                        for c in user_choice:
                            docs_to_load.append(f"{st.session_state.username}/{c}/")

            if opt_5 == True and st.session_state.username == 'temp' and st.session_state["Temp_Stream"]:
                st.session_state.option_upload = True


            
        if any([option_1,option_2,option_3,option_4]) or st.session_state["temp_upload"] == True or st.session_state.option_upload==True:
            st.session_state.show_chat = True
        else:
            st.session_state.show_chat=False

    return docs_to_load


def load_merge_store(docs_to_load):
    st.session_state["docs_to_load"] = docs_to_load
    stores = ai.load_store(docs_to_load)

    if st.session_state["temp_upload"] == True and st.session_state.username == 'temp':
        temp_store = ai.store_temp(st.session_state["Temp_Stream"])
        if temp_store is not None:
            stores.append(temp_store)

    store_list = funcy.lflatten(stores)
    
    if len(store_list)>1:
        st.session_state.vector_store = ai.merge_faiss_stores(store_list)
    else:
        st.session_state.vector_store = store_list[0]
    

def chat(docs_to_load):
    if st.session_state.show_chat == True:
        query = st.chat_input("Verzeichnisse wählen und hier die Frage stellen")
        chat_container = st.container(border=True)
       
        with chat_container:
            
            if docs_to_load != [] or st.session_state["temp_upload"] == True:

                d.show_sidebar()
                

                if query != None or st.session_state.vector_store == None or docs_to_load != st.session_state["docs_to_load"]:
                    load_merge_store(docs_to_load)
                    
                if st.checkbox(label="Ausführliche Antwort", value=False):
                    st.session_state.long_answer = True

                if query:
                    with st.spinner("Die Dokumente werden durchsucht"):
                        message = ai.bauchat_query(query, st.session_state.vector_store)
                        if st.session_state.username != 'temp':
                            db.user_update_message_and_tokens(message)

                else:
                    st.write("Stellen Sie eine Frage an die Dokumente")

                if st.session_state.messages != []:
                    d.chat_display(st.session_state.messages)

            else:
                st.write("Bitte wählen Sie eine Sammlung oder laden Sie eigene Dokumente hoch")
