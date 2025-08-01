import streamlit as st

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.docstore.document import Document
from langchain.vectorstores import FAISS
from langchain.chains.question_answering import load_qa_chain
from langchain.callbacks import get_openai_callback

import os
import re
import pickle
import store
import io
import time
import tiktoken
import db
from pypdf import PdfReader, PdfWriter

import dotenv
dotenv.load_dotenv()

st.session_state.update(st.session_state)


MODE = os.getenv("LLM_MODE", "cloud")

if MODE ==  "cloud":
    import openai
    try:
        key =  st.session_state["u_data"]["openai_key_user"]
    except:
        key = ''
    st.session_state.openai_key_user = key

    if st.session_state.openai_key_user == '':
        openai.api_key = os.getenv('OPENAI_API_KEY')
    else:
        openai.api_key =  st.session_state.openai_key_user


def get_embedding_model():
    MODE = os.getenv("LLM_MODE", "cloud")
    
    if MODE == "cloud":
        #openai.api_key = os.getenv("OPENAI_API_KEY")

        from langchain.embeddings.openai import OpenAIEmbeddings
        return OpenAIEmbeddings()
    
    else:
        from langchain.embeddings import HuggingFaceEmbeddings
        EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL")
        return HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
        

def get_llm():
    MODE = os.getenv("LLM_MODE", "cloud")
    system_prompt = "Du bist ein Assistent, der sich mit Baurecht auskennt."

    if MODE == "cloud":
        import openai
     
        def cloud_llm(prompt):
            model = 'gpt-3.5-turbo-0125'
            temperature = 0.0
            response = openai.ChatCompletion.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt},
                ],
                temperature=temperature
            )
            answer = response['choices'][0]['message']['content']
            usage = response['usage']
            return answer, usage

        return cloud_llm

    else:
        from ctransformers import AutoModelForCausalLM

        def load_local_llm():
            model_path = os.getenv("MODEL_PATH")
            model_type = os.getenv("MODEL_TYPE", "mistral") 

            llm = AutoModelForCausalLM.from_pretrained(
                model_path,
                model_type=model_type,
                temperature=0.3,
                top_k=40,
                top_p=0.7,
                repetition_penalty=1.1,
                threads=6,
                gpu_layers=0  # wichtig für M1 und Intel
            )
            #max_new_tokens=150,

            def local_llm(prompt):
                response = llm(prompt)
                usage = {"total_tokens": len(prompt.split()) + len(response.split())}
                return response, usage

            return local_llm
        
        return load_local_llm()

def pdf_preprocess(stream, metadata):
    text_pages = []
    full_text = ""
    reader = PdfReader(stream)
    
    stream.seek(0)
    stream_bytes_data = stream.getvalue()
    file_size = len(stream_bytes_data)
    st.session_state["bytes_update"] += file_size

    for i, page in enumerate(reader.pages,start=1):
        meta = {'page':i} | metadata
        text_page = page.extract_text()
        text_pages.append(Document(page_content=text_page, metadata=meta))
        full_text += text_page

    if full_text == "":
        st.session_state["ocr_needed"] = True
        st.session_state["exctraction_problem_files"].append(metadata["title"])
    return text_pages, reader, full_text, file_size


def pdf_page_to_buffer(reader, index):
    output = PdfWriter()
    buffer = io.BytesIO()
    output.add_page(reader._get_page(index))
    output.write(buffer)
    return buffer.getvalue()


def pdf_to_doc(stream, metadata):

    text_pages, reader, full_text,file_size = pdf_preprocess(stream, metadata)        

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size = 1500,
        chunk_overlap=200,
        length_function=len)
    
    num_pages = len(reader.pages)

    stream.seek(0)
    full_pdf = stream.getvalue()

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
    return {"title":metadata["title"],
            "document":document, 
            "pdf_reader":reader, 
            "full_text":full_text,
            "full_pdf": full_pdf,
            "num_pages":num_pages, 
            "file_size":file_size,
            }
    

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
    MODE = os.getenv("LLM_MODE", "cloud")
    docs = docs["document"]

    if MODE == "cloud":
        try:
            import tiktoken
            encoding = tiktoken.encoding_for_model("gpt-4-1106-preview")
            num_tokens = sum(len(encoding.encode(doc.page_content)) for doc in docs)
        except ImportError:
            num_tokens = 0
    else:
        num_tokens = 0

    if st.session_state["preload_active"] == False:
        st.session_state.token_usage += num_tokens
    return docs




def store_from_docs(docs):
    embeddings = get_embedding_model()
    return FAISS.from_documents(docs, embedding=embeddings)

