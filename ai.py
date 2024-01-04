from pypdf import PdfReader, PdfWriter
import streamlit as st

from langchain.text_splitter import RecursiveCharacterTextSplitter
import re
import pickle
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.docstore.document import Document
from langchain.vectorstores import FAISS
from langchain.chains.question_answering import load_qa_chain
from langchain.callbacks import get_openai_callback
import os
import openai
import store
import io
import time
import tiktoken
import db

import dotenv
dotenv.load_dotenv()

from langchain.document_loaders import PyPDFLoader
openai.api_key = os.getenv('OPENAI_API_KEY')


def pdf_preprocess(stream, metadata):
    text_pages = []
    full_text = ""
    reader = PdfReader(stream)

    for i, page in enumerate(reader.pages,start=1):
        meta = {'page':i} | metadata
        text_page = page.extract_text()
        text_pages.append(Document(page_content=text_page, metadata=meta))
        full_text += text_page

    return text_pages, reader, full_text


def pdf_page_to_buffer(reader, index):
    output = PdfWriter()
    buffer = io.BytesIO()
    output.add_page(reader._get_page(index))
    output.write(buffer)
    return buffer.getvalue()


def pdf_to_doc(stream, metadata):

    text_pages, reader, full_text = pdf_preprocess(stream, metadata)

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size = 1500,
        chunk_overlap=200,
        length_function=len)
    
    texts = []
    text = [p.page_content for p in text_pages]
    for t in text:
        texts.append(clean_text(t))

    meta_page = [p.metadata for p in text_pages]
    metas = []
    if metadata != None:
        for m in meta_page:
            metas.append(m|metadata)
    else:
        metas = meta_page

    document = text_splitter.create_documents(texts = texts, metadatas = metas)
    return {"title":metadata["title"],"document":document, "pdf_reader":reader, "full_text":full_text}


def clean_text(text):
    clean_text = text.encode("utf-8", "ignore").decode("utf-8")
    
    clean_text = re.sub(r" {2,}", " ", clean_text)
    clean_text = re.sub(r"-\n", "", clean_text)
    clean_text = clean_text.strip()
    clean_text = re.sub(r"\n", "", clean_text)
    finder = re.compile("([a-z])\s([a-z])")
    clean_text = finder.sub(r'\1\2', clean_text, 1)
    
    return clean_text


def embedd_FAISS(docs):
    embeddings = OpenAIEmbeddings()
    encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")
    #num_tokens = 0
    docs = docs["document"]
    #for doc in docs:
    #    num_tokens += len(encoding.encode(doc))
    #st.session_state.token_usage += num_tokens

    VectorStore = FAISS.from_documents(docs, embedding=embeddings)
    return VectorStore


def create_Store(docs):

    if st.session_state.username != 'temp':
        save_loc = docs["document"][0].metadata["save_loc"]
        VectorStore = embedd_FAISS(docs)
        
        pickle_full_text = pickle.dumps(docs["full_text"])
        store.s3_uploader(save_loc+".txt", pickle_full_text)

        pickle_byte_obj = pickle.dumps(VectorStore)
        store.s3_uploader(save_loc+".pkl", pickle_byte_obj)

        for index in range(len(docs["pdf_reader"].pages)):
            pdf_page = pdf_page_to_buffer(docs["pdf_reader"], index)
            store.s3_uploader(save_loc + "-" + str(index+1) + ".pdf", pdf_page)
        
        st.session_state["Files_Saved"] = True

    if st.session_state.username == "temp":
        VectorStore = embedd_FAISS(docs)                
        st.session_state["Files_Saved"] = True

    #login.user_update_embedding_tokens(st.session_state.username)
    return VectorStore


def combine_Stores(VectorStores):
    # Merges all Vectorstores to the Base (First in List)
    baseVS = VectorStores[0]
    for vs in VectorStores[1:]:
        baseVS.merge_from(vs)
    return baseVS


#@st.cache_data
def load_Store(paths):
    VectorStores = []
    
    for p in paths:
        #if st.session_state["Storage"] == "S3":
        files = store.s3_download_files(p)
        VectorStores = files

        # if st.session_state["Storage"] == "Local":
        #     subfolders = sorted((f for f in os.listdir(p) if not f.startswith(".")), key=str.lower)
        #     for s in subfolders:
        #         if s.split(".")[-1] == "pkl":
        #             with open(f"{p}{s}","rb") as f:
        #                 VectorStore = pickle.load(f)
        #                 VectorStores.append(VectorStore)
            
    VectorStore = combine_Stores(VectorStores)

    return VectorStore #, Stream


def pickle_store(stream=None, collection=None):
    if st.session_state["Files_Saved"] == False:
        if  len(stream) >= 1:
            for s in stream:
                title = s.name.strip(".pdf")
                stores_path = store.store_location(new_collection=collection)
                save_loc = os.path.join(stores_path,title)
                metadata = {"collection":collection,"save_loc":save_loc,"title":title, "type":s.type }
                documents = pdf_to_doc(s, metadata)
                #create_Store(documents)
                db.update_data_db(metadata)


def submit_upload(stream):
    with st.spinner("Dokumente zwischenspeichern"):
        if st.session_state["collection"] != None:
            pickle_store(stream=stream, collection = st.session_state["collection"] )
            st.session_state["user_choice_default"] = st.session_state["collection"]
            st.session_state["option5value"] = True
            
        elif st.session_state["update_collection"] != None:
            pickle_store(stream=stream, collection= st.session_state["update_collection"] )
            st.session_state["user_choice_default"] = st.session_state["update_collection"]
            st.session_state["option5value"] = True
        
        else:
            st.write("Sammlung auswählen")

        st.session_state["speicher_expander"] = False
        st.session_state["update_collection"] = None
        st.session_state["collection"] = None


def store_temp(stream=None, collection=None):
    title = stream.name.strip(".pdf")
    metadata = {"collection":collection, "title":title}
    #st.write(stream)
    documents = pdf_to_doc(stream, metadata)
    Vectorstore_Temp = create_Store(documents)
    return Vectorstore_Temp




# ----- Suche -----
def search(VectorStore, query,k=3):
    docs = VectorStore.similarity_search(query=query, k =k)
    return docs


def prompt(query, results, k=1):
    model = 'gpt-3.5-turbo'
    temperature=0.0
    kontext = "\n".join([text.page_content + " Quelle= " + text.metadata["title"] + " Seite= " + str(text.metadata["page"]) for i,text in enumerate(results)])
    
    if st.session_state.long_answer == False:
        answerlength = "kurz in zwei bis drei Sätzen"
    else:
        answerlength = "ausführlich mit bis zu 10 Sätzen"
    
    prompt = f"Aufgabe: Frage {answerlength} mit einer oder mehreren Quellen beantworten, diese auch angeben (Quelle und Seite). Sie sind nach Relevanz sortiert. Quellen:{kontext}Frage: {query} Antwort:"
    response = openai.ChatCompletion.create(
        model=model,
        messages=[
            {"role": "system", "content": "Du bist ein Assisten der sich mit Baurecht auskennt."},
            {"role": "user", "content": prompt},
            ],
        temperature=temperature)
    
    answer = response['choices'][0]['message']['content']
    usage = response['usage']
    return answer, usage



def bauchat_query(query, VectorStore, k=4):
 
    with st.spinner("Dokumente durchsuchen"):
        result = search(VectorStore,query,k=k+2)
    answer, usage = prompt(query, result, k=k)

    references_list = []
    for res in result:
        try:
            save_loc = res.metadata["save_loc"]
        except:
            save_loc = 'temp'
 
        references = {"title":res.metadata["title"],  "page":res.metadata["page"], "save_loc":save_loc }
        references_list.append(references)


    date = time.strftime("%Y-%m")
    id = time.strftime("%Y-%m-%d-%m-%H-%M-%S")
    m_user = {"role": "user", "content": query, "date":date}
    m_ai = {"role": "ai", "content": answer, "references":references_list}

    message_dict = {"user":m_user, "ai": m_ai, "references":references_list, "usage":usage, "id":id}
    st.session_state.messages.append(message_dict)

    return message_dict

