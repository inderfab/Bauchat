import boto3
import os
from st_files_connection import FilesConnection
import streamlit as st
import dotenv
dotenv.load_dotenv()
import os
import io
import datetime
import pickle
import db
import random

st.session_state.update(st.session_state)

AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_DEFAULT_REGION = os.getenv("AWS_DEFAULT_REGION")
AWS_BUCKET_NAME = os.getenv("AWS_BUCKET_NAME")

# @st.cache_data
# def load_data_preloaded():
#     filepath = "data_preloaded-folders.pkl"
#     path = "data_preloaded/"

#     try:
#         folders = s3_download_pkl(filepath)
#     except:
#         folders = get_subfolders(path)

#         s3_upload_pkl(filepath, folders)

#     return path, folders



def load_data_temp():
    if st.session_state["u_folders"] == None: 
        
        timenow = datetime.datetime.now()
        timenow = timenow.strftime("%y-%m-%d_%H-%M-%S")

        st.session_state["u_folders"] = timenow


# ----- S3 Storage

def s3_boto_client():
    return boto3.client("s3")


def s3_uploader(filepath, file):
    # Binary Mode File
    client = s3_boto_client()
    bucket = "bauchatstorage"
    success = client.upload_fileobj(io.BytesIO(file), bucket,filepath)
    return success


def s3_reader(filepath):
    conn = st.experimental_connection('s3', type=FilesConnection)
    file = conn.open("bauchatstorage/"+filepath,mode="rb")
    return file



# def s3_get_subfolders(path):
#     client = s3_boto_client()
#     bucket = "bauchatstorage"
#     response = client.list_objects_v2(Bucket = bucket, Delimiter='/',Prefix =path) 
#     subfolders = []

#     files = []
#     if response.get("Contents"):
#         for key in response.get("Contents"):
#             f_name = key.get("Key").split("/")[-1]
#             files.append(f_name)
#         return files

#     else:
#         #st.write(path)
#         for folder in response.get('CommonPrefixes'):
#             subpath = folder.get('Prefix')
#             foldername = folder.get('Prefix').rstrip('/').split("/")[-1]  
#             sf = s3_get_subfolders(subpath)
#             subfolders.append([foldername,sf])
    
#     return subfolders

def s3_upload_pkl(key, data):
    
    data_pkl = pickle.dumps(data)
    success = s3_uploader(key, data_pkl)

    return success


def s3_download_pkl(key) -> str : 
    client = s3_boto_client()
    bucket = "bauchatstorage"
    
    file = client.get_object(Bucket=bucket,Key=key)
    file = file['Body'].read()
    file = pickle.loads(file)

    return file


def read_s3_contents_with_buffer(key) -> str :
    client = s3_boto_client()
    bucket = "bauchatstorage"
    bytes = io.BytesIO()
    client.download_fileobj(bucket, key, bytes)
    return bytes.getvalue()



def s3_download_files(path) -> str :
    client = s3_boto_client()
    bucket = "bauchatstorage"
    path = os.path.join(path,"docs/")
    response=client.list_objects_v2(Bucket=bucket,Prefix  = path)['Contents']
    #st.write("Response", response)
    files = []
    for f in response:
        key = f["Key"]
        if key.endswith(".pkl"):
            #st.write("Key: ", key)
            file = client.get_object(Bucket=bucket,Key=key)
            file = file['Body'].read()
            file = pickle.loads(file)
            files.append(file)
    #st.write("Files", files)
    return files


def s3_get_files(path) -> str :
    client = s3_boto_client()
    bucket = "bauchatstorage"
    response = client.list_objects_v2(Bucket = bucket, Delimiter='/',Prefix =path)
    st.write("s3_get_ ",response)

    files = []
    for file in response:
        subpath = os.path.join(path,file)
        
        if os.path.isfile(subpath):
            file_name = subpath.split("/")[-1]
            files.append(file_name) 
    return files



def download_button_full_pdf(key):   
    keynr = random.randint(100000,999999)
    #Key ist save_loc
    key += "-full.pdf" 
    down_file = st.button(label="Ganzes PDF herunterladen", key=keynr)
    if down_file is True:
        with st.spinner("Das PDF wird vom Server geladen"):
            pdf = s3_download_pkl(key)
        st.download_button(
            label="PDF speichern",
            data=pdf,
            file_name=key,
            mime="application/octet-stream",
            help="Lade das gesamte PDF herunter", 
            use_container_width=False,
            )

# ----- Local Storage

# def get_subfolders(path):
#     #Local Storage
#     objects_in_dir = sorted((f for f in os.listdir(path) if not f.startswith(".")), key=str.lower)

#     subfolders = []
#     for object in objects_in_dir:
#         subpath = os.path.join(path,object)
    
#         if os.path.isdir(subpath):
#             #st.write(subpath)
#             sf = get_subfolders(subpath)
#             if sf == []:
#                 sf = get_files(subpath)
#             subfolders.append([object,sf])
            
#     return subfolders

# def get_files(path):
#     objects_in_dir = sorted((f for f in os.listdir(path) if not f.startswith(".")), key=str.lower)

#     files = []
#     for file in objects_in_dir:
#         subpath = os.path.join(path,file)
        
#         if os.path.isfile(subpath):
#             file_name = subpath.split("/")[-1]
#             files.append(file_name) 
#     return files