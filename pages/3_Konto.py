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
    
    with st.expander("Verfügbare Einheiten"):
        if st.session_state.token_change == True:
            st.session_state["u_data"] = db.get_user(st.session_state.username)
            st.session_state.token_change = False

        date = time.strftime("%Y-%m")
        try:
            token_month = st.session_state["u_data"]["token_month"][date]
            bytes_month = st.session_state["u_data"]["bytes_month"][date]
        except:
            token_month = 0
            bytes_month = 0

        token_verfügbar1 = 1-(token_month/st.session_state["u_data"]["token_available"])
        token_verfügbar2 = st.session_state["u_data"]["token_available"] - token_month
        bytes_verfügbar1 = 1-(bytes_month/st.session_state["u_data"]["bytes_available"]) #1 byte is equal to 0.000001 megabytes
        bytes_verfügbar2 = (st.session_state["u_data"]["bytes_available"] - bytes_month) / 1000000

        st.progress(value= token_verfügbar1,text= "Verfügbare Token diesen Monat: " + str(token_verfügbar2) + " Tokens")
        st.progress(value= bytes_verfügbar1,text= "Verfügbare MB diesen Monat: " + str(round(bytes_verfügbar2,1)) + " MB")

    with st.expander("Sammlungen"):
        if st.session_state["u_folders"] == None:
            db.load_data_user()


        for collection in st.session_state["u_folders"]["collections"]:
            tags =  " | ".join(collection["tags"])
            st.write(collection["collection"].upper(), "      Tags: ",tags)
            st.dataframe(collection["filenames"],
                        use_container_width = True,
                        column_order=("titel","num_pages","up_date"),
                        column_config={"titel": "Titel",
                                        "num_pages": "Seitenzahl",
                                        "up_date": "Hochgeladen am"
                                        },
                        hide_index=True,
                        )
            
    with st.expander("Chatverlauf"):
        if st.session_state["u_data"]["history"] != []:
            display.chat_display(st.session_state["u_data"]["history"])


