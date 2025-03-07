import os
import streamlit as st
from langchain_chroma import Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceBgeEmbeddings
from langchain_core.documents import Document
import pdfplumber
import config
import pandas as pd
def sidebar():
    st.sidebar.title("Settings")
    st.session_state.chunk_size = st.sidebar.number_input("Chunk Size", value=st.session_state.chunk_size)
    st.session_state.chunk_overlap = st.sidebar.number_input("Chunk Overlap", value=st.session_state.chunk_overlap)
    st.session_state.embedding = st.sidebar.selectbox("Embedding", ["BAAI/bge-small-zh-v1.5", "BAAI/bge-small-en-v1.5","/Users/zhangchenwei/Downloads/models/chinese_train/model"])
    st.session_state.splitter_option = st.sidebar.selectbox("Splitter", ["LangChain Recursive Splitter"])
    st.session_state.separators = ["故障狀況","\n\n","\n"]
    display_separators = [sep.replace("\n", "\\n") for sep in st.session_state.separators]
    df = pd.DataFrame(display_separators)
    separators_df = st.sidebar.data_editor(
        df,
        column_config={
            "0": st.column_config.TextColumn("Separators", width="medium")},
        hide_index=True,
        num_rows="dynamic")
    if separators_df is not None:
        updated_separators = separators_df["0"].tolist()
        st.session_state.separators = [sep.replace("\\n", "\n") for sep in updated_separators]
        st.sidebar.write("separators:", st.session_state.separators)
    st.sidebar.link_button("chunkviz", "https://chunkviz.up.railway.app/")

def list_companies(root_directory, filename):
    matching_folders = []
    if not os.path.exists(root_directory):
        os.makedirs(root_directory, exist_ok=True)
        st.switch_page('pages/create_company.py')
    else:
        for dirpath, dirnames, filenames in os.walk(root_directory):
            if filename in filenames:
                matching_folders.append(os.path.basename(dirpath))
        if matching_folders == []:
            st.switch_page('pages/create_company.py')
        else:
            return matching_folders

def list_existing_files(persist_directory):
    if os.path.exists(persist_directory):
        db = Chroma(collection_name="test2", persist_directory=persist_directory)
        return set(metadata['source'] for metadata in db.get()['metadatas'])
    return []

def process_txts(txt):
    text=""
    encodings = ['utf-8', 'gbk', 'ISO-8859-1']
    for encoding in encodings:
        try:
            text = txt.read().decode(encoding)
            break
        except UnicodeDecodeError:
            print(f"編碼 {encoding} 失敗。")
        except Exception as e:
            print(f"發生錯誤: {e}")
    chunks = get_text_chunks(text)
    return chunks

def process_pdfs(pdf):
    text=""
    with pdfplumber.open(pdf) as pdf_file:
        for page in pdf_file.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text
    chunks = get_text_chunks(text)
    return chunks
def get_text_chunks(raw_text):
    if st.session_state.splitter_option == "LangChain Recursive Splitter":
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=st.session_state.chunk_size,  # 可調整塊大小
            chunk_overlap=st.session_state.chunk_overlap,
            separators=st.session_state.separators,
            length_function=len,
            keep_separator= True
        )
        chunks = splitter.split_text(raw_text)
    return chunks  
  
def save_to_vectordb(chunks,selected_company,txt_name,root_directory):
    embeddings = HuggingFaceBgeEmbeddings(
        model_name=st.session_state.embedding,
        model_kwargs={'device': "cpu"},
        encode_kwargs={'normalize_embeddings': True},
    )
    save_file_path = os.path.join("vectordb/data", txt_name)
    chunks_with_metadata = [
            Document(page_content=chunk, metadata={"source": save_file_path}) for chunk in chunks if chunk.strip()
    ]
    for company in selected_company:
        persist_directory = os.path.join(root_directory, company)
        vectorstore = Chroma.from_documents(documents=chunks_with_metadata, embedding=embeddings, persist_directory=persist_directory, collection_name='test2')
    return vectorstore

def save_uploaded_file(file, target_directory):
    """
    儲存上傳的檔案到指定資料夾。
    :param file: 上傳的檔案物件
    :param target_directory: 目標儲存資料夾路徑
    """
    os.makedirs(target_directory, exist_ok=True)
    save_path = os.path.join(target_directory, file.name)
    with open(save_path, "wb") as f:
        f.write(file.getbuffer())
    return save_path

def create_company_process_txts(txt, persist_directory,save_file_path):
    save_uploaded_file(txt,config.SAVE_FILE_DIRECTORY)
    embeddings = HuggingFaceBgeEmbeddings(
        model_name= st.session_state.embedding,
        model_kwargs={'device': "cpu"},
        encode_kwargs={'normalize_embeddings': True},
    )
    text=""
    encodings = ['utf-8', 'gbk', 'ISO-8859-1']
    for encoding in encodings:
        try:
            text = txt.read().decode(encoding)
            break
        except UnicodeDecodeError:
            print(f"編碼 {encoding} 失敗。")
        except Exception as e:
            print(f"發生錯誤: {e}")

    chunks = get_text_chunks(text)
    chunks_with_metadata = [
            Document(page_content=chunk, metadata={"source": save_file_path}) for chunk in chunks
    ]
    vectorstore =  Chroma.from_documents(documents=chunks_with_metadata, embedding=embeddings, persist_directory=persist_directory, collection_name='test2')
    return vectorstore

def create_company_process_pdfs(pdf, persist_directory,save_file_path):
    save_uploaded_file(pdf,config.SAVE_FILE_DIRECTORY)
    embeddings = HuggingFaceBgeEmbeddings(
        model_name= st.session_state.embedding,
        model_kwargs={'device': "cpu"},
        encode_kwargs={'normalize_embeddings': True},
    )
    text=""
    with pdfplumber.open(pdf) as pdf_file:
        for page in pdf_file.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text

    chunks = get_text_chunks(text)
    chunks_with_metadata = [
            Document(page_content=chunk, metadata={"source": save_file_path}) for chunk in chunks
    ]
    vectorstore = Chroma.from_documents(documents=chunks_with_metadata, embedding=embeddings, persist_directory=persist_directory, collection_name='test2')
    return vectorstore