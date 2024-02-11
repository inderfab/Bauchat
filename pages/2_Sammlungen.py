import streamlit as st
from streamlit_extras.app_logo import add_logo 

import configuration

import db
st.session_state.update(st.session_state)

add_logo("gallery/bauchat_logo.png", height=200)
configuration.conf_session_state()


if st.session_state["preload_data_loaded"] == False:
    db.load_data_preloaded()

st.write("Übersicht der Dokumente in den Sammlungen")
keys = ["baugesetz", "normen", "richtlinien", "produkte"]
for key in keys:
    with st.expander(label=key.upper()):
        for collection in st.session_state[key]["collections"]:
            tags =  " | ".join(collection.get("tags",""))
                               
            st.write(collection["collection"].upper(), "      Tags: ",tags)
            st.dataframe(collection["filenames"],
                        use_container_width = True,
                        column_order=("name","link","herausgabedatum","titel","sprache","num_pages","up_date"),
                        column_config={"name": "Titel",
                                       "titel": "Dokumentenname",
                                        "sprache": "Sprache",
                                        "num_pages": "Seitenzahl",
                                        "link": st.column_config.LinkColumn("Link", display_text="Link zur Quelle"),
                                        "herausgabedatum": "Herausgabedatum",
                                        "up_date": "Hochgeladen am"
                                        },
                        hide_index=True,
                        )

        