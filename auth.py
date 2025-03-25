import streamlit as st

# Dummy Admin Credentials (Replace with Database Authentication)
ADMIN_CREDENTIALS = {"admin": "admin123"}

def authenticate_admin(username, password):
    return ADMIN_CREDENTIALS.get(username) == password  # Check credentials

def is_admin_logged_in():
    return st.session_state.get("admin_logged_in", False)

def logout_admin():
    st.session_state["admin_logged_in"] = False
