# ======================= Import Section =======================
import streamlit as st
import psycopg2
import os
import time
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
# from langchain.vectorstores import FAISS    #use this for local
from langchain_community.vectorstores import FAISS    # type: ignore     #use this for deploying on streamlit and remove type ignore
from langchain.chains.question_answering import load_qa_chain
from langchain.prompts import PromptTemplate
from PyPDF2 import PdfReader
import pandas as pd
from io import StringIO
from docx import Document

# ======================= Streamlit Config, API & PostgreSQL Database Connection =======================

st.set_page_config(page_title="ChatDocs", page_icon="📝")
st.title("📝 ChatDocs")

# 🔹 Load API Key from Streamlit Secrets
os.environ["GOOGLE_API_KEY"] = st.secrets["general"]["GOOGLE_API_KEY"]

# 🔹 PostgreSQL Database Connection
def connect_db():
    return psycopg2.connect(
        dbname=st.secrets["database"]["DB_NAME"],
        user=st.secrets["database"]["DB_USER"],
        password=st.secrets["database"]["DB_PASSWORD"],
        host=st.secrets["database"]["DB_HOST"],
        port=st.secrets["database"]["DB_PORT"]
    )


# ======================= Delete Chat =======================

# 🔹 Delete Chat History Function
def delete_chat_history(user_id):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM chat_history WHERE user_id = %s", (user_id,))
    conn.commit()
    cursor.close()
    conn.close()

# 🔹 Function to Delete Chat History for a Specific PDF
def delete_chat_history_pdf(user_id, pdf_name):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM chat_history WHERE user_id = %s AND pdf_name = %s", (user_id, pdf_name))
    conn.commit()
    cursor.close()
    conn.close()


# ======================= User Account Management =======================

# 🔹 Delete User Account
def delete_account(user_id):
    try:
        with connect_db() as conn:
            with conn.cursor() as cursor:
                cursor.execute("DELETE FROM chat_history WHERE user_id = %s", (user_id,))
                cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
            conn.commit()
        return True
    except Exception as e:
        st.error(f"❌ Error deleting account: {e}")
        return False

def get_admin_username(user_id):
    """Fetch the admin's username from the users table."""
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT username FROM users WHERE id = %s", (user_id,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()
    
    return user[0].upper() if user else None

# 🔹 User Session Management
if "user_id" not in st.session_state:
    st.session_state["user_id"] = None


# ======================= Sidebar Chat History =======================

# Apply custom CSS to hide the default sidebar
st.markdown(
    """
    <style>
        [data-testid="stSidebarNav"] {display: none;} /* Hides default sidebar navigation */
    </style>
    """,
    unsafe_allow_html=True
)

st.markdown(
    """
    <style>
        /* Sidebar Styling */
        [data-testid="stSidebar"] {
            transition: background-color 0.3s ease, color 0.3s ease;
            min-width: 200px !important;
            max-width: 400px !important;
            box-shadow: 2px 0px 10px rgba(255, 255, 255, 0.2);
            resize: horizontal; /* Allow resizing */
            overflow: auto; /* Prevent content overflow */
        }

        /* Adjust Sidebar Based on Theme */
        html[data-theme="light"] [data-testid="stSidebar"] {
            background-color: #f8f9fa !important; /* Light Gray */
            color: black !important;
            box-shadow: 2px 0px 10px rgba(0, 0, 0, 0.2);
        }
        html[data-theme="dark"] [data-testid="stSidebar"] {
            background-color: #1E1E1E !important; /* Dark Mode */
            color: white !important;
            box-shadow: 2px 0px 10px rgba(255, 255, 255, 0.2);
        }

        /* Sidebar Header */
        .sidebar-title {
            font-size: 22px;
            font-weight: bold;
            text-align: center;
            padding: 15px 0;
        }

        /* Light Theme Sidebar Header */
        html[data-theme="light"] .sidebar-title {
            color: black;
        }

        /* Dark Theme Sidebar Header */
        html[data-theme="dark"] .sidebar-title {
            color: white;
        }

        /* Sidebar Buttons */
        .sidebar-item {
            padding: 12px;
            font-size: 16px;
            font-weight: bold;
            text-decoration: none;
            display: block;
            transition: background 0.3s ease, color 0.3s ease;
            border-radius: 5px;
        }

        /* Light Theme Buttons */
        html[data-theme="light"] .sidebar-item {
            color: black;
        }
        html[data-theme="light"] .sidebar-item:hover {
            background: rgba(0, 0, 0, 0.1);
        }

        /* Dark Theme Buttons */
        html[data-theme="dark"] .sidebar-item {
            color: white;
        }
        html[data-theme="dark"] .sidebar-item:hover {
            background: rgba(255, 255, 255, 0.2);
        }
    </style>
    """,
    unsafe_allow_html=True
)


