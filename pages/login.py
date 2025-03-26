import streamlit as st
import psycopg2
import bcrypt
import time
import re  # Import regex for email validation
import smtplib
import random
from email.mime.text import MIMEText
# Streamlit Config
st.set_page_config(page_title="Login", page_icon="🔑", initial_sidebar_state="collapsed")


# Function to connect to PostgreSQL
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
st.title("🔐 Login to ChatDocs")



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


# Sidebar Content
with st.sidebar:
    st.markdown('<div class="sidebar-title">⚡ ChatDocs</div>', unsafe_allow_html=True)

    if st.button("💬 Home Page", use_container_width=True):
        st.switch_page("chatdocs.py")

    # if st.button("⚙️ Login ", use_container_width=True):
    #     st.switch_page("pages/login.py")

    if st.button("🔐 Admin Login", use_container_width=True):
        st.switch_page("pages/admin_login.py")

    # st.markdown("---")  # Divider Line


# Detect if the user is coming from another page
if "current_page" in st.session_state and st.session_state["current_page"] != "login":
    st.session_state.clear()  # Log out the user
    st.success("✅ You have been logged out.")
    time.sleep(2)  # Show the message for 2 seconds
    st.rerun()  # Refresh the page to show the login form

# Track current page
st.session_state["current_page"] = "login"


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
            st.switch_page("pages/chatdocs2.py")
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

