import streamlit as st
from database import db
from utils import auth
from utils.helpers import load_css, ensure_warehouse, ensure_location
from components.sidebar import render_sidebar
from components.navbar import render_navbar

st.set_page_config(page_title="Settings", page_icon="⚙️", layout="wide")
load_css()
auth.require_login()
render_sidebar()

render_navbar("Settings", "Manage warehouses, locations, and system configuration")

st.markdown("<div class='glass-card fade-up'>", unsafe_allow_html=True)
st.markdown("<h3>Warehouse Management</h3>", unsafe_allow_html=True)

with st.form("warehouse_form"):
    col1, col2 = st.columns(2)
    with col1:
        warehouse_name = st.text_input("Warehouse Name", placeholder="Central DC")
    with col2:
        region = st.text_input("Region", placeholder="Midwest")
    add_wh = st.form_submit_button("Add Warehouse")

    if add_wh:
        if warehouse_name:
            ensure_warehouse(warehouse_name, region)
            st.success("Warehouse saved")
        else:
            st.error("Warehouse name is required")

st.markdown("</div>", unsafe_allow_html=True)

st.markdown("<div class='glass-card fade-up' style='margin-top:1rem;'>", unsafe_allow_html=True)
st.markdown("<h3>Location Management</h3>", unsafe_allow_html=True)

warehouses = db.fetch_all("SELECT id, name FROM warehouses ORDER BY name")
wh_map = {w["name"]: w["id"] for w in warehouses}

with st.form("location_form"):
    warehouse_choice = st.selectbox("Warehouse", list(wh_map.keys()) if wh_map else ["No warehouses"])
    location_name = st.text_input("Location Name", placeholder="Rack A")
    add_loc = st.form_submit_button("Add Location")

    if add_loc:
        if not wh_map:
            st.error("Add a warehouse first")
        elif location_name:
            ensure_location(wh_map[warehouse_choice], location_name)
            st.success("Location saved")
        else:
            st.error("Location name is required")

st.markdown("</div>", unsafe_allow_html=True)

st.markdown("<div class='glass-card table-card fade-up' style='margin-top:1rem;'>", unsafe_allow_html=True)
st.markdown("<h3>Warehouses & Locations</h3>", unsafe_allow_html=True)

rows = db.fetch_all(
    """
    SELECT w.name AS warehouse, w.region, l.name AS location
    FROM warehouses w
    LEFT JOIN locations l ON l.warehouse_id = w.id
    ORDER BY w.name, l.name
    """
)

if rows:
    table_rows = "".join(
        f"<tr><td>{r['warehouse']}</td><td>{r['region'] or ''}</td><td>{r['location'] or ''}</td></tr>"
        for r in rows
    )
    table = f"""
    <table>
      <thead><tr><th>Warehouse</th><th>Region</th><th>Location</th></tr></thead>
      <tbody>{table_rows}</tbody>
    </table>
    """
    st.markdown(table, unsafe_allow_html=True)
else:
    st.info("No warehouses configured yet.")

st.markdown("</div>", unsafe_allow_html=True)
