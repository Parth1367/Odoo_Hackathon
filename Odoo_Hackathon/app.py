import streamlit as st
from database import db
from utils import auth
from utils.helpers import load_css

st.set_page_config(page_title="Inventory Management", page_icon="📦", layout="wide")

load_css()
db.init_db()
auth.ensure_default_user()

if st.session_state.get("authenticated"):
    st.switch_page("pages/dashboard.py")

auth.login_form()
