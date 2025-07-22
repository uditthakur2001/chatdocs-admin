# 📁 ChatDocs Admin Panel

**ChatDocs Admin** is the admin interface for managing uploaded documents and monitoring user interactions in the [ChatDocs](https://chatdocs-ai.streamlit.app/) document-based Q&A chatbot. Built with **Streamlit**, this panel enables admins to handle file uploads, manage user-specific document history, and store chat and file metadata using **PostgreSQL (Neon DB)** and **FAISS** for semantic search.

---

## 🔗 Live Apps

- 💬 ChatDocs : [https://chatdocs-app.streamlit.app/](https://chatdocs-ai.streamlit.app/)

---

## ✨ Features

- ✅ Upload and manage documents (PDF, Word, Excel, CSV, TXT)
- ✅ View and manage user-specific chat history
- ✅ PostgreSQL (Neon DB) used for persistent storage
- ✅ FAISS vector database for document embedding and semantic search
- ✅ Google Gemini AI for answering document-based queries
- ✅ Admin-friendly, Streamlit-based UI

---

## 🛠 Tech Stack

| Layer             | Technology                |
|-------------------|----------------------------|
| 🧠 AI Model        | Google Gemini AI           |
| 🗃 Vector DB       | FAISS                      |
| 🗄️ Relational DB   | PostgreSQL (Neon DB)       |
| 💻 Backend         | Python (Streamlit)         |
| ☁ Hosting         | Streamlit Cloud            |
| 📁 File Handling   | JSON + Local file storage  |

---

## 📁 Project Structure

chatdocs-admin/
├── assets/ # Images and branding

├── data/ # Local documents and temporary JSONs

├── pages/ # Multi-page components for Streamlit

├── utils/ # Utility functions (DB, FAISS, etc.)

├── main.py # Main Streamlit app entry point

├── requirements.txt # Python dependencies

└── README.md # Project documentation

yaml
Copy
Edit

---

## 🚀 Getting Started

Follow these steps to run the project locally:

### 1. Clone the repository

```bash
git clone https://github.com/uditthakur2001/chatdocs-admin.git
cd chatdocs-admin
```

### 2. (Optional) Create a virtual environment

```bash
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate
```

### 3. Install required dependencies

```bash
pip install -r requirements.txt
```

### 4. Set up environment variables
Create a .env file in the root directory and add your DB credentials:

```bash
POSTGRES_HOST=your_neon_host
POSTGRES_DB=your_database_name
POSTGRES_USER=your_username
POSTGRES_PASSWORD=your_password
POSTGRES_PORT=5432
```
### 5. Run the application

```bash
streamlit run main.py
```

## 🧠 How It Works
Admin uploads documents via the UI.

Metadata and chat history are stored in PostgreSQL (Neon DB).

Semantic embeddings are generated with FAISS.

Google Gemini AI handles user queries based on vector search results.

Document and user records are searchable and editable via the admin interface.

## 📌 Roadmap
 Admin authentication system

 Document versioning and tagging

 Activity analytics and user stats

 Integration with cloud object storage (S3, GCS, etc.)

## 🙋‍♂️ Author
Made by Udit Raj Singh

Helping users interact with their documents using AI-powered Q&A.

If this project helped you, consider starring ⭐ the repo!

