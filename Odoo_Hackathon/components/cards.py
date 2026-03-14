import streamlit as st


def kpi_card(title: str, value: str, note: str = ""):
    st.markdown(
        f"""
        <div class="glass-card kpi-card fade-up">
          <div class="kpi-title">{title}</div>
          <div class="kpi-value count">{value}</div>
          <div class="muted" style="font-size:0.8rem;">{note}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
