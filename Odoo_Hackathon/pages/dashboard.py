import streamlit as st
from database import db
from utils import auth
from utils.helpers import load_css, inject_counter_js
from components.sidebar import render_sidebar
from components.navbar import render_navbar

st.set_page_config(page_title="Dashboard", page_icon="📊", layout="wide")
load_css()
db.init_db()
auth.ensure_default_user()
auth.require_login()
render_sidebar()

render_navbar("Dashboard", "Live inventory KPIs and movement overview")

pending_statuses = ("Draft", "Waiting", "Ready")

count_products = db.fetch_one("SELECT COUNT(*) AS c FROM products")["c"]
stock_total = db.fetch_one("SELECT COALESCE(SUM(stock_qty),0) AS s FROM products")["s"]
low_stock = db.fetch_one(
    "SELECT COUNT(*) AS c FROM products WHERE stock_qty <= COALESCE(reorder_level, 20)")["c"]

pending_receipts = db.fetch_one(
    "SELECT COUNT(*) AS c FROM receipts WHERE status IN ('Draft','Waiting','Ready')")["c"]

pending_deliveries = db.fetch_one(
    "SELECT COUNT(*) AS c FROM deliveries WHERE status IN ('Draft','Waiting','Ready')")["c"]

pending_transfers = db.fetch_one(
    "SELECT COUNT(*) AS c FROM transfers WHERE status IN ('Draft','Waiting','Ready')")["c"]

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.markdown("<div class='glass-card kpi-card fade-up'>", unsafe_allow_html=True)
    st.markdown("<div class='kpi-title'>Total Products</div><div class='kpi-value count'>{}</div><div class='muted'>Active SKUs</div>".format(count_products), unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

with col2:
    st.markdown("<div class='glass-card kpi-card fade-up'>", unsafe_allow_html=True)
    st.markdown("<div class='kpi-title'>Total Stock</div><div class='kpi-value count'>{}</div><div class='muted'>All locations</div>".format(stock_total), unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

with col3:
    st.markdown("<div class='glass-card kpi-card fade-up'>", unsafe_allow_html=True)
    st.markdown("<div class='kpi-title'>Low/Out of Stock</div><div class='kpi-value count'>{}</div><div class='muted'>Needs attention</div>".format(low_stock), unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

with col4:
    st.markdown("<div class='glass-card kpi-card fade-up'>", unsafe_allow_html=True)
    st.markdown("<div class='kpi-title'>Pending Receipts</div><div class='kpi-value count'>{}</div><div class='muted'>Awaiting validation</div>".format(pending_receipts), unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

with col5:
    st.markdown("<div class='glass-card kpi-card fade-up'>", unsafe_allow_html=True)
    st.markdown("<div class='kpi-title'>Pending Deliveries</div><div class='kpi-value count'>{}</div><div class='muted'>Outbound queue</div>".format(pending_deliveries), unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

inject_counter_js()

st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)

filter_col1, filter_col2, filter_col3, filter_col4, filter_col5 = st.columns(5)

with filter_col1:
    doc_filter = st.selectbox("Document Type", ["All", "Receipt", "Delivery", "Internal", "Adjustment"])
with filter_col2:
    status_filter = st.selectbox("Status", ["All", "Draft", "Waiting", "Ready", "Done", "Canceled"])
with filter_col3:
    warehouse_filter = st.selectbox(
        "Warehouse",
        ["All"] + [w["name"] for w in db.fetch_all("SELECT name FROM warehouses ORDER BY name")],
    )
with filter_col4:
    category_filter = st.selectbox(
        "Product Category",
        ["All"] + [c["category"] for c in db.fetch_all("SELECT DISTINCT category FROM products WHERE category IS NOT NULL")],
    )
with filter_col5:
    location_filter = st.selectbox(
        "Location",
        ["All"] + [l["name"] for l in db.fetch_all("SELECT name FROM locations ORDER BY name")],
    )

query = """
    SELECT m.created_at, p.name, p.category, m.document_type, m.movement_type, m.quantity, m.reference, m.status,
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
if category_filter != "All":
    query += " AND p.category = ?"
    params.append(category_filter)
if location_filter != "All":
    query += " AND l.name = ?"
    params.append(location_filter)

query += " ORDER BY m.created_at DESC LIMIT 12"

movements = db.fetch_all(query, params)

st.markdown("<div class='glass-card table-card fade-up'>", unsafe_allow_html=True)
st.markdown("<h3>Recent Inventory Movements</h3>", unsafe_allow_html=True)

if movements:
    rows = "".join(
        f"<tr><td>{m['created_at']}</td><td>{m['name']}</td><td>{m['document_type'] or ''}</td><td>{m['quantity']}</td><td>{m['warehouse'] or ''}</td><td>{m['location'] or ''}</td><td><span class='status-pill {m['status'].lower()}'>{m['status']}</span></td></tr>"
        for m in movements
    )
    table = f"""
    <table>
      <thead>
        <tr>
          <th>Timestamp</th><th>Product</th><th>Doc Type</th><th>Qty</th><th>Warehouse</th><th>Location</th><th>Status</th>
        </tr>
      </thead>
      <tbody>{rows}</tbody>
    </table>
    """
    st.markdown(table, unsafe_allow_html=True)
else:
    st.info("No movements yet. Add products and record receipts or deliveries.")

st.markdown("</div>", unsafe_allow_html=True)

st.markdown("<div class='glass-card fade-up' style='margin-top:1rem;'>", unsafe_allow_html=True)
st.markdown("<h3>Internal Transfers Scheduled</h3>", unsafe_allow_html=True)

transfer_rows = db.fetch_all(
    """
    SELECT t.created_at, p.name, t.quantity, t.source_location, t.dest_location, t.status
    FROM transfers t
    JOIN products p ON t.product_id = p.id
    WHERE t.status IN ('Draft','Waiting','Ready')
    ORDER BY t.created_at DESC
    LIMIT 8
    """
)

if transfer_rows:
    rows = "".join(
        f"<tr><td>{t['created_at']}</td><td>{t['name']}</td><td>{t['quantity']}</td><td>{t['source_location']}</td><td>{t['dest_location']}</td><td><span class='status-pill {t['status'].lower()}'>{t['status']}</span></td></tr>"
        for t in transfer_rows
    )
    table = f"""
    <table>
      <thead>
        <tr><th>Timestamp</th><th>Product</th><th>Qty</th><th>From</th><th>To</th><th>Status</th></tr>
      </thead>
      <tbody>{rows}</tbody>
    </table>
    """
    st.markdown(table, unsafe_allow_html=True)
else:
    st.info("No scheduled internal transfers.")

st.markdown("</div>", unsafe_allow_html=True)
