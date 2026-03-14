import hashlib
import streamlit as st
from database import db


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def ensure_default_user():
    user = db.fetch_one("SELECT id FROM users LIMIT 1")
    if not user:
        db.execute(
            "INSERT INTO users (email, password_hash, name, role) VALUES (?, ?, ?, ?)",
            ("admin@ims.com", hash_password("admin123"), "Admin User", "Admin"),
        )


def authenticate(email: str, password: str):
    row = db.fetch_one("SELECT * FROM users WHERE email = ?", (email,))
    if not row:
        return None
    return row if row["password_hash"] == hash_password(password) else None


def login_form():
    st.markdown("<div class='login-bg'>", unsafe_allow_html=True)
    with st.container():
        st.markdown("<div class='login-card'>", unsafe_allow_html=True)
        st.markdown("<h2>Inventory Matrix</h2>", unsafe_allow_html=True)
        st.markdown("<p class='muted'>Secure access to your inventory workspace</p>", unsafe_allow_html=True)

        tab_login, tab_signup, tab_reset = st.tabs(["Login", "Sign Up", "Reset Password"])

        with tab_login:
            email = st.text_input("Email", placeholder="you@company.com")
            password = st.text_input("Password", type="password", placeholder="••••••••")
            login_clicked = st.button("Login", use_container_width=True)

            if login_clicked:
                user = authenticate(email, password)
                if user:
                    st.session_state["authenticated"] = True
                    st.session_state["user"] = dict(user)
                    st.success("Login successful")
                    st.experimental_rerun()
                else:
                    st.error("Invalid email or password")

        with tab_signup:
            name = st.text_input("Full Name", placeholder="Alex Morgan")
            new_email = st.text_input("Work Email", placeholder="alex@company.com")
            new_password = st.text_input("Password", type="password", placeholder="Create a password")
            create = st.button("Create Account", use_container_width=True)

            if create:
                if not new_email or not new_password:
                    st.error("Email and password are required")
                else:
                    existing = db.fetch_one("SELECT id FROM users WHERE email = ?", (new_email,))
                    if existing:
                        st.error("Email already exists")
                    else:
                        db.execute(
                            "INSERT INTO users (email, password_hash, name, role) VALUES (?, ?, ?, ?)",
                            (new_email, hash_password(new_password), name, "User"),
                        )
                        st.success("Account created. Please log in.")

        with tab_reset:
            reset_email = st.text_input("Account Email", placeholder="you@company.com")
            send = st.button("Send OTP", use_container_width=True)
            if send:
                if not reset_email:
                    st.error("Enter your email to receive OTP")
                else:
                    st.success("OTP sent (placeholder). Follow the verification flow.")

        st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)


def logout_button():
    if st.button("Logout", use_container_width=True):
        st.session_state.clear()
        st.experimental_rerun()


def require_login():
    if not st.session_state.get("authenticated"):
        login_form()
        st.stop()
