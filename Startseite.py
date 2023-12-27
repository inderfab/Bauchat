import streamlit as st
import ai
import display as d
import store
import configuration

import store
from streamlit_extras.no_default_selectbox import selectbox
from streamlit_extras.switch_page_button import switch_page
from streamlit_extras.app_logo import add_logo 

import dotenv
dotenv.load_dotenv()


page_title = "bauCHAT"

configuration.conf_session_state()

st.set_page_config(page_title = page_title,initial_sidebar_state=st.session_state.sidebar_state,layout="wide") #

# titel_text = "BauCHAT"
# if st.session_state.username != '':
#     titel_text += ' im Gespräch mit ' + st.session_state.username
# st.subheader(titel_text)

add_logo("gallery/bauchat_logo.png", height=100)
# ---- LOADER ----


st.subheader("Laden sie ihre PDF-Dokumente hoch oder suchen Sie in den Verzeichnissen")
#st.write("---")


stream = st.file_uploader(label="Laden sie ihr PDF hoch oder suchen Sie in den Verzeichnissen", type='pdf',accept_multiple_files=True, label_visibility="hidden")
if st.session_state.username == '':
    up_col1, up_col2 = st.columns([1,4])
    with up_col1:
        zu_anmeldung = st.button("Anmelden / Registrieren")
    with up_col2:
        st.write("Anmelden um bis zu 15 Dokumente gleichzeitig hochzuladen. Sonst nur in einem eigenen Dokument gesucht werden.")

    if zu_anmeldung:
        switch_page("konto")

if st.session_state.username != '' and len(stream) > 15:
    stream = stream[:15]
    st.write("Die erste 15 Dokumente wurden zwischengespeichert")
elif st.session_state.username == '' and len(stream) >= 1:
    stream = stream[0]
    #st.write("Das erste Dokument wurden zwischengespeichert")


if stream != []:
    st.session_state["loader_state"] = False
    
    if st.session_state.username != '':
        with st.expander("Sammlung erstellen", expanded=st.session_state["speicher_expander"]):
            with st.form(key="Update Collections"):
                sc1, sc2, sc3 = st.columns([2,2,1])
                
                with sc1:
                    collection = st.text_input("Neue Sammlung anlegen:", max_chars=20, help="maximal 20 Buchstaben", value=None)

                if st.session_state["u_folders"] != [] and st.session_state["u_data_exists"] == True:
                    with sc2:
                        store.load_data_user()
                        update_col = st.selectbox('Sammlung aktualisieren',[n[0] for n in st.session_state["u_folders"][0][1]])

                with sc3:
                    submitted = st.form_submit_button("Laden")
                    

                if submitted:
                    if collection != None:
                        #Check if collection already exists
                        with st.spinner("Dokumente zwischenspeichern"):
                            ai.pickle_store(stream=stream, collection=collection )
                        st.session_state["user_choice_default"] = collection
                        st.session_state["option5value"] = True
                    else:
                        with st.spinner("Dokumente zwischenspeichern"):
                            ai.pickle_store(stream=stream, collection=update_col )
                        st.session_state["user_choice_default"] = update_col
                        st.session_state["option5value"] = True
                    st.session_state["speicher_expander"] = False
            
    else:
        collection = None
        #with st.spinner("Dokumente zwischenspeichern"):
        st.session_state["temp_upload"] = True 
        st.session_state["Temp_Stream"] = stream
        st.write("Ihr hochgeladenes Dokument wurde zwischengespeichert, auf laden klicken um mit dem dokument zu chatten")
            #ai.pickle_store(stream=stream, collection=collection )
            #st.session_state["option5value"] = True
            
            

st.write("Alle angewählten Verzeichnisse werden gleichzeitig durchsucht. Wählen Sie die Gewünschten und klicken Sie auf laden.")



col1, col2, col3, col4, col5 = st.columns(5)
docs_to_load = []
path, folders = store.load_data_preloaded()

baugesetz = folders[0]
normen = folders[1]
richtlininen = folders[2]
unternehmen = folders[3]

store.load_data_user()


with col1:
    option_1 = st.checkbox(baugesetz[0].split("_")[1])
    if option_1 == True:
        kanton_titel = baugesetz[1][0][0].split("_")[1]
        kanton_liste = [kanton[0] for kanton in baugesetz[1][0][1]]
        kanton_sel = selectbox(kanton_titel, kanton_liste)

        if kanton_sel:
            for kant in baugesetz[1][0][1]:
                if kant[0] == kanton_sel:
                    gemeinde_liste = [gemeinde[0] for gemeinde in kant[1]]
                    gemeinde_sel = selectbox("Gemeinde",gemeinde_liste)
                    if gemeinde_sel:
                        docs_to_load.append(f"{path}{baugesetz[0]}/{kanton_sel}/{gemeinde_sel}/")

with col2:
    option_2 = st.checkbox(normen[0].split("_")[1])
    if option_2 == True:
        normen_liste = [n[0] for n in normen[1]]
        norm = st.multiselect('Wählen Sie Normen', normen_liste)
        if norm != []:
            for n in norm:
                docs_to_load.append(f"{path}{normen[0]}/{n}/")

with col3:
    option_3 = st.checkbox(richtlininen[0].split("_")[1])
    if option_3 == True:
        richtlinie_liste = [n[0] for n in richtlininen[1]]
        richtlinie = st.multiselect('Wählen Sie Richtlinien',richtlinie_liste)
        if richtlinie != []:
            for r in richtlinie:
                docs_to_load.append(f"{path}{richtlininen[0]}/{r}/")

with col4:
    option_4 = st.checkbox(unternehmen[0].split("_")[1])
    if option_4 == True:
        unternehmen_liste = [n[0] for n in unternehmen[1]]
        konstruktion = st.multiselect('Wählen Sie Anbieter',unternehmen_liste)
        if konstruktion != []:
            for k in konstruktion:
                docs_to_load.append(f"{path}{unternehmen[0]}/{k}/")

with col5:
    if st.session_state.username != '':
        sammlung_checkbox = "Eigene Sammlungen"
    else:
        sammlung_checkbox = "Hochgeladenes Dokument"

    option_5 = None 

    opt_5 = st.checkbox(sammlung_checkbox,value=st.session_state["option5value"])
    if opt_5 == True and st.session_state.username != '':
        option_5 = True
        st.session_state["u_folders"] = None
        store.load_data_user()
        user_liste = [n[0] for n in st.session_state["u_folders"][0][1]]

        user_choice = st.multiselect('Sammlungen',user_liste, default=st.session_state["user_choice_default"])
        if user_choice != []:
            for c in user_choice:
                docs_to_load.append(f"{st.session_state['u_path']}/{c}/")

    if opt_5 == True and st.session_state.username == '':
        if st.session_state['u_path'] == None:
            st.write(st.session_state['u_path'])
        docs_to_load.append(f"{st.session_state['u_path']}/")
        option_5 = True
       

if any([option_1,option_2,option_3,option_4,option_5]) or st.session_state["temp_upload"] == True:
    if st.button("Verzeichnisse jetzt laden",type="primary"):
        st.session_state["docs_to_load"] = docs_to_load
        switch_page("chat")


