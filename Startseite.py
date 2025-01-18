import streamlit as st
import ai
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
docs_to_load = store.user_choice()
store.chat(docs_to_load)


