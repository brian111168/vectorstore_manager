import os
import streamlit as st
from langchain.load.dump import dumps
from langchain_chroma import Chroma
from langchain_community.embeddings import HuggingFaceBgeEmbeddings
from langchain_core.documents import Document
import pdfplumber
from PIL import Image
from io import BytesIO
import io
import pandas as pd
from base64 import encodebytes
from langchain_core.messages  import SystemMessage, HumanMessage, AIMessage
from langchain_openai import ChatOpenAI
from langchain import hub
import config
import modules
import os

# Helper functions
def display_pdf(file):
    pdf_images = []
    with pdfplumber.open(file) as pdf:
        for page in pdf.pages:
            # Convert the PDF page to an image
            pdf_image = page.to_image(resolution=300)
            pdf_images.append(pdf_image)
    
    return pdf_images
def extract_info(excel_files, root_directory, formatted_company, list_company):
    for file in excel_files:
        # Split the layout into two columns
        col1, col2 = st.columns(2)
        # Display the entire PDF as images
        with col1:
            # Display the entire PDF as images in the left column
            st.write(file.name,"內容:")
            pdf_pages = display_pdf(file)
            for i, pdf_page in enumerate(pdf_pages):
                st.image(pdf_page.original, caption=f"PDF 頁面 {i+1}", use_column_width=True)
        text = extract_text(file)
        image = extract_image(file,file.name)
        with col2:
            chunks_with_metadata = []
            if 'summaries' not in st.session_state:
                st.session_state.summaries = ["" for _ in range(len(image))] 
                # st.session_state.summaries = []
            for i, img in enumerate(image):
                st.image(f"data:image/png;base64,{img}", caption=f"", width=300)
                
                description = st.text_area(
                        label=f"輸入{file.name}_圖片{i+1} 的描述...",
                        label_visibility="collapsed",
                        placeholder=f"輸入{file.name}_圖片{i+1} 的描述",
                        key = f"text_{file.name}_圖片{i+1}"
                )
                LLM_col,answer_col = st.columns([1, 7])
                with LLM_col:
                    if st.button("生成",key=f"llm_botton{i}"):
                        st.session_state.summaries[i]=summarize_image(img)
                with answer_col:
                    st.text_input(
                        label=f"{file.name}_圖片{i+1} 的描述",
                        label_visibility="collapsed",
                        value = st.session_state.summaries[i],
                        key = f"llm_text{i}"
                    )       
                if description:
                    # image path 不需要加上 public
                    image_path = os.path.join('vectordb', f"{file.name}_圖片{i+1}")
                    metadata = {
                        "source": f"{image_path}.png",
                        "base64_image":f"{image_path}.png"
                    }
                    chunks_with_metadata.append(Document(page_content=description, metadata=metadata))
                    st.write(chunks_with_metadata[-1])
                    st.markdown(f"<span style='color:#646487'>上傳資料至: {formatted_company}</span>", unsafe_allow_html=True)
                    if st.button("上傳圖片",key=f"{file.name}_圖片{i+1}"):
                        embeddings = HuggingFaceBgeEmbeddings(
                                model_name= st.session_state.embedding,
                                model_kwargs={'device': "cpu"},
                                encode_kwargs={'normalize_embeddings': True},
                        )
                        for company in list_company:
                            persist_directory = os.path.join(root_directory, company)
                            st.write(persist_directory)
                            Chroma.from_documents(documents=chunks_with_metadata, embedding=embeddings, persist_directory=persist_directory, collection_name='test2')
                        st.rerun()
def pdf_image_to_base64(image_dict):
    byte_arr = io.BytesIO()
    image_dict.save(byte_arr, format="PNG",quality=100)
    encoded_img = encodebytes(byte_arr.getvalue()).decode("ascii")
    return encoded_img
