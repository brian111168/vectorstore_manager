import os
import streamlit as st
from langchain.load.dump import dumps
from langchain_chroma import Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter,SpacyTextSplitter,NLTKTextSplitter
from langchain_community.embeddings import HuggingFaceBgeEmbeddings
from langchain_core.documents import Document
import pandas as pd
import pdfplumber
import config
import modules


def search_vector_database(selected_company, query, root_directory):
    embeddings = HuggingFaceBgeEmbeddings(
        model_name= st.session_state.embedding,
        model_kwargs={'device': "cpu"},
        encode_kwargs={'normalize_embeddings': True},
    )
    results = {}
    for company in selected_company:
        persist_directory = os.path.join(root_directory, company)
        vectorstore = Chroma(embedding_function=embeddings, persist_directory=persist_directory, collection_name='test2')
        retriever = vectorstore.as_retriever(search_kwargs={'k': 10})
        result = retriever.get_relevant_documents(query)
        results[company] = result
    return results


st.set_page_config(layout="wide")
st.title("VectorDB Manager")

root_directory = config.ROOT_DIRECTORY
required_extensions = config.REQUIRED_EXTENSIONS

if "chunk_size" not in st.session_state:
    st.session_state.chunk_size = 220
if "chunk_overlap" not in st.session_state:
    st.session_state.chunk_overlap = 0
if "slpitter_option" not in st.session_state:
    st.session_state.slpitter_option = 0

modules.sidebar()

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
    
st.subheader("retrieve test")
query = st.text_input("輸入要檢索的文字：")
if query:
    results = search_vector_database(list_company, query, root_directory)
    if results:
        st.write("檢索結果：")
        for company, docs in results.items():
            st.subheader(f"公司：{company}")
            if docs:
                for idx, doc in enumerate(docs):
                    # 假設每個檢索結果有 `page_content` 屬性
                    # st.markdown(f"**{idx + 1}.** {doc.page_content}")
                    source = doc.metadata.get("source", "未知來源")  # 確保來源存在
                    st.markdown(f"**{idx + 1}.** {doc.page_content}  \n**來源：** {source}")
            else:
                st.write("未找到相關結果。")
    else:
        st.write("未找到相關結果。")