st.session_state["current_page"] = "chatdocs"

st.sidebar.title("📜 Chat History")

if st.session_state["user_id"]:
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT pdf_name FROM chat_history WHERE user_id = %s", (st.session_state["user_id"],))
    pdfs = cursor.fetchall()
    cursor.close()
    conn.close()

    if pdfs:
        selected_pdf = st.sidebar.selectbox(
            "Select a Document",  # Keep a valid label
            [pdf[0] for pdf in pdfs],
            label_visibility="collapsed"  # Hides the label but avoids warnings
        )

        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT question, answer, timestamp FROM chat_history WHERE user_id = %s AND pdf_name = %s ORDER BY timestamp DESC",
            (st.session_state["user_id"], selected_pdf),
        )
        chats = cursor.fetchall()
        cursor.close()
        conn.close()
        

        if chats:
            for chat in chats:
                st.sidebar.write(f" **Q:** {chat[0]}")
                st.sidebar.write(f" **A:** {chat[1]}")
                st.sidebar.write("---")
        else:
            st.sidebar.info("No chats found for this PDF.")

        # 🔹 Show Delete Chat History for Selected PDF only if `selected_pdf` exists
        if st.sidebar.button(f"🗑️ Delete Chat for '{selected_pdf}'"):
            delete_chat_history_pdf(st.session_state["user_id"], selected_pdf)
            st.sidebar.success(f"✅ Chat history for '{selected_pdf}' deleted!")
            st.rerun()
    else:
        st.sidebar.info("No chat history found.")

    # 🔹 Always show "Delete All Chat History" button
    if pdfs and st.sidebar.button("🗑️ Delete All Chat History"):
        delete_chat_history(st.session_state["user_id"])
        st.sidebar.success("✅ Chat history deleted!")
        st.rerun()

else:
    st.sidebar.info("🔑 Please log in to see your chat history.")


# ======================= Logout & Delete Account =======================

# Check if user is logged in
if "user_id" in st.session_state and st.session_state["user_id"]:
    admin_name = get_admin_username(st.session_state["user_id"])
    st.session_state["admin_name"] = admin_name  # Store in session

    st.markdown(
    """
    <style>
        /* Admin Name Styling */
        .admin-name {
            font-size: 18px;
            font-weight: bold;
        }

        /* Button Styling (Light & Dark Theme) */
        .stButton > button {
            border-radius: 5px;
            border: none;
            padding: 6px 12px;
            font-weight: bold;
            cursor: pointer;
            transition: background 0.3s ease, color 0.3s ease;
        }

        /* Adjust based on theme */
        [data-testid="stAppViewContainer"] {
            transition: background-color 0.3s ease, color 0.3s ease;
        }

        /* Light Theme */
        html[data-theme="light"] .stButton > button {
            background-color: #ffffff;
            color: black;
            border: 1px solid #ccc;
        }
        html[data-theme="light"] .stButton > button:hover {
            background-color: #f0f0f0;
        }

        /* Dark Theme */
        html[data-theme="dark"] .stButton > button {
            background-color: #333;
            color: white;
            border: 1px solid #555;
        }
        html[data-theme="dark"] .stButton > button:hover {
            background-color: #444;
        }
    </style>
    """,
    unsafe_allow_html=True
)


    # Create a row layout with admin name + buttons on the right
    col1, col2 = st.columns([10, 2])  # Adjust column width to push right

    with col1:
        st.markdown("")  # Empty space to push items right

    with col2:
        st.markdown(f'<p class="admin-name">👤 {admin_name.upper()}</p>', unsafe_allow_html=True)
        delete_acc = st.button("🗑️ Delete Account")
        logout = st.button("🚪 Logout")

    # Handle button actions
    if delete_acc:
        delete_account(st.session_state["user_id"])  # Define this function
        st.session_state.clear()  # Clear session
        st.success("✅ Your account has been deleted.")
        st.rerun()


    if logout:
        st.session_state.clear()  # Clear session
        st.success("✅ You have been logged out.")
        time.sleep(2)  # Wait for 2 seconds to show the message
        st.switch_page("chatdocs.py") 

