import streamlit as st
import ai
import display as d
import store
import configuration

import store
from streamlit_extras.no_default_selectbox import selectbox
from streamlit_extras.app_logo import add_logo 
import db
import ai
import os

import dotenv
dotenv.load_dotenv()
st.session_state.update(st.session_state)


page_title = "Preloader"


if "u_path" not in st.session_state:
        st.session_state["u_path"] = None
if "u_folder" not in st.session_state:
    st.session_state["u_folders"] = None
if "metadata_preloaded" not in st.session_state:
    st.session_state["metadata_preloaded"] = None
if "Files_Saved" not in st.session_state:
    st.session_state["Files_Saved"] = False
if "collection" not in st.session_state:
    st.session_state["collection"] = None
if "update_collection" not in st.session_state:
    st.session_state["update_collection"] = None
if "preload_key" not in st.session_state:
    st.session_state["preload_key"] = None
if "preload_active" not in st.session_state:
    st.session_state["preload_active"] = True
st.session_state["bytes_update"] = 0
if "exctraction_problem_files" not in st.session_state:
    st.session_state["exctraction_problem_files"] = []
if "submitted" not in st.session_state:
    st.session_state["submitted"] = False
        
keys = ["baugesetz", "normen", "richtlinien", "produkte"]


key = st.selectbox("key wählen", keys)
st.session_state["preload_key"] = key
st.session_state["username"] = key


stream = st.file_uploader(label="Laden sie ihr PDF hoch oder suchen Sie in den Verzeichnissen", type='pdf',accept_multiple_files=True, label_visibility="hidden")

st.session_state["firmas"] = db.fetch_all_firmas()

c1,c2 = st.columns(2)
with c1:
    name = st.text_input("Name")
    sprache = st.text_input("Sprache")
    herausgabedatum = st.text_input("Herausgabedatum")
    st.write("Seite neu laden nach dem einfügen von neuen Firmen")
    firma_id = st.selectbox(label="Firma wählen",options=[f["firma_name"]+" | "+f["key"] for f in st.session_state["firmas"]], index=None)
    if firma_id is not None:
        firma_id = firma_id.split(" | ")[1]
    link = st.text_input("link")
    tags = st.text_input("tags")

    st.session_state["metadata_preloaded"] = {"name":name,
                                              "language":sprache,
                                              "printdate":herausgabedatum,
                                              "firma_id":firma_id,
                                              "link":link,
                                              "tags":[t.strip()for t in tags.split(",")]
                                              }

with c2:
    firma_name = st.text_input("Firma Namen")
    firma_strasse = st.text_input("Firma Strasse")
    firma_plz = st.text_input("Firma PLZ")
    firma_ort = st.text_input("Firma Ort")
    firma_tel = st.text_input("Firma Tel")
    firma = {"firma_name":firma_name,"strasse":firma_strasse,"plz":firma_plz,"ort":firma_ort,"firma_tel":firma_tel}
    c_name= st.text_input("Kontakt Name")
    c_email = st.text_input("Kontakt Mail")
    c_tel = st.text_input("Kontakt Telefon")
    contact = {"contact_name:":c_name,"contact_email":c_email,"contact_tel":c_tel}
    firma.update(contact)

    if st.button("Firma speichern"):
        st.write(db.insert_firma(firma))
        st.session_state["firmas"] = db.fetch_all_firmas()



if stream != []:
    st.session_state["Files_Saved"] == False
    st.write("Key: ",st.session_state["preload_key"])
    db.load_data_user(st.session_state["preload_key"])

    st.session_state["speicher_expander"] = True
    
    with st.expander("Sammlung erstellen", expanded=True):
            
        sc1, sc2 = st.columns(2)
        
        with sc1:
            collection = st.text_input("Neue Sammlung anlegen:", max_chars=30, help="maximal 25 Buchstaben", value=None)                        
            if collection is not None:
                st.session_state["collection"] = collection

        with sc2:
            update_collection = st.selectbox('Sammlung aktualisieren',[n["collection"] for n in st.session_state["u_folders"]["collections"]], index=None)
            if update_collection is not None:
                st.session_state["collection"] = update_collection
        
        if st.button(label="Dokument speichern"):
            ai.submit_upload(stream)
            #st.form_submit_button("Speichern", on_click=ai.submit_upload, args=[stream])


with st.container():
    db.load_data_preloaded()
    key2 = st.session_state["preload_key"]
    with st.expander(label=key2.upper()):
        
        edited_data = []
        for collection in st.session_state[key2]["collections"]:
            st.write(collection["collection"].upper())
            
            tag = [] 
            tags = collection.get("tags", []) 
            tag_updater = st.experimental_data_editor(tags, num_rows="dynamic")
            
            df = collection["filenames"]
            new_df = []
            for entry in df:
                if entry.get("name") is None:
                    entry.update({"name":"---"})
                new_df.append(entry)
            
            edited_df = st.experimental_data_editor(new_df,
                        use_container_width = True,
                        column_order=("titel","name","herausgabedatum","link","sprache","num_pages","up_date"),
                        column_config={"name":"Name",
                                       "titel": "Titel",
                                       "herausgabedatum": "Herausgabedatum",
                                       "link": "Link",
                                       "sprache": "Sprache",
                                       "num_pages": "Seitenzahl",
                                       "up_date": "Hochgeladen am"
                                       },
                        hide_index=True,
                        )
        
            updated_collection = {"collection":collection["collection"],
                                  "filenames": edited_df,
                                  "tags":tag_updater
                                  }
            edited_data.append(updated_collection)

        if st.button("Speichern von "+ key2):
            update = db.db_data.put({"collections" : edited_data}, key=key2)
