import os
import streamlit as st
import time
import config
import modules


st.set_page_config(layout="centered")
st.title("VectorDB Manager")

root_directory = config.ROOT_DIRECTORY
required_extensions = config.REQUIRED_EXTENSIONS

if "chunk_size" not in st.session_state:
    st.session_state.chunk_size = 220
if "chunk_overlap" not in st.session_state:
    st.session_state.chunk_overlap = 0

modules.sidebar()

st.subheader("Create Company")
new_company_name = st.text_input("輸入公司名稱")
# PDF upload
upload_files = st.file_uploader("選擇 PDF 檔案", type=["pdf","txt"], accept_multiple_files=True)
if st.button("創建公司並上傳資料"):
    if not upload_files and not new_company_name:
        st.warning("請輸入公司名稱及選擇檔案！")
    elif not upload_files:
        st.warning("請選擇檔案！")
    elif not new_company_name:
        st.warning("請輸入公司名稱！")
    else:
        success =True
        for file in upload_files:
            file_name = file.name
            persist_directory = os.path.join(root_directory, new_company_name)
            file_extension = os.path.splitext(file_name)[1].lower()
            try:
                if file_extension == ".pdf":
                    save_file_path = os.path.join("vectordb/data", file_name)
                    modules.create_company_process_pdfs(file,persist_directory,save_file_path)
                elif file_extension == ".txt":
                    save_file_path = os.path.join("vectordb/data", file_name)
                    modules.create_company_process_txts(file,persist_directory,save_file_path)
            except Exception as e:
                    st.error(f"處理檔案{file_name}時發生錯誤：{e}")
                    success = False
                    continue
            if success:            
                st.success("向量儲存成功！")
            else:
                st.warning("有部分檔案處理失敗，請檢查上傳的檔案格式或內容。")
        time.sleep(1.5)
        # st.rerun()

        