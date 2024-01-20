import streamlit as st
from streamlit_extras.app_logo import add_logo 
import configuration

st.session_state.update(st.session_state)

add_logo("gallery/bauchat_logo.png", height=200)

configuration.conf_session_state()

st.subheader("Anleitung")
