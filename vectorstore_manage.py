import os
import streamlit as st
from langchain_chroma import Chroma
import pandas as pd
import time
import config
import modules
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(layout="centered")
st.title("VectorDB Manager")
# User input
root_directory = config.ROOT_DIRECTORY
required_extensions = config.REQUIRED_EXTENSIONS

if "chunk_size" not in st.session_state:
    st.session_state.chunk_size = 220
if "chunk_overlap" not in st.session_state:
    st.session_state.chunk_overlap = 0
if "preview_text" not in st.session_state:
    st.session_state.preview_text = ""

modules.sidebar()
print("api", os.getenv("OPENAI_API_KEY"))

company_names = modules.list_companies(root_directory, required_extensions)
list_company = st.multiselect('Company',company_names,company_names[0])

if list_company:
    data = []
    for company in list_company:
        persist_directory = os.path.join(root_directory, company)
        existing_files = modules.list_existing_files(persist_directory)
        for file in existing_files:
            data.append({"公司": company, "文件": file})

    df = pd.DataFrame(list(data))
    df["選擇"]= False
    edited_df = st.data_editor(
        df, 
        column_config={
            "公司": st.column_config.Column("公司", disabled=True), 
            "文件": st.column_config.Column("文件", disabled=True), 
            "選擇": "選擇檔案"}, 
        hide_index=True)
    modify_files = edited_df[edited_df["選擇"] == True]["文件"].tolist()
    modify_company = edited_df[edited_df["選擇"] == True]["公司"].tolist()
   
    files_to_delete = list(zip(modify_files, modify_company))

    formatted_files_to_delete = '、<br>'.join([f"{file} (來自: {company})" for file, company in files_to_delete])
    st.markdown(f"<span style='color:#ff6666'>刪除資料:<br> {formatted_files_to_delete}</span>", unsafe_allow_html=True)

    if st.button("刪除檔案"):
        try:
            for file_to_delete, company in files_to_delete:
                persist_directory = os.path.join(root_directory, company)
                st.write(f"正在刪除檔案 '{file_to_delete}' 在公司 '{company}' 的資料庫...")
                db = Chroma(collection_name="test2", persist_directory=persist_directory)
                delete_ids = db.get(where={"source": file_to_delete})['ids']
                if delete_ids:
                    db.delete(delete_ids)
                    st.success(f"檔案 '{file_to_delete}' 已從公司 '{company}' 刪除！")
                    time.sleep(2)
                    st.rerun()
        except Exception as e:
            st.error(f"刪除檔案時發生錯誤：{e}")
else:
    st.switch_page('pages/create_company.py')