import streamlit as st

from streamlit_extras.app_logo import add_logo 

import funcy
import ai
import display
import configuration
import db
import faiss

st.session_state.update(st.session_state)
VectorStore = None

add_logo("gallery/bauchat_logo.png", height=200)

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


