import streamlit as st
import psycopg2
import time

# 🔹 PostgreSQL Database Connection
def connect_db():
    return psycopg2.connect(
        dbname=st.secrets["database"]["DB_NAME"],
        user=st.secrets["database"]["DB_USER"],
        password=st.secrets["database"]["DB_PASSWORD"],
        host=st.secrets["database"]["DB_HOST"],
        port=st.secrets["database"]["DB_PORT"]
    )
# Function to fetch all users in uppercase
def fetch_users():
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, UPPER(username) FROM users")  # Convert to uppercase
    users = cursor.fetchall()
    conn.close()
    return users

# Function to get total user count
def get_user_count():
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users")
    user_count = cursor.fetchone()[0]
    conn.close()
    return user_count

# Function to delete a user
def delete_user(user_id):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
    conn.commit()
    conn.close()
    st.success(f"✅ User with ID {user_id} deleted successfully!")
    st.rerun()  # Refresh the page to update the user list

# Hide sidebar & apply custom styling
st.set_page_config(page_title="Admin Panel", page_icon="⚙️", layout="wide")

st.markdown(
    """
    <style>
        /* Hide Sidebar */
        [data-testid="stSidebar"] {display: none;}

        /* Navigation Button */
        .nav-button {
            border: none;
            font-size: 16px;
            cursor: pointer;
            font-weight: bold;
            margin-top: 5rem;
            padding: 12px 25px;
            border-radius: 8px;
            transition: all 0.3s ease;
        }

        /* Light Theme Button */
        html[data-theme="light"] .nav-button {
            background: white;
            color: black;
        }
        html[data-theme="light"] .nav-button:hover {
            background: rgba(0, 0, 0, 0.1);
        }
        html[data-theme="light"] .active {
            background: rgba(0, 0, 0, 0.2);
        }

        /* Dark Theme Button */
        html[data-theme="dark"] .nav-button {
            background: #1E1E1E;
            color: white;
        }
        html[data-theme="dark"] .nav-button:hover {
            background: rgba(255, 255, 255, 0.2);
        }
        html[data-theme="dark"] .active {
            background: rgba(255, 255, 255, 0.3);
        }

        /* Dashboard Card */
        .dashboard-card {
            padding: 20px;
            border-radius: 10px;
            text-align: center;
            font-size: 18px;
            font-weight: bold;
            transition: all 0.3s ease;
        }

        /* Light Theme Dashboard */
        html[data-theme="light"] .dashboard-card {
            background: #f8f9fa;
            color: black;
            box-shadow: 2px 2px 10px rgba(0, 0, 0, 0.1);
        }

        /* Dark Theme Dashboard */
        html[data-theme="dark"] .dashboard-card {
            background: #292b2c;
            color: white;
            box-shadow: 2px 2px 10px rgba(255, 255, 255, 0.1);
        }

        /* User Card */
        .user-card {
            padding: 15px;
            border-radius: 10px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
            transition: all 0.3s ease;
        }

        /* Light Theme User Card */
        html[data-theme="light"] .user-card {
            background: white;
            color: black;
            box-shadow: 2px 2px 10px rgba(0, 0, 0, 0.1);
        }

        /* Dark Theme User Card */
        html[data-theme="dark"] .user-card {
            background: #333;
            color: white;
            box-shadow: 2px 2px 10px rgba(255, 255, 255, 0.1);
        }

        /* Delete Button */
        .delete-btn {
            border: none;
            padding: 8px 12px;
            border-radius: 6px;
            cursor: pointer;
            transition: background 0.3s ease;
        }

        /* Light Theme Delete Button */
        html[data-theme="light"] .delete-btn {
            background: red;
            color: white;
        }
        html[data-theme="light"] .delete-btn:hover {
            background: darkred;
        }

        /* Dark Theme Delete Button */
        html[data-theme="dark"] .delete-btn {
            background: darkred;
            color: white;
        }
        html[data-theme="dark"] .delete-btn:hover {
            background: red;
        }
    </style>
    """,
    unsafe_allow_html=True
)


# Ensure session state exists
if "admin_logged_in" not in st.session_state:
    st.session_state["admin_logged_in"] = False
if "current_page" not in st.session_state:
    st.session_state["current_page"] = "home"  # Default to home page

# Redirect to login page if not logged in
if not st.session_state["admin_logged_in"]:
    st.warning("⚠️ Unauthorized Access! Redirecting to login...")
    time.sleep(2)
    st.switch_page("pages/admin_login.py")
    st.stop()


col1, col_space1, col2, col_space2, col3 = st.columns([1, 2.5, 1, 2.5, 1])  # Adding gaps between columns

with col1:
    if st.button("🏠 Home", key="home", help="Go to Home", use_container_width=True):
        st.session_state["current_page"] = "home"
        st.rerun()

with col2:
    if st.button("👥 Manage Users", key="users", help="View & Delete Users", use_container_width=True):
        st.session_state["current_page"] = "users"
        st.rerun()

with col3:
    if st.button("🚪 Logout", key="logout", help="Log Out", use_container_width=True):
        st.session_state["admin_logged_in"] = False
        st.session_state.clear()
        # st.success("✅ You have been logged out. Redirecting to login...")
        time.sleep(2)
        st.switch_page("pages/admin_login.py")
        st.stop()

st.markdown('</div>', unsafe_allow_html=True)

# Render Different Pages Based on Session State
if st.session_state["current_page"] == "home":
    st.title("⚙️ Admin Panel")
    st.subheader("Welcome to the Admin Dashboard")

    # Dashboard Stats
    user_count = get_user_count()
    col1, col_space, col2 = st.columns([1, 0.2, 1])  # Spacing between dashboard cards

    with col1:
        st.markdown('<div class="dashboard-card">👥 Total Users: ' + str(user_count) + '</div>', unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="dashboard-card">📂 Recent Activity: No new updates</div>', unsafe_allow_html=True)

    st.markdown("---")

    # Quick Links
    st.subheader("Quick Actions 🚀")
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("➕ Add New User", use_container_width=True):
            st.warning("⚠️ Feature Not Implemented Yet!")

    with col2:
        if st.button("📋 View User List", use_container_width=True):
            st.session_state["current_page"] = "users"
            st.rerun()

    with col3:
        if st.button("🔄 Refresh Dashboard", use_container_width=True):
            st.rerun()

elif st.session_state["current_page"] == "users":
    st.title("👥 Manage Users")
    st.subheader("User List")

    users = fetch_users()

    if not users:
        st.info("No users found.")
    else:
        for user in users:
            user_id, username = user
            col1, col2 = st.columns([4, 1])
            col1.markdown(f'<div class="user-card"><strong>{username}</strong></div>', unsafe_allow_html=True)
            if col2.button("🗑️ Delete", key=user_id, help="Delete User", use_container_width=True):
                delete_user(user_id)
