# vectorstore_manager

`vectorstore_manager` 是一款基於 Streamlit 和 ChromaDB 的向量存儲管理工具，旨在提供直觀的用戶界面來管理和查詢向量資料庫。

## 功能特性

- **用戶友好的界面**：利用 Streamlit 提供直觀的 Web 界面，方便用戶與向量資料庫進行互動。
- **高效的向量存儲**：通過ChromaDB，確保向量資料的高效存儲和檢索。

## 安裝步驟

```bash

git clone https://github.com/brian111168/vectorstore_manager.git

cd vectorstore_manager

pip install -r requirements.txt
```
## 設置環境變數（.env）
#### vectorstore_manager 使用 .env 來存儲環境變數，請按照以下步驟設置：

```bash
cp .env_example .env
```
#### 設定.env 中的內容
```bash
LANGCHAIN_TRACING_V2=true
LANGCHAIN_ENDPOINT=https://api.smith.langchain.com
LANGCHAIN_API_KEY=
LANGCHAIN_PROJECT=

OPENAI_API_KEY=
```
## 使用方法
```bash
streamlit run vectorstore_manage.py
```

