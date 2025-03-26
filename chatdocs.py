# ======================= Import Section =======================
import streamlit as st
import psycopg2
import bcrypt
import os
import time
import re  # Import regex for email validation
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
import smtplib
import random
from email.mime.text import MIMEText


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

# ======================= Email Handling =======================

# 🔹 Fetch Email Credentials from Streamlit Secrets
def get_email_credentials():
    sender_email = st.secrets["email"]["SENDER_EMAIL"]
    sender_password = st.secrets["email"]["SENDER_PASSWORD"]
    return sender_email, sender_password

def send_reset_email(email, otp):
    try:
        sender_email, sender_password = get_email_credentials()
        msg = MIMEText(f"Your password reset OTP is: {otp}")
        msg["Subject"] = "Password Reset Code"
        msg["From"] = sender_email
        msg["To"] = email

        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, email, msg.as_string())

        return True
    except smtplib.SMTPAuthenticationError:
        st.error("❌ Email authentication failed. Check your credentials.")
    except smtplib.SMTPException as e:
        st.error(f"❌ Error sending email: {e}")
    return False

def forgot_password(email):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE email=%s", (email,))
    user = cursor.fetchone()

    if user:
        otp = random.randint(100000, 999999)
        st.session_state["reset_otp"] = otp
        st.session_state["reset_email"] = email
        if send_reset_email(email, otp):
            return True
        else:
            return False
    return False

# 🔹 Reset Password Function
def reset_password(email, otp, new_password):
    if "reset_otp" in st.session_state and "reset_email" in st.session_state:
        if st.session_state["reset_otp"] == otp and st.session_state["reset_email"] == email:
            hashed_pw = hash_password(new_password)
            conn = connect_db()
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET password=%s WHERE email=%s", (hashed_pw, email))
            conn.commit()
            cursor.close()
            conn.close()
            return True
    return False


# ======================= Authentication Section =======================

# 🔹 Hash Passwords
def hash_password(password):
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

def check_password(plain_password, hashed_password):
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))

# 🔹 Validate User Login
def validate_user(username, password):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, password FROM users WHERE username=%s", (username,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()
    if user and check_password(password, user[1]):
        return user[0]
    return None

# 🔹 Register User
def register_user(username, email, password):
    # 🔹 Validate Email (Must End with @gmail.com)
    if not email.endswith("@gmail.com"):
        return "❌ Invalid email! Only Gmail accounts (@gmail.com) are allowed."

    # 🔹 Validate Password (Cannot Be Empty)
    if not password.strip():
        return "❌ Password cannot be empty!"

    hashed_pw = hash_password(password)
    conn = connect_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            "INSERT INTO users (username, email, password) VALUES (%s, %s, %s)", 
            (username, email, hashed_pw)
        )
        conn.commit()
        return "✅ Registration successful!"
    except psycopg2.IntegrityError:
        return "❌ Email already registered!"
    finally:
        cursor.close()
        conn.close()


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
            width: 380px !important;
            transition: background-color 0.3s ease, color 0.3s ease;
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


# Sidebar Content
with st.sidebar:
    st.markdown('<div class="sidebar-title">⚡ ChatDocs</div>', unsafe_allow_html=True)

    if st.button("💬 Home Page", use_container_width=True):
        st.switch_page("chatdocs.py")

    # if st.button("⚙️ Admin Panel", use_container_width=True):
    #     st.switch_page("pages/admin_panel.py")

    if st.button("🔐 Admin Login", use_container_width=True):
        st.switch_page("pages/admin_login.py")

    st.markdown("---")  # Divider Line


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
        st.rerun()  # Refresh the page

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

# ======================= Login UI Page =======================

# Initialize session state
if "auth_mode" not in st.session_state:
    st.session_state["auth_mode"] = "Login"
if "redirect_triggered" not in st.session_state:
    st.session_state["redirect_triggered"] = False

