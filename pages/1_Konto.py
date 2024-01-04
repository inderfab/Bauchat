import streamlit as st
import db
from streamlit_extras.switch_page_button import switch_page
from streamlit_extras.app_logo import add_logo 
import configuration
import time
import display

add_logo("gallery/bauchat_logo.png", height=100)

configuration.conf_session_state()

if st.session_state.username == 'temp':
    db.login()
    db.registration()
    db.forget_pwd()

else:
    st.write("Benutzername: ", st.session_state.username )
    date = time.strftime("%Y-%m")
    
    if st.session_state.token_change == True:
        st.session_state["u_data"] = db.get_user(st.session_state.username)
    
    try:
        token_month = st.session_state["u_data"]["token_month"][date]
    except:
        token_month = 0
    token_verfügbar1 = 1-(token_month/st.session_state["u_data"]["token_available"])
    token_verfügbar2 = st.session_state["u_data"]["token_available"] -token_month


    st.progress(value= token_verfügbar1,text= "Verfügbare Token diesen Monat: " + str(token_verfügbar2))
    
    if st.session_state["u_data"]["history"] != []:
        display.chat_display(st.session_state["u_data"]["history"])
