import streamlit as st
import ai
import display as d
import store
import configuration

import store
from streamlit_extras.app_logo import add_logo 
import db
import os
#from random import randint

import dotenv
dotenv.load_dotenv()
st.session_state.update(st.session_state)
page_title = "bauCHAT"
st.set_page_config(page_title = page_title,layout="wide") #

configuration.conf_session_state()
configuration.conf_menu()
add_logo("gallery/bauchat_logo.png", height=300)


if st.session_state["preload_data_loaded"] != True:
    db.load_data_preloaded()


store.stream_uploader()
show_chat,docs_to_load = store.user_choice()

     
if st.session_state.show_chat == True:
    query = st.chat_input("Verzeichnisse wählen und hier die Frage stellen")
    chat_container = st.container(border=True)
    with chat_container:
        
        if docs_to_load != [] or st.session_state["temp_upload"] == True:

            d.show_sidebar()
            

            if query != None or st.session_state.vector_store == None or docs_to_load != st.session_state["docs_to_load"]:
                store.load_merge_store(docs_to_load)
                
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


