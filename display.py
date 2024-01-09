import pdf2image
import streamlit as st
import io
from PIL import Image
import os
from pathlib import Path
from streamlit_extras.row import row
from pypdf import PdfReader
import store
import base64


def pdf_display(references, id):
    #generates tab with Radio Button to choose page to display

    keys = {}
    for i, ref in enumerate(references):
        pagenr = ref["page"]
        name = f'{str(i+1)}: {ref["title"]} Seite: {str(ref["page"])}'
        if ref.get("save_loc") is not 'temp':
            key = ref["save_loc"] + "-" + str(pagenr) +".pdf"
        else:
            key = "temporary"
        keys.update({name:key})
    
    img_col, src_col = st.columns([3,1])
    with src_col:
        img_src = st.radio(label="Relevante Quellen", options=keys, key=id)
        full_pdf_key = "".join(keys[img_src].split("-")[:-1])
        if keys[img_src] != 'temporary': 
            store.download_button_full_pdf(full_pdf_key)

    with img_col:
        if keys[img_src] != 'temporary': 
            pdf_s3_to_img(keys[img_src])
            #pdf_s3_to_iframe(keys[img_src])
        else:
            pdf_temp_to_img()
            #pdf_temp_to_iframe()
        
        #display_PDF_HTML_S3(key)



@st.cache_data
def pdf_s3_to_img(key):
    #Downloads PDF Page from AWS S3 and outputs as IMG in st.image
    size = None
    file = store.read_s3_contents_with_buffer(key)
    img = pdf2image.convert_from_bytes(file,first_page= 0,last_page=1,size=size)
    st.image(img,use_column_width=True)    
    

@st.cache_data
def pdf_s3_to_iframe(key):
    #Downloads PDF Page from AWS S3 and outputs in iFrame as PDF
    file = store.read_s3_contents_with_buffer(key)
    base64_pdf = base64.b64encode(file).decode('utf-8')

    pdf_iframe = F'<iframe src="data:application/pdf;base64,{base64_pdf}" view="fit" frameBorder="0" width="700" height="950" type="application/pdf"></iframe>'

    #page=5&navpanes=0&scrollbar=0&view=fit
    st.markdown(pdf_iframe, unsafe_allow_html=True)


@st.cache_data
def pdf_temp_to_img():
    #Displays the Stream.read() file
    file = st.session_state["Temp_Stream_IMG"]
    img = pdf2image.convert_from_bytes(file)
    st.image(img)    


#@st.cache_data
def pdf_temp_to_iframe():
    #Downloads PDF Page from AWS S3 and outputs in iFrame as PDF
    file = st.session_state["Temp_Stream_IMG"]
    base64_pdf = base64.b64encode(file).decode('utf-8')

    pdf_iframe = F'<iframe src="data:application/pdf;base64,{base64_pdf}" view="fit" frameBorder="0" width="700" height="950" type="application/pdf"></iframe>'
    st.markdown(pdf_iframe, unsafe_allow_html=True)



def chat_display(messages):
    expand_newest_len = len(messages)
    expand_newest = [False] * expand_newest_len
    expand_newest[-1] = True

    for i,message in enumerate(messages):

        # m_user = {"role": "user", "content": query, "date":date}
        # m_ai = {"role": "ai", "content": answer, "references":references_list}
        # message_dict = {"user":m_user, "ai": m_ai, "references":references_list, "usage":usage}
        

        with st.expander(label=message["user"]["content"], expanded=expand_newest[i]):

            chat_tab, pdf_tab = st.tabs(["Chat", "Quellen"])
            with chat_tab:
                with st.chat_message("user"):
                    st.write(message["user"]["content"])

                with st.chat_message("ai"):
                    st.write(message["ai"]["content"])

            with pdf_tab:
                pdf_display(references = message["references"], id = message["id"])
