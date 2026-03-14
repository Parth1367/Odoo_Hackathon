import streamlit as st
from utils import auth


def render_sidebar():
    with st.sidebar:
        st.markdown(
            """
            <div class="sidebar-brand">
              <div class="sidebar-logo">IM</div>
              <div>
                <div style="font-weight:700;">Inventory Matrix</div>
                <div class="muted" style="font-size:0.75rem;">Enterprise IMS</div>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.page_link("pages/dashboard.py", label="Dashboard", icon="📊")
        st.page_link("pages/products.py", label="Products", icon="📦")
        st.page_link("pages/receipts.py", label="Receipts", icon="📥")
        st.page_link("pages/deliveries.py", label="Deliveries", icon="🚚")
        st.page_link("pages/transfers.py", label="Transfers", icon="🔁")
        st.page_link("pages/adjustments.py", label="Adjustments", icon="🧮")
        st.page_link("pages/move_history.py", label="Move History", icon="📜")
        st.page_link("pages/settings.py", label="Settings", icon="⚙️")
        st.page_link("pages/profile.py", label="My Profile", icon="👤")

        st.markdown("<div style='height:1rem;'></div>", unsafe_allow_html=True)
        auth.logout_button()
