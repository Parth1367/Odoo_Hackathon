import streamlit as st


def render_navbar(title: str, subtitle: str = ""):
    st.markdown(
        f"""
        <div class="navbar fade-up">
          <div style="display:flex;justify-content:space-between;align-items:center;gap:1rem;">
            <div>
              <h2 style="margin:0;">{title}</h2>
              <div class="muted" style="font-size:0.85rem;">{subtitle}</div>
            </div>
            <div class="pill">Live</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