def switch_to_login():
    """Force switch to login mode"""
    st.session_state["auth_mode"] = "Login"
    st.session_state["redirect_triggered"] = True  # Trigger rerun
    st.rerun()

# ✅ **Login Form**
def login_form():
    st.subheader("🔑 Login")
    username = st.text_input("Username", placeholder="Enter your username")
    password = st.text_input("Password", type="password", placeholder="Enter your password")
    
    if st.button("Login"):
        user_id = validate_user(username, password)
        if user_id:
            st.session_state["user_id"] = user_id
            st.session_state["username"] = username
            st.success("✅ Login successful!")
            st.rerun()
        else:
            st.error("❌ Invalid username or password")

    st.button("Sign Up", on_click=lambda: st.session_state.update(auth_mode="Sign Up"))
    st.button("Forgot Password", on_click=lambda: st.session_state.update(auth_mode="Forgot Password"))

# ✅ **Sign Up Form**
def signup_form():
    st.subheader("🆕 Sign Up")
    new_username = st.text_input("New Username",placeholder="Enter your username")
    email = st.text_input("Email Id",placeholder="Enter your email id")
    new_password = st.text_input("New Password", type="password",placeholder="Enter your password")

    if st.button("Sign Up"):
        if not new_username.strip():
            st.error("❌ Username cannot be empty!")
        elif not re.match(r"^[a-zA-Z][a-zA-Z0-9_ ]*$", new_username):
            st.error("❌ Username must start with a letter and can contain only letters, numbers, and underscores!")
        elif not re.match(r"^[a-zA-Z0-9._%+-]+@gmail\.com$", email):
            st.error("❌ Invalid email! Please enter a valid Gmail address (e.g., example@gmail.com).")
        elif not new_password.strip():
            st.error("❌ Password cannot be empty!")
        elif len(new_password) < 4:
            st.error("❌ Password must be at least 4 characters long!")
        else:
            result = register_user(new_username, email, new_password)
            if result == "✅ Registration successful!":
                st.success("✅ Account created! Redirecting to login...")
                time.sleep(1)
                switch_to_login()

    st.button("Back to Login", on_click=lambda: st.session_state.update(auth_mode="Login"))

# ✅ **Forgot Password Form**
def forgot_password_form():
    st.subheader("🔄 Forgot Password")
    email = st.text_input("Registered Email Id",placeholder="Enter your registered email")
    
    if st.button("Send OTP"):
        if forgot_password(email):
            st.success("✅ OTP sent to your email. (Please check your spam folder as well!)")
        else:
            st.error("❌ Email not found.")

    otp = st.text_input("OTP",placeholder="Enter the received otp")
    new_password = st.text_input("Password", type="password",placeholder="Enter new password")

    if st.button("Reset Password"):
        if not email.strip():  
            st.error("❌ Please enter the Email id.")   
        if not otp.strip():  
            st.error("❌ Please enter the OTP.")  
        elif not otp.strip().isdigit():  
            st.error("❌ Invalid OTP. Please enter a valid numeric OTP.")  
        elif not new_password.strip():  
            st.error("❌ Please enter a new password.")  
        else:  
            if reset_password(email, int(otp), new_password):  
                st.success("✅ Password reset successful! Redirecting to login...") 
                time.sleep(1)
                switch_to_login() 
            else:  
                st.error("❌ Invalid OTP or email.")  
    st.button("Back to Login", on_click=lambda: st.session_state.update(auth_mode="Login"))

# ✅ **Render the selected form**
if not st.session_state.get("user_id"):
    col1, col2 = st.columns([2, 3])
    with col1:
        if st.session_state["auth_mode"] == "Login":
            login_form()
        elif st.session_state["auth_mode"] == "Sign Up":
            signup_form()
        elif st.session_state["auth_mode"] == "Forgot Password":
            forgot_password_form()

    if st.session_state["redirect_triggered"]:
        st.session_state["redirect_triggered"] = False  # Reset flag
        st.rerun()  # Force UI refresh

    st.stop()


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
user_question = st.text_input("Your Question")
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