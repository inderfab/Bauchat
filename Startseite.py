import streamlit as st
import os

page_title = "bauCHAT"

st.set_page_config(page_title = page_title,layout="wide") #

AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
AWS_DEFAULT_REGION = os.getenv('AWS_DEFAULT_REGION')
AWS_BUCKET_NAME = os.getenv('AWS_BUCKET_NAME')

st.write(AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY,AWS_DEFAULT_REGION,AWS_BUCKET_NAME)
