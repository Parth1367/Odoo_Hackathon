import streamlit as st
from database import db
from utils import auth
from utils.helpers import load_css, ensure_warehouse, ensure_location, adjust_stock
from components.sidebar import render_sidebar
from components.navbar import render_navbar

st.set_page_config(page_title="Receipts", page_icon="📥", layout="wide")
load_css()
db.init_db()
auth.ensure_default_user()
auth.require_login()
render_sidebar()

render_navbar("Receipts", "Capture incoming goods and update stock")

products = db.fetch_all("SELECT id, name, sku FROM products ORDER BY name")
product_options = {f"{p['name']} ({p['sku']})": p["id"] for p in products}
product_labels = list(product_options.keys()) or ["No products available"]

st.markdown("<div class='glass-card fade-up'>", unsafe_allow_html=True)
st.markdown("<h3>Incoming Goods</h3>", unsafe_allow_html=True)

with st.form("receipt_form"):
    supplier = st.text_input("Supplier")
    product_label = st.selectbox("Product", product_labels, disabled=not product_options)
    qty = st.number_input("Quantity Received", min_value=1, step=1)
    warehouse_name = st.text_input("Warehouse", placeholder="Main Warehouse")
    location_name = st.text_input("Location", placeholder="Inbound Dock")
    status = st.selectbox("Status", ["Draft", "Waiting", "Ready", "Done", "Canceled"], index=3)
    received_at = st.date_input("Received Date")
    submit = st.form_submit_button("Validate Receipt")

    if submit:
        if not product_options:
            st.error("Add a product before receiving goods.")
        elif status == "Canceled":
            st.error("Canceled receipts cannot be validated.")
        else:
            product_id = product_options[product_label]
            warehouse_id = ensure_warehouse(warehouse_name or "Main Warehouse")
            location_id = ensure_location(warehouse_id, location_name or "Inbound Dock")

            db.execute(
                "INSERT INTO receipts (product_id, quantity, supplier, received_at, status, location_id) VALUES (?, ?, ?, ?, ?, ?)",
                (product_id, qty, supplier, str(received_at), status, location_id),
            )

            if status in ["Ready", "Done"]:
                adjust_stock(product_id, location_id, int(qty))
                db.execute(
                    "INSERT INTO inventory_movements (product_id, movement_type, quantity, reference, note, document_type, location_id, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (product_id, "RECEIPT", qty, "Receipt", supplier, "Receipt", location_id, status),
                )

            st.success("Receipt recorded")

st.markdown("</div>", unsafe_allow_html=True)

history = db.fetch_all(
    """
    SELECT r.created_at, p.name, r.quantity, r.supplier, r.received_at, r.status
    FROM receipts r
    JOIN products p ON r.product_id = p.id
    ORDER BY r.created_at DESC
    LIMIT 10
    """
)

st.markdown("<div class='glass-card table-card fade-up' style='margin-top:1rem;'>", unsafe_allow_html=True)
st.markdown("<h3>Receipt History</h3>", unsafe_allow_html=True)

if history:
    rows = "".join(
        f"<tr><td>{h['created_at']}</td><td>{h['name']}</td><td>{h['quantity']}</td><td>{h['supplier'] or ''}</td><td>{h['received_at']}</td><td><span class='status-pill {h['status'].lower()}'>{h['status']}</span></td></tr>"
        for h in history
    )
    table = f"""
    <table>
      <thead>
        <tr><th>Timestamp</th><th>Product</th><th>Qty</th><th>Supplier</th><th>Received</th><th>Status</th></tr>
      </thead>
      <tbody>{rows}</tbody>
    </table>
    """
    st.markdown(table, unsafe_allow_html=True)
else:
    st.info("No receipts yet.")

st.markdown("</div>", unsafe_allow_html=True)
