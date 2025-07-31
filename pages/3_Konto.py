import streamlit as st
import db
from streamlit_extras.app_logo import add_logo 
import configuration
import time
import display
from random import randint
import openai
st.session_state.update(st.session_state)
from db import update_user, get_user


add_logo("gallery/bauchat_logo.png", height=300)

configuration.conf_session_state()
configuration.buy_coffee()


def clear_user_and_to_start_page():
    st.session_state.username = 'temp'
    st.session_state.messages = []
    #st.switch_page("Startseite.py") 

if st.session_state.username == 'temp':
    db.login()
    db.registration()
    db.forget_pwd()


else:
    st.session_state.upload_limit = 20
    name = "Benutzername:   " + st.session_state.username
    st.subheader(name)
    st.button("Abmelden", on_click=clear_user_and_to_start_page)
    #db.verification_button(st.session_state["u_data"])
           

    def openai_key_test(key):
        try:
            openai.api_key = key
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[{"role": "user", "content": "Sag hallo"}],
                max_tokens=5)
            
            st.session_state.openai_key_user = key
            update_user(st.session_state.username, {"openai_key":key})
            st.success("API-Key ist gültig!")
            
        except Exception as e:
            st.error(f"Fehler beim Testen des Keys: {e}")

    if st.session_state.openai_key_user == '':
        key = st.text_input("🔑 Dein OpenAI API-Key eingeben:")
        if st.button("Key prüfen"):
            openai_key_test(key)
    else:
        st.write("🔑 Dein OpenAI API-Key:(", st.session_state.openai_key_user,")")
        st.write("-->",st.session_state.u_data["openai_key"])

    if st.session_state.openai_key_user == '':
        st.subheader("Nutzung")
        #with st.expander("Verfügbare Einheiten"):
        if st.session_state.token_change == True:
            st.session_state.token_change = False

        date = time.strftime("%Y-%m")
        try:
            token_month = st.session_state["u_data"]["token_month"][date]
            #bytes_month = st.session_state["u_data"]["bytes_month"][date]
        except:
            token_month = 0
            #bytes_month = 0

        token_verfügbar1 = 1-(token_month/st.session_state["u_data"]["token_available"])
        if token_verfügbar1 < 0:
            st.session_state.chat_limit_reached = True
        token_verfügbar2 = st.session_state["u_data"]["token_available"] - token_month
        #bytes_verfügbar1 = 1-(bytes_month/st.session_state["u_data"]["bytes_available"]) #1 byte is equal to 0.000001 megabytes
        #bytes_verfügbar2 = (st.session_state["u_data"]["bytes_available"] - bytes_month) / 1000000

        st.progress(value= token_verfügbar1,text= "Verfügbare Token diesen Monat: " + str(token_verfügbar2) + " Tokens")
        #st.progress(value= bytes_verfügbar1,text= "Verfügbare MB diesen Monat: " + str(round(bytes_verfügbar2,1)) + " MB")

    st.subheader("Sammlungsübersicht")
    with st.expander("Sammlungen"):
        try:
            db.load_data_user()
            for collection in st.session_state["u_folders"]["collections"]:
                #tags =  " | ".join(collection["tags"])
                st.write(collection["collection"].upper()) #, "      Tags: ",tags
                st.dataframe(collection["filenames"],
                            use_container_width = True,
                            column_order=("titel","num_pages","up_date"),
                            column_config={"titel": "Titel",
                                            "num_pages": "Seitenzahl",
                                            "up_date": "Hochgeladen am"
                                            },
                            hide_index=True,
                            )
        except:
            st.write("Noch keine Eigene Sammlung")
            
    st.subheader("Chatverlauf")
    if st.session_state["u_data"]["history"] != []:
        display.chat_display(st.session_state["u_data"]["history"])