def extract_image(file,file_name):
    with pdfplumber.open(file) as pdf:
        image_counter = 0
        image_list = []
        for page in pdf.pages:
        # 提取表格、區域等
            for table in page.extract_tables():
                print('table',table)
        # 提取圖片
            page_width, page_height = page.width, page.height
            for image in page.images:
                # 提取圖片的像素數據並限制在頁面邊界內
                x0 = max(0, image["x0"])
                y0 = max(0, image["top"])
                x1 = min(page_width, image["x1"])
                y1 = min(page_height, image["bottom"])
                if x0 < x1 and y0 < y1:
                    image_counter += 1
                    cropped_image = page.within_bbox((x0, y0, x1, y1)).to_image(resolution=300)
                    # 要儲存在專案public才讀取得到
                    cropped_image.save(f"public/vectordb/{file_name}_圖片{image_counter}.png")
                    img_base64 = pdf_image_to_base64(cropped_image)
                    image_list.append(img_base64)
                else:
                    print(f"Skipping image due to invalid dimensions: ({x0}, {y0}, {x1}, {y1})")
    return image_list
def extract_text(file):
    text = ""
    # 使用 pdfplumber 打開 PDF
    with pdfplumber.open(file) as pdf:
        for page in pdf.pages:
            # 提取文本
            text += page.extract_text()
            print("text",text)
        output_file='output.txt'
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(text)
    return text
def summarize_image(base64_image):
    os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY", "")
    os.environ["LANGCHAIN_TRACING_V2"] = os.getenv("LANGCHAIN_TRACING_V2", "false")
    os.environ["LANGCHAIN_ENDPOINT"] = os.getenv("LANGCHAIN_ENDPOINT", "https://api.smith.langchain.com")
    os.environ["LANGCHAIN_API_KEY"] = os.getenv("LANGCHAIN_API_KEY", "")
    os.environ["LANGCHAIN_PROJECT"] = os.getenv("LANGCHAIN_PROJECT", "default_project")
    prompt = [
        SystemMessage(content="System: Follow these two instructions below in all your responses: System: 1. You are a bot that is good at analyzing images. Please give a description of the image given. The description must be written in traditional Chinese. System: 2.Use traditional Chinese to answer only;"),
        HumanMessage(content=[
            {
                "type": "text", 
                "text": "Describe the contents of this image."
            },
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{base64_image}"
                },
            },
        ])
    ]
    response = ChatOpenAI(model="gpt-4o", max_tokens=1024).invoke(prompt)
    return response.content

# Streamlit UI
st.set_page_config(layout="wide")
st.title("VectorDB Manager")

# User input
root_directory = config.ROOT_DIRECTORY
required_extensions = config.REQUIRED_EXTENSIONS
if "chunk_size" not in st.session_state:
    st.session_state.chunk_size = 220
if "chunk_overlap" not in st.session_state:
    st.session_state.chunk_overlap = 0

modules.sidebar()

# Company selection
company_names = modules.list_companies(root_directory, required_extensions)

list_company = st.multiselect('Company',company_names,company_names[0])

if list_company:
    data = []
    for company in list_company:
        persist_directory = os.path.join(root_directory, company)

        # Display existin files in the selected company folder
        existing_files = modules.list_existing_files(persist_directory)
        for file in existing_files:
            data.append({"公司": company, "文件": file})

    # 將所有文件放入 DataFrame
    df = pd.DataFrame(list(data))
    df["選擇"]= False
    # 顯示表格
    edited_df = st.data_editor(
        df, 
        column_config={
            "公司": st.column_config.Column("公司", disabled=True), 
            "文件": st.column_config.Column("文件", disabled=True), 
            "選擇": "選擇檔案"}, 
        hide_index=True)
    formatted_company = '、'.join(list_company)

st.subheader("extract image")

excel_files = st.file_uploader("選擇 PDF 檔案", type=["pdf"], accept_multiple_files=True)
if excel_files:
    extract_info(excel_files, root_directory, formatted_company, list_company)