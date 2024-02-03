import streamlit as st
import ai
import display as d
import store
import configuration

import store
from streamlit_extras.no_default_selectbox import selectbox
from streamlit_extras.app_logo import add_logo 
import db
import os
#from random import randint
import funcy
import display

import dotenv
dotenv.load_dotenv()
st.session_state.update(st.session_state)

page_title = "bauCHAT"

st.set_page_config(page_title = page_title,layout="wide") #

configuration.conf_session_state()
configuration.conf_menu()

add_logo("gallery/bauchat_logo.png", height=200)

db.load_data_preloaded()

st.subheader("Laden sie ihre PDF-Dokumente hoch oder suchen Sie in den Verzeichnissen")

cont = st.container()

if st.session_state.username == 'temp':
    zu_anmeldung = st.button("Anmelden / Registrieren", 
                                 help="Anmelden um bis zu 15 Dokumente gleichzeitig hochzuladen. Sonst nur in einem eigenen Dokument gesucht werden.")
    if zu_anmeldung:
        st.switch_page("pages/3_Konto.py")

else:
    db.load_data_user()
    st.session_state["u_collections"] = [n["collection"] for n in st.session_state["u_folders"]["collections"]]

upload_container = st.container(border=True)
with upload_container:
    stream = store.uploader()
    stream = store.file_uploader_container(stream)

#st.write("Alle angewählten Verzeichnisse werden gleichzeitig durchsucht. Wählen Sie die Gewünschten und klicken Sie auf laden.")

sammlung_container = st.container(border=True)
with sammlung_container:
    col1, col2, col3, col4, col5 = st.columns(5)
    docs_to_load = []



    if st.session_state["preload_data_loaded"] == True:
        with col1:
            option_1 = st.checkbox("Baugesetz", value=False)
            if option_1 == True:
                kanton_liste = [n["collection"] for n in st.session_state["baugesetz"]["collections"]]
                kanton_titel = "Kanton und Gemeinde wählen"
                kanton_sel = selectbox(kanton_titel, kanton_liste)
                if kanton_sel is not None:
                    docs_to_load.append( os.path.join("baugesetz",kanton_sel,"") )

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
                    

        with col3:
            option_3 = st.checkbox("Richtlinien", value=False)
            if option_3 == True:
                richtlinie_liste = [n["collection"] for n in st.session_state["richtlinien"]["collections"]]
                richtlinie_title = "Richtlinien wählen"
                richtlinie_sel = st.multiselect(richtlinie_title, richtlinie_liste)

                if richtlinie_sel != []:
                    for u_sel in richtlinie_sel:
                        docs_to_load.append( os.path.join("richtlinien",u_sel,"") )

        with col4:
            option_4 = st.checkbox("Produkte", value=False)
            
            if option_4 == True:
                
                unternehmen_liste = [n["collection"] for n in st.session_state["produkte"]["collections"]]
                unternehmen_title = "Unternehmerprodukte wählen"
                unternehmen_sel = st.multiselect(unternehmen_title, unternehmen_liste)

                if unternehmen_sel != []:
                    for u_sel in unternehmen_sel:
                        docs_to_load.append( os.path.join("produkte",u_sel,"") )


    with col5:
        if st.session_state.username != 'temp':
            sammlung_checkbox = "Eigene Sammlungen"
        else:
            sammlung_checkbox = "Hochgeladenes Dokument"
        option_5 = None 

        opt_5 = st.checkbox(sammlung_checkbox,value=st.session_state["option5value"])
        if opt_5 == True and st.session_state.username != 'temp':
            
            if st.session_state["u_collections"] != []:
                #st.write("user_l", user_l, st.session_state.u_folders)

                option_5 = True
                
                user_choice = st.multiselect('Sammlungen',st.session_state["u_collections"], default=st.session_state["user_choice_default"])
                if user_choice != []:
                    for c in user_choice:
                        #st.write(st.session_state.username)
                        docs_to_load.append(f"{st.session_state.username}/{c}/")
                        #st.write(docs_to_load)

        if opt_5 == True and st.session_state.username == 'temp' and stream:
            option_5 = True


    if st.button("Verzeichnisse jetzt laden",type="primary"):      
        if any([option_1,option_2,option_3,option_4,option_5]) or st.session_state["temp_upload"] == True:
            st.session_state["docs_to_load"] = docs_to_load
        else:
            st.write("Verzeichnisse wählen")

chat_container = st.container(border=True)
with chat_container:

    VectorStore = None
    if st.session_state.docs_to_load != [] or st.session_state["temp_upload"] == True:

        if st.session_state.docs_to_load != []:
            with st.sidebar:
                chat_docs = ''
                for i in st.session_state["docs_to_load"]:
                    chat_docs += "- " + i.split("/")[-2] + "\n"
                st.write("Geladene Dokumente:")
                st.markdown(chat_docs)

        #st.write("Docs to load:" , st.session_state["docs_to_load"]) 
        stores = ai.load_Store(st.session_state["docs_to_load"])
            
        if st.session_state["temp_upload"] == True:
            temp_store = ai.store_temp(st.session_state["Temp_Stream"])
            if temp_store is not None:
                stores.append(temp_store)

        store_list = funcy.lflatten(stores)
        
        if len(store_list)>1:
            VectorStore = ai.merge_faiss_stores(store_list)
        else:
            VectorStore = store_list[0]
        
        if st.checkbox(label="Ausführliche Antwort", value=False):
            st.session_state.long_answer = True

        query = st.chat_input("Stellen Sie hier Ihre Frage")

        if query:
            with st.spinner("Die Dokumente werden durchsucht"):
                message = ai.bauchat_query(query, VectorStore)
                if st.session_state.username != 'temp':
                    db.user_update_message_and_tokens(message)

        else:
            st.write("Stellen Sie eine Frage an die Dokumente")

        if st.session_state.messages != []:
            display.chat_display(st.session_state.messages)

    else:
        st.write("Bitte wählen Sie eine Sammlung oder laden Sie eigene Dokumente hoch")


