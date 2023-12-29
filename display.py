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


def pdf2jpg_from_s3(references, k):
    keys = {}
    for i, ref in enumerate(references):
        pagenr = ref["page"]
        name = f'{str(i+1)}: {ref["title"]} Seite: {str(ref["page"])}'
        key = ref["save_loc"] + "-" + str(pagenr) +".pdf"
        keys.update({name:key})
    
    img_col, src_col = st.columns([3,1])
    with src_col:
        img_src = st.radio(f"Die {k} relevantesten Quellen", keys)
    
    with img_col:
        display_PDF_IMG(keys[img_src])
        #display_PDF_HTML(key)


@st.cache_data
def display_PDF_IMG(key):
    size = None
    file = store.read_s3_contents_with_buffer(key)
    img = pdf2image.convert_from_bytes(file,first_page= 0,last_page=1,size=size)
    st.image(img,use_column_width=True)    
    

def display_PDF_HTML(key):
    file = store.read_s3_contents_with_buffer(key)
    base64_pdf = base64.b64encode(file).decode('utf-8')

    pdf_display = F'<iframe src="data:application/pdf;base64,{base64_pdf}" view="fit" frameBorder="0" width="700" height="950" type="application/pdf"></iframe>'

    st.markdown(pdf_display, unsafe_allow_html=True)



def PDF2JPG2(result,k=3):
    size = None
    use_column_width = "auto"
    display_lst = []
    Stream = []


    for res in result:
        for folder in st.session_state["docs_to_load"]:
            file_path = os.path.join(folder,res.metadata['title'] + ".stream")


    for res in result:
        for folder in st.session_state["docs_to_load"]:
            file_path = os.path.join(folder,res.metadata['title'] + ".stream")
            
            if os.path.exists(file_path):
                with open(file_path,"rb") as fp:
                    Stream = io.BufferedReader(fp)
                    page = res.metadata["page"]
                    title = res.metadata["title"]
                    img = pdf2image.convert_from_bytes(Stream.read(),first_page= page,last_page=page,size=size)
                    display_lst.append({"title":title,"seite":page,"bild":img})
                    
         
    if display_lst != []:
        cols = st.columns(k,gap="medium")
        col = 0
        for res in display_lst:
            with cols[col]:          
                st.write(res["title"])
                st.write("Seite: " + str(res["seite"]))
                st.image(res["bild"],use_column_width=use_column_width)
            col += 1
        