# 🔹 Center Login Form and Make it Full Width
st.markdown(
    """
    <style>
        .block-container {
            max-width: 100% !important;
            padding: 2rem;
        }
    </style>
    """,
    unsafe_allow_html=True
)


# ======================= Extraction of text =======================

# 🔹 Extract Text from PDF
def extract_text_from_pdf(uploaded_file):
    reader = PdfReader(uploaded_file)
    text = "\n".join(page.extract_text() for page in reader.pages if page.extract_text())
    return text

def extract_text_from_docx(uploaded_file):
    doc = Document(uploaded_file)
    return "\n".join([para.text for para in doc.paragraphs])

def extract_text_from_csv(uploaded_file):
    df = pd.read_csv(uploaded_file)
    return df.to_string()

def extract_text_from_xlsx(uploaded_file):
    df = pd.read_excel(uploaded_file)
    return df.to_string()

def extract_text_from_txt(uploaded_file):
    return StringIO(uploaded_file.getvalue().decode("utf-8")).read()


# ======================= File Upload Section =======================

uploaded_file = st.file_uploader("📂 Upload a document", type=["pdf", "docx", "csv", "xlsx", "txt"])

if uploaded_file is None:
    st.warning("⚠️ Please upload a document to proceed.")
    st.stop()

file_type = uploaded_file.type
if "pdf" in file_type:
    document_text = extract_text_from_pdf(uploaded_file)
elif "word" in file_type or "docx" in uploaded_file.name:
    document_text = extract_text_from_docx(uploaded_file)
elif "csv" in file_type:
    document_text = extract_text_from_csv(uploaded_file)
elif "excel" in file_type or "xlsx" in uploaded_file.name:
    document_text = extract_text_from_xlsx(uploaded_file)
elif "text" in file_type or "txt" in uploaded_file.name:
    document_text = extract_text_from_txt(uploaded_file)
else:
    st.error("❌ Unsupported file type.")
    st.stop()


# ======================= Faiss operations & QnA =======================

# 🔹 Text Splitting & Embedding
text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
texts = text_splitter.split_text(document_text)

embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
vector_store = FAISS.from_texts(texts, embeddings)

# 🔹 Question Answering
st.subheader("Ask a Question from the Docs:")

# Function to process the question using Google Gemini AI
def process_question(question):
    # Replace this with your Gemini API call
    return question  # Placeholder response

# ======================= Predefined Questions for PDFs =======================

predefined_questions = [
    "What is the main topic of this document?",
    "Summarize this document.",
    "List the key points discussed in this document.",
    "Are there any conclusions or recommendations in this document?",
    "Who is the author of this document?",
    "What are the important dates mentioned in this document?",
    "Explain the methodology used in this document."
]

# st.subheader("🔹 Quick Questions") 
selected_question = st.radio("Select a question:", predefined_questions, index=None)

# Custom question input
custom_question = st.text_input("Or type your own question:")

# Determine which question to process
user_question = custom_question if custom_question.strip() else selected_question

if user_question:
    response = process_question(user_question)  # Calls the function to get an answer
    st.write("💡 Question:", response)

if user_question:
    docs = vector_store.similarity_search(user_question)
    llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash")
    chain = load_qa_chain(llm, chain_type="stuff")
    answer = chain.run(input_documents=docs, question=user_question)

    # 🔹 Display Answer
    st.write("💡 **Answer:**", answer)

    # 🔹 Save Q&A to Database
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO chat_history (user_id, pdf_name, question, answer) VALUES (%s, %s, %s, %s)",
        (st.session_state["user_id"], uploaded_file.name, user_question, answer),
    )
    conn.commit()
    cursor.close()
    conn.close()