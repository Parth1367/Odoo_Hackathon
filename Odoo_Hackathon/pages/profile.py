import streamlit as st
from database import db
from utils import auth
from utils.helpers import load_css
from components.sidebar import render_sidebar
from components.navbar import render_navbar

st.set_page_config(page_title="My Profile", page_icon="👤", layout="wide")
load_css()
db.init_db()
auth.require_login()
render_sidebar()

render_navbar("My Profile", "Update your profile details")

user = st.session_state.get("user") or {}

st.markdown("<div class='glass-card fade-up'>", unsafe_allow_html=True)
st.markdown("<h3>Profile Details</h3>", unsafe_allow_html=True)

col1, col2 = st.columns(2)
with col1:
    name = st.text_input("Full Name", value=user.get("name", ""))
with col2:
    email = st.text_input("Email", value=user.get("email", ""))

role = user.get("role", "User")
st.text_input("Role", value=role, disabled=True)

if st.button("Save Changes"):
    if not email:
        st.error("Email is required")
    else:
        db.execute("UPDATE users SET name = ?, email = ? WHERE id = ?", (name, email, user.get("id")))
        st.session_state["user"] = {**user, "name": name, "email": email}
        st.success("Profile updated")

st.markdown("</div>", unsafe_allow_html=True)
