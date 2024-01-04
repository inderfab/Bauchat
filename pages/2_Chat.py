import streamlit as st

from streamlit_extras.switch_page_button import switch_page
from streamlit_extras.app_logo import add_logo 


import ai
import display
import configuration
import db

VectorStore = None

add_logo("gallery/bauchat_logo.png", height=100)

configuration.conf_session_state()

#titel_text = "BauCHAT"
#if st.session_state.username != 'temp':
#    titel_text += ' im Gespräch mit ' + st.session_state.username
#st.subheader(titel_text)


if st.session_state.docs_to_load != [] or st.session_state["temp_upload"] == True:

    if st.session_state.docs_to_load != []:
        with st.sidebar:
            chat_docs = ''
            for i in st.session_state["docs_to_load"]:
                chat_docs += "- " + i.split("/")[-2] + "\n"
            st.write("Geladene Dokumente:")
            st.markdown(chat_docs)
        
    if st.session_state.username != "temp":
        with st.spinner("Dokumente laden"):
            VectorStore = ai.load_Store(st.session_state["docs_to_load"])
        
    if st.session_state["temp_upload"] == True:
        Vectorstore_Temp = ai.store_temp(st.session_state["Temp_Stream"])
        #if VectorStore != None:
        #    VectorStore = ai.combine_Stores([VectorStore,Vectorstore_Temp])
        #else:
        #    VectorStore = Vectorstore_Temp$
        VectorStore = Vectorstore_Temp

    if st.checkbox(label="Ausführliche Antwort", value=False):
            st.session_state.long_answer = True

    query = st.chat_input("Stellen Sie hier Ihre Frage")

    if query:
        message = ai.bauchat_query(query, VectorStore,k=4)
        db.user_update_message_and_tokens(message)

    else:
        st.write("Stellen Sie eine Frage an die Dokumente")

    if st.session_state.messages != []:
        display.chat_display(st.session_state.messages)

else:
    st.write("Bitte wählen Sie eine Sammlung oder laden Sie eigene Dokumente hoch")


