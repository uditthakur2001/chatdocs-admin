import streamlit as st

# ✅ Ensure set_page_config is at the top
# st.set_page_config(page_title="Admin Login", page_icon="👑")
st.set_page_config(page_title="ChatDocs", page_icon="📝", layout="wide")


# Apply custom CSS to hide the default sidebar
st.markdown(
    """
    <style>
        [data-testid="stSidebarNav"] {display: none;} /* Hides default sidebar navigation */
    </style>
    """,
    unsafe_allow_html=True
)
# Custom CSS for a Beautiful Sidebar
st.markdown(
    """
    <style>
        /* Sidebar Styling */
        [data-testid="stSidebar"] {
            background-color: #1E1E1E !important;
            color: white;
            width: 280px !important;
            box-shadow: 2px 0px 10px rgba(255, 255, 255, 0.2);
        }

        /* Sidebar Header */
        .sidebar-title {
            font-size: 22px;
            font-weight: bold;
            text-align: center;
            padding: 15px 0;
            color: white;
        }

        /* Sidebar Buttons */
        .sidebar-item {
            padding: 12px;
            font-size: 16px;
            font-weight: bold;
            color: white;
            text-decoration: none;
            display: block;
            transition: background 0.3s ease;
            border-radius: 5px;
        }
        .sidebar-item:hover {
            background: rgba(255, 255, 255, 0.2);
        }
    </style>
    """,
    unsafe_allow_html=True
)

# Sidebar Content
with st.sidebar:
    st.markdown('<div class="sidebar-title">⚡ ChatDocs</div>', unsafe_allow_html=True)

    if st.button("💬 ChatDocs", use_container_width=True):
        st.switch_page("chatdocs.py")

    # if st.button("⚙️ Admin Panel", use_container_width=True):
    #     st.switch_page("pages/admin_panel.py")

    if st.button("🔐 Admin Login", use_container_width=True):
        st.switch_page("pages/admin_login.py")
        
st.title("👨‍💻 Admin Login")

# Session state to store admin login status
if "admin_logged_in" not in st.session_state:
    st.session_state["admin_logged_in"] = False

# Admin Credentials
ADMIN_CREDENTIALS = {
    "admin": "admin123",  # Example: admin username & password
}

username = st.text_input("Admin Username")
password = st.text_input("Admin Password", type="password")

if st.button("Login"):
    if username in ADMIN_CREDENTIALS and password == ADMIN_CREDENTIALS[username]:
        st.session_state["admin_logged_in"] = True
        st.success("✅ Login successful! Redirecting...")
        st.rerun()  
    else:
        st.error("❌ Invalid credentials")

# Redirect to admin panel if logged in
if st.session_state["admin_logged_in"]:
    st.switch_page("pages/admin_panel.py")  # Redirect to admin panel
