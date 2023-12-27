import streamlit as st

from streamlit_extras.switch_page_button import switch_page
from streamlit_extras.app_logo import add_logo 


import ai
import display
import configuration
import login

VectorStore = None

add_logo("gallery/bauchat_logo.png", height=100)

configuration.conf_session_state()

#titel_text = "BauCHAT"
#if st.session_state.username != '':
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
        

        with st.spinner("Dokumente laden"):
            VectorStore = ai.load_Store(st.session_state["docs_to_load"])
        
    if st.session_state["temp_upload"] == True:
        Vectorstore_Temp = ai.store_temp(st.session_state["Temp_Stream"])
        if VectorStore != None:
            VectorStore = ai.combine_Stores([VectorStore,Vectorstore_Temp])
        else:
            VectorStore = Vectorstore_Temp

    query = st.chat_input("Stellen Sie hier Ihre Frage")
    k = 4

    chat_col, pdf_col = st.tabs(["Mit den Dokumenten chatten", "Quellen anzeigen"])
    with chat_col:
        #st.subheader("Stelle Sie ihre Frage an die Dokumente:")
        
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        
        if query:
            message, usage, references = ai.bauchat_query(query, VectorStore,k=4)
            st.session_state.chat_references = references
            login.user_update_message_and_tokens(st.session_state.username, message, usage)
            

    with pdf_col:
        if st.session_state.chat_references != None:
            display.pdf2jpg_from_s3(st.session_state.chat_references, k=k)
        else:
            st.write("Stellen Sie eine Frage an die Dokumente")

else:
    st.write("Bitte wählen Sie eine Sammlung oder laden Sie eigene Dokumente hoch")


