import streamlit as st

# ✅ Ensure set_page_config is at the top
st.set_page_config(page_title="ChatDocs", page_icon="📝",initial_sidebar_state="collapsed")


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
            transition: background 0.3s ease, box-shadow 0.3s ease;
            min-width: 200px !important;
            max-width: 400px !important;
            box-shadow: 2px 0px 10px rgba(255, 255, 255, 0.2);
            resize: horizontal; /* Allow resizing */
            overflow: auto; /* Prevent content overflow */
        }

        /* Light Theme Sidebar */
        html[data-theme="light"] [data-testid="stSidebar"] {
            background-color: #f8f9fa !important;
            color: black;
            box-shadow: 2px 0px 10px rgba(0, 0, 0, 0.2);
        }

        /* Dark Theme Sidebar */
        html[data-theme="dark"] [data-testid="stSidebar"] {
            background-color: #1E1E1E !important;
            color: white;
            box-shadow: 2px 0px 10px rgba(255, 255, 255, 0.2);
        }

        /* Sidebar Header */
        .sidebar-title {
            font-size: 22px;
            font-weight: bold;
            text-align: center;
            padding: 15px 0;
        }

        /* Light Theme Sidebar Title */
        html[data-theme="light"] .sidebar-title {
            color: black;
        }

        /* Dark Theme Sidebar Title */
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

        /* Light Theme Sidebar Buttons */
        html[data-theme="light"] .sidebar-item {
            color: black;
        }
        html[data-theme="light"] .sidebar-item:hover {
            background: rgba(0, 0, 0, 0.1);
        }

        /* Dark Theme Sidebar Buttons */
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

    if st.button("⚙️ Login Page", use_container_width=True):
        st.switch_page("pages/login.py")

    # if st.button("🔐 Admin Login", use_container_width=True):
    #     st.switch_page("pages/admin_login.py")
        
st.title("👨‍💻 Admin Login")

# Session state to store admin login status
if "admin_logged_in" not in st.session_state:
    st.session_state["admin_logged_in"] = False

# Admin Credentials
ADMIN_CREDENTIALS = {
    "admin": "admin123",  # Example: admin username & password
}

username = st.text_input("Admin Username", placeholder="Enter admin name")
password = st.text_input("Admin Password", type="password", placeholder="Enter admin password")

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
