import streamlit as st
from streamlit_extras.app_logo import add_logo 
import configuration


add_logo("gallery/bauchat_logo.png", height=100)

configuration.conf_session_state()

st.subheader("Anleitung")
