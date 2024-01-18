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

import dotenv
dotenv.load_dotenv()
st.session_state.update(st.session_state)

page_title = "bauCHAT"


st.set_page_config(page_title = page_title,layout="wide") #

configuration.conf_session_state()
configuration.conf_menu()
add_logo("gallery/bauchat_logo.png", height=100)

if st.session_state["preload_data_loaded"] == False:
    db.load_data_preloaded()

if st.session_state.username != "Temp": 
    db.load_data_user(st.session_state.username)

st.session_state["data_user"] = None


st.subheader("Laden sie ihre PDF-Dokumente hoch oder suchen Sie in den Verzeichnissen")


if st.session_state.username == 'temp':
    up_col1, up_col2 = st.columns([1,4])
    with up_col1:
        zu_anmeldung = st.button("Anmelden / Registrieren")
    with up_col2:
        st.write("Anmelden um bis zu 15 Dokumente gleichzeitig hochzuladen. Sonst nur in einem eigenen Dokument gesucht werden.")

    if zu_anmeldung:
        st.switch_page("pages/3_Konto.py")

stream = st.file_uploader(label="Laden sie ihr PDF hoch oder suchen Sie in den Verzeichnissen", type='pdf',accept_multiple_files=True, label_visibility="hidden")

if st.session_state.username != 'temp' and len(stream) > 15:
    stream = stream[:15]
    st.write("Die erste 15 Dokumente wurden zwischengespeichert")
elif st.session_state.username == 'temp' and len(stream) >= 1:
    stream = stream[0]
    #st.write("Das erste Dokument wurden zwischengespeichert")


if stream != []:
    st.session_state["speicher_expander"] = True
    #st.session_state["loader_state"] = False
    
    if st.session_state.username != 'temp':
        with st.expander("Sammlung erstellen", expanded=st.session_state["speicher_expander"]):
            with st.form(key="Update Collections"):
                sc1, sc2 = st.columns(2)
                
                with sc1:
                    collection = st.text_input("Neue Sammlung anlegen:", max_chars=25, help="maximal 25 Buchstaben", value=None)                        
                    if collection is not None:
                        st.session_state["collection"] = collection

                st.session_state["u_folders"] = db.collections_data_db(st.session_state.username)

                if st.session_state["u_folders"] is not None:# and st.session_state["u_data_exists"] == True:
                    with sc2:
                        update_collection = st.selectbox('Sammlung aktualisieren',[n["collection"] for n in st.session_state["u_folders"]["collections"]], index=None)
                        if update_collection is not None:
                                st.session_state["collection"] = update_collection
                
                st.session_state["submitted"] = st.form_submit_button("Speichern")
            
            
            if st.session_state["submitted"] is not None:
                ai.submit_upload(stream)
                st.session_state["submitted"] = None
                

    else:
        collection = None
        st.write("Ihr hochgeladenes Dokument wurde zwischengespeichert, auf laden klicken um mit dem dokument zu chatten")
        st.session_state["temp_upload"] = True 
        st.session_state["Temp_Stream"] = stream
        st.session_state["Temp_Stream_IMG"] = stream.read()
        st.session_state["option5value"] = True
            

st.write("Alle angewählten Verzeichnisse werden gleichzeitig durchsucht. Wählen Sie die Gewünschten und klicken Sie auf laden.")


col1, col2, col3, col4, col5 = st.columns(5)
docs_to_load = []



if st.session_state["preload_data_loaded"] == True:
    with col1:
        option_1 = st.checkbox("Baugesetz", value=False)
        if option_1 == True:
            kanton_liste = [n["collection"] for n in st.session_state["baugesetz"]["collections"]]
            kanton_titel = "Kanton und Gemeinde wählen"
            kanton_sel = selectbox(kanton_titel, kanton_liste)
            if kanton_sel is not None:
                docs_to_load.append( os.path.join("baugesetz",kanton_sel,"") )

    with col2:
        option_2 = st.checkbox("Normen", value=False)
        if option_2 == True:
            if st.session_state["u_data"] is not None:
                if st.session_state["u_data"].get("full_access", None):
                
                    normen_liste = [n["collection"] for n in st.session_state["normen"]["collections"]]
                    normen_title = "Normen wählen"
                    norm_sel = st.multiselect(normen_title, normen_liste)
                    if norm_sel != []:
                        for u_sel in norm_sel:
                            docs_to_load.append( os.path.join("normen",u_sel,"") )
                else:
                    st.write("Normen sind aus rechtlichen Gründen zur Zeit noch nicht freigeschaltet")
            else:
                st.write("Normen sind aus rechtlichen Gründen zur Zeit noch nicht freigeschaltet")
                

    with col3:
        option_3 = st.checkbox("Richtlinien", value=False)
        if option_3 == True:
            richtlinie_liste = [n["collection"] for n in st.session_state["richtlinien"]["collections"]]
            richtlinie_title = "Richtlinien wählen"
            richtlinie_sel = st.multiselect(richtlinie_title, richtlinie_liste)

            if richtlinie_sel != []:
                for u_sel in richtlinie_sel:
                    docs_to_load.append( os.path.join("richtlinien",u_sel,"") )

    with col4:
        option_4 = st.checkbox("Produkte", value=False)
        
        if option_4 == True:
            
            unternehmen_liste = [n["collection"] for n in st.session_state["produkte"]["collections"]]
            unternehmen_title = "Unternehmerprodukte wählen"
            unternehmen_sel = st.multiselect(unternehmen_title, unternehmen_liste)

            if unternehmen_sel != []:
                for u_sel in unternehmen_sel:
                    docs_to_load.append( os.path.join("produkte",u_sel,"") )


with col5:
    if st.session_state.username != 'temp':
        sammlung_checkbox = "Eigene Sammlungen"
    else:
        sammlung_checkbox = "Hochgeladenes Dokument"
    option_5 = None 

    opt_5 = st.checkbox(sammlung_checkbox,value=st.session_state["option5value"])
    if opt_5 == True and st.session_state.username != 'temp':
        db.load_data_user( st.session_state.username )
        if st.session_state["u_folders"] is not None:
            option_5 = True

            user_liste = [n["collection"] for n in st.session_state["u_folders"]["collections"]]

            user_choice = st.multiselect('Sammlungen',user_liste, default=st.session_state["user_choice_default"])
            if user_choice != []:
                for c in user_choice:
                    docs_to_load.append(f"{st.session_state['u_path']}/{c}/")

    if opt_5 == True and st.session_state.username == 'temp' and stream:
        option_5 = True


if st.button("Verzeichnisse jetzt laden",type="primary"):      
    if any([option_1,option_2,option_3,option_4,option_5]) or st.session_state["temp_upload"] == True:
        st.session_state["docs_to_load"] = docs_to_load
        st.switch_page("pages/1_Chat.py")
    else:
        st.write("Verzeichnisse wählen")

