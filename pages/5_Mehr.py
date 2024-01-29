import streamlit as st
from streamlit_extras.app_logo import add_logo 
import configuration


st.session_state.update(st.session_state)



add_logo("gallery/bauchat_logo.png", height=200)

configuration.conf_session_state()

col1, col2 = st.columns(2)
with col1:
        about_markdown = configuration.read_markdown_file("text/about.md")
        st.markdown(about_markdown, unsafe_allow_html=True)

        agb_markdown = configuration.read_markdown_file("text/agb.md")
        st.markdown(agb_markdown, unsafe_allow_html=True)