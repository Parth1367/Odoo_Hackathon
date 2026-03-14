import streamlit as st
from database import db
from utils import auth
from utils.helpers import load_css
from components.sidebar import render_sidebar
from components.navbar import render_navbar

st.set_page_config(page_title="Move History", page_icon="📜", layout="wide")
load_css()
db.init_db()
auth.ensure_default_user()
auth.require_login()
render_sidebar()

render_navbar("Move History", "Unified stock ledger across all operations")

col1, col2, col3, col4 = st.columns(4)
with col1:
    doc_filter = st.selectbox("Document Type", ["All", "Receipt", "Delivery", "Internal", "Adjustment"])
with col2:
    status_filter = st.selectbox("Status", ["All", "Draft", "Waiting", "Ready", "Done", "Canceled"])
with col3:
    warehouse_filter = st.selectbox(
        "Warehouse",
        ["All"] + [w["name"] for w in db.fetch_all("SELECT name FROM warehouses ORDER BY name")],
    )
with col4:
    search = st.text_input("Search SKU/Product", placeholder="Search by product name")

query = """
    SELECT m.created_at, p.name, p.sku, p.category, m.document_type, m.movement_type, m.quantity, m.reference, m.status,
           w.name AS warehouse, l.name AS location
    FROM inventory_movements m
    JOIN products p ON m.product_id = p.id
    LEFT JOIN locations l ON m.location_id = l.id
    LEFT JOIN warehouses w ON l.warehouse_id = w.id
    WHERE 1=1
"""
params = []

if doc_filter != "All":
    query += " AND m.document_type = ?"
    params.append(doc_filter)
if status_filter != "All":
    query += " AND m.status = ?"
    params.append(status_filter)
if warehouse_filter != "All":
    query += " AND w.name = ?"
    params.append(warehouse_filter)
if search:
    query += " AND (p.name LIKE ? OR p.sku LIKE ?)"
    params.extend([f"%{search}%", f"%{search}%"])

query += " ORDER BY m.created_at DESC"

rows_data = db.fetch_all(query, params)

st.markdown("<div class='glass-card table-card fade-up'>", unsafe_allow_html=True)
st.markdown("<h3>Inventory Ledger</h3>", unsafe_allow_html=True)

if rows_data:
    rows = "".join(
        f"<tr><td>{r['created_at']}</td><td>{r['name']}</td><td>{r['sku']}</td><td>{r['document_type'] or ''}</td><td>{r['quantity']}</td><td>{r['warehouse'] or ''}</td><td>{r['location'] or ''}</td><td><span class='status-pill {r['status'].lower()}'>{r['status']}</span></td></tr>"
        for r in rows_data
    )
    table = f"""
    <table>
      <thead>
        <tr>
          <th>Timestamp</th><th>Product</th><th>SKU</th><th>Document</th><th>Qty</th><th>Warehouse</th><th>Location</th><th>Status</th>
        </tr>
      </thead>
      <tbody>{rows}</tbody>
    </table>
    """
    st.markdown(table, unsafe_allow_html=True)
else:
    st.info("No movement logs yet.")

st.markdown("</div>", unsafe_allow_html=True)
