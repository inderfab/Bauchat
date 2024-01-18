import streamlit as st
from streamlit_extras.app_logo import add_logo 

import configuration

import db
st.session_state.update(st.session_state)

add_logo("gallery/bauchat_logo.png", height=100)
configuration.conf_session_state()




if st.session_state["preload_data_loaded"] == False:
    db.load_data_preloaded()

keys = ["baugesetz", "normen", "richtlinien", "produkte"]
for key in keys:
    with st.expander(label=key.upper()):
        for collection in st.session_state[key]["collections"]:
            try:
                tags =  " | ".join(collection["tags"])
            except:
                tags = ""
            st.write(collection["collection"].upper(), "      Tags: ",tags)
            st.dataframe(collection["filenames"],
                        use_container_width = True,
                        column_order=("titel","sprache","num_pages","link","herausgabedatum","up_date"),
                        column_config={"titel": "Titel",
                                        "sprache": "Sprache",
                                        "num_pages": "Seitenzahl",
                                        "link": "Link",
                                        "herausgabedatum": "Herausgabedatum",
                                        "up_date": "Hochgeladen am"
                                        },
                        hide_index=True,
                        )

        