### TODO
def create_Store(docs):
    if st.session_state.preload_key != None or st.session_state.username != "temp":
        path = docs["document"][0].metadata["save_loc"]
        title = docs["document"][0].metadata["title"]
    
        embedded_docs = embedd_FAISS(docs)
        vector_store = store_from_docs(embedded_docs)
        path_docs = os.path.join(path + "docs", title + ".pkl")

        pickle_byte_obj = pickle.dumps(vector_store)
        store.upload_file(path_docs, pickle_byte_obj)

        pickle_full_text = pickle.dumps(docs["full_text"])
        store.upload_file(os.path.join(path,title) + ".txt", pickle_full_text)


        for index in range(len(docs["pdf_reader"].pages)):
            pdf_page = pdf_page_to_buffer(docs["pdf_reader"], index)
            store.upload_file(os.path.join(path,title) + "-" + str(index+1) + ".pdf", pdf_page)
        
        full_pdf = pickle.dumps(docs["full_pdf"])
        store.upload_file(os.path.join(path,title) + "-full.pdf", full_pdf)
        

    if st.session_state.username == "temp":
        embedded_docs = embedd_FAISS(docs)
        vector_store = store_from_docs(embedded_docs)
        return vector_store           

    if st.session_state["preload_active"] == False and st.session_state.username != "temp":
        db.user_update_embedding_tokens(st.session_state.username)
        db.update_user_byte_size()
    
    return None


#@st.cache_data(ttl=0.1, show_spinner="Lädt die Sammlungen")
def load_store(paths):
    print("Stores to download", paths)
    stores = []
    if paths != []:
        for p in paths:
            file = store.download_all_pickles(p)
            stores.append(file)
    return stores


#@st.cache_data(show_spinner="Das zwischengespeicherte Dokument wird verarbeitet")
def store_temp(stream):
    title = stream.name.strip(".pdf")
    metadata = {"collection":None, "title":title}
    documents = pdf_to_doc(stream, metadata)
    if documents is not None:
        VectorStore = create_Store(documents)
        return VectorStore


def pickle_store(stream, collection):

    stream_len = len(stream)    
    if  stream_len >= 1:
        for s in stream:
            st.session_state["ocr_needed"] = False
            title = s.name.strip(".pdf")

            if st.session_state.preload_active:
                stores_path = os.path.join(st.session_state.preload_key, collection,'')
            else:
                stores_path = os.path.join(st.session_state.username, collection,'')
            metadata = {"collection":collection,"save_loc":stores_path,"title":title, "type":s.type }
            documents = pdf_to_doc(s, metadata)
            if st.session_state["ocr_needed"] == False:
                metadata.update({"num_pages":documents["num_pages"], 
                                    "file_size":documents["file_size"]})
                create_Store(documents)
                db.update_collection(metadata)


def submit_upload(stream):
    with st.spinner("Dokumente werden in die Cloud hochladen"):
        if st.session_state["collection"] != None:
            pickle_store(stream=stream, collection = st.session_state["collection"] )
            st.session_state["user_choice_default"] = st.session_state["collection"]
            st.session_state["option5value"] = True
            st.session_state["update_collection"] = None
            st.session_state["collection"] = None

        elif st.session_state["update_collection"] != None:
            pickle_store(stream=stream, collection= st.session_state["update_collection"] )
            st.session_state["user_choice_default"] = st.session_state["update_collection"]
            st.session_state["option5value"] = True
            st.session_state["update_collection"] = None
            st.session_state["collection"] = None

        else:
            st.write("Sammlung auswählen")

        st.session_state["speicher_expander"] = False
        

    if st.session_state["preload_active"] == True:
        st.write("Streams: ", stream )

#@st.cache_data(ttl=60)
def merge_faiss_stores(store_list):
    vector_store = store_list.pop(0)
    for store in store_list:  
        vector_store.merge_from(store)
    return vector_store


# ----- Suche -----
def search(VectorStore, query,k=3):
    docs = VectorStore.similarity_search(query=query, k=k,)
    return docs


def prompt(query, results, k=1):

    kontext = "\n".join([text.page_content + " Quelle= " + text.metadata["title"] + " Seite= " + str(text.metadata["page"]) for i,text in enumerate(results)])
    
    if st.session_state.long_answer == False:
        answerlength = "kurz in zwei bis drei Sätzen"
    else:
        answerlength = "ausführlich mit bis zu 10 Sätzen"
    
    prompt_text = f"Aufgabe: Frage {answerlength} mit einer oder mehreren Quellen beantworten, diese auch angeben (Quelle und Seite). Sie sind nach Relevanz sortiert. Quellen:{kontext}Frage: {query} Antwort:"
    
    llm = get_llm()
    answer, usage = llm(prompt_text)
    
    return answer, usage



def bauchat_query(query, VectorStore, k=3):

    result = search(VectorStore,query,k=4)
    
    references_list = []

    for res in result:
        try:
            save_loc = res.metadata["save_loc"]
        except:
            save_loc = 'temp'

        references = {"title":res.metadata["title"],  "page":res.metadata["page"], "save_loc":save_loc }
        references_list.append(references)

    answer, usage = prompt(query, result, k)

    date = time.strftime("%Y-%m")
    id = time.strftime("%Y-%m-%d-%m-%H-%M-%S")
    m_user = {"role": "user", "content": query, "date":date}
    m_ai = {"role": "ai", "content": answer, "references":references_list}

    message_dict = {"user":m_user, "ai": m_ai, "references":references_list, "usage":usage, "id":id}
    st.session_state.messages.append(message_dict)

    return message_dict

