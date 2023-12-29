import streamlit as st
import login
from streamlit_extras.switch_page_button import switch_page
from streamlit_extras.app_logo import add_logo 
import configuration
import time

add_logo("gallery/bauchat_logo.png", height=100)

configuration.conf_session_state()

if st.session_state.username == 'temp':
    login.login()
    login.registration()
    login.forget_pwd()

else:
    st.write("Benutzername: ", st.session_state.username )
    date = time.strftime("%Y-%m")
    
    if st.session_state.token_change == True:
        st.session_state["u_data"] = login.get_user(st.session_state.username)
    
    try:
        token_month = st.session_state["u_data"]["token_month"][date]
    except:
        token_month = 0
    token_verfügbar1 = 1-(token_month/st.session_state["u_data"]["token_available"])
    token_verfügbar2 = st.session_state["u_data"]["token_available"] -token_month


    st.progress(value= token_verfügbar1,text= "Verfügbare Token diesen Monat: " + str(token_verfügbar2))
    
    if st.session_state["u_data"]["history"] != []:
        with st.expander(label="Verlauf",expanded=True):
            for message in st.session_state["u_data"]["history"]:
                with st.chat_message(message[0]["role"]):
                    st.markdown(message[0]["content"] + " (" + message[0]["date"] +")")
                with st.chat_message(message[1]["role"]):
                    st.markdown(message[1]["content"])


