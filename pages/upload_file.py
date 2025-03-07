import os, config, modules, time
import streamlit as st
import pandas as pd


# Streamlit UI
st.set_page_config(layout="wide")
st.title("VectorDB Manager")

root_directory = config.ROOT_DIRECTORY
required_extensions = config.REQUIRED_EXTENSIONS
save_file_directory = config.SAVE_FILE_DIRECTORY

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
    
st.subheader("text splitter")
uploaded_file = st.file_uploader("upload file", type=["pdf","txt"])
if uploaded_file:
    file_extension = os.path.splitext(uploaded_file.name)[1].lower()
    try:
        if file_extension == ".pdf":
            chunks = modules.process_pdfs(uploaded_file)
        elif file_extension == ".txt":
            chunks = modules.process_txts(uploaded_file)
    except Exception as e:
        st.error(f"處理檔案{uploaded_file.name}時發生錯誤：{e}")
    st.markdown(f"<span style='color:#646487'>Total {len(chunks)} chunks</span>", unsafe_allow_html=True)
    data = pd.DataFrame(chunks)
    chunk_df = st.data_editor(
       data,
       column_config={
           "0":st.column_config.TextColumn(f"{len(chunks)} chunks",width="large")
       },
       use_container_width=True,
       hide_index=True
    )
    formatted_company = '、'.join(list_company)
    st.markdown(f"<span style='color:#646487'>上傳資料至: {formatted_company}</span>", unsafe_allow_html=True)
    if st.button("上傳檔案"):
        try:
            if file_extension in [".pdf",".txt"]:
                modules.save_to_vectordb(chunk_df["0"].tolist(),list_company,uploaded_file.name,root_directory)
                save_directory = modules.save_uploaded_file(uploaded_file,save_file_directory)
                st.success(f"檔案已儲存到 {save_directory}")
                time.sleep(2)
                st.rerun()
        except Exception as e:
            st.error(f"處理檔案{uploaded_file.name}時發生錯誤：{e}")
    # st.write(chunk_df["0"].tolist())

