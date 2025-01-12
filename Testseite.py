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

import dotenv
dotenv.load_dotenv()
st.session_state.update(st.session_state)

configuration.conf_session_state()
configuration.conf_menu()


paths = ['adigross/ZEGE_Protokolle_BK/']
stores = ai.load_store(paths)
store_list = funcy.lflatten(stores)
if len(store_list)>1:
    vector_store = ai.merge_faiss_stores(store_list)
else:
    vector_store = store_list[0]

query = 'Was steht da drin'
st.write('Query: ',query)

message = ai.bauchat_query(query,vector_store)
st.write(message)