
import streamlit as st
import db

def conf_session_state():


    if 'sidebar_state' not in st.session_state:
        st.session_state.sidebar_state = 'expanded'
    if "username" not in st.session_state:
        st.session_state.username = 'temp'
    if "loader_state" not in st.session_state:
        st.session_state["loader_state"] = True
    if "speicher_expander" not in st.session_state:   
        st.session_state["speicher_expander"] = True
    if "is_expanded" not in st.session_state:
        st.session_state["is_expanded"] = True
    if "show_chat" not in st.session_state:
        st.session_state["show_chat"] = False
    if "sammlung_expanded" not in st.session_state:
        st.session_state["sammlung_expanded"] = True
    if "docs_to_load" not in st.session_state:
        st.session_state["docs_to_load"] = []
    if "zuStartseite" not in st.session_state:
        st.session_state["zuStartseite"] = False
    if "option5value" not in st.session_state:
        st.session_state["option5value"] = False
    if "user_choice_default" not in st.session_state:
        st.session_state["user_choice_default"] = None
    if "temp_upload" not in st.session_state:
        st.session_state["temp_upload"] = False   
    if "anmeldeversuch" not in st.session_state:
        st.session_state["anmeldeversuch"] = False   


    # Storage
    if "Files_Saved" not in st.session_state:
        st.session_state["Files_Saved"] = False
    if "Temp_Stream" not in st.session_state:
        st.session_state["Temp_Stream"] = None
    if "Temp_Stream_IMG" not in st.session_state:
        st.session_state["Temp_Stream_IMG"] = None
    if "submitted" not in st.session_state:
        st.session_state["submitted"] = None


    # User-Folder
    if "u_path" not in st.session_state:
        st.session_state["u_path"] = None
    if "u_folder" not in st.session_state:
        st.session_state["u_folders"] = None
    #if "u_data_exists" not in st.session_state:
    #    st.session_state["u_data_exists"] = False
    if "u_data" not in st.session_state:
        st.session_state["u_data"] = None
    if "collection" not in st.session_state:
        st.session_state["collection"] = None
    if "update_collection" not in st.session_state:
        st.session_state["update_collection"] = None
    if "preload_data_loaded" not in st.session_state:
        st.session_state["preload_data_loaded"] = False


    #Chat
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "long_answer" not in st.session_state:
            st.session_state.long_answer = False
    if "token_change" not in st.session_state:
        st.session_state.token_change = False
    if "token_usage" not in st.session_state:
        st.session_state.token_usage = 0
    if "chat_references" not in st.session_state:
        st.session_state.chat_references = None

    #db.login_fast()


def conf_menu():
    hide_streamlit_style = """
                <style>
                #MainMenu {visibility: hidden;}
                footer {visibility: hidden;}
                #GithubIcon {visibility: hidden;}
                </style>
                """
    st.markdown(hide_streamlit_style, unsafe_allow_html=True)