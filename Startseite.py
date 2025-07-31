import streamlit as st
import store
import configuration
import store
from streamlit_extras.app_logo import add_logo 
import db
import dotenv


dotenv.load_dotenv()
st.session_state.update(st.session_state)
st.set_page_config(page_title =  "bauCHAT",layout="wide") #
configuration.conf_session_state()
configuration.conf_menu()
configuration.buy_coffee()

add_logo("gallery/bauchat_logo.png", height=300)

if st.session_state["preload_data_loaded"] != True:
    db.load_data_preloaded()

#Main
if st.session_state.chat_limit_reached == True:
    db.token_limit_error(True)
else:
    store.stream_uploader()
    store.chat(store.user_choice() )



