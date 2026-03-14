import streamlit as st
from database import db
from utils import auth
from utils.helpers import load_css, ensure_warehouse, ensure_location, adjust_stock, get_stock
from components.sidebar import render_sidebar
from components.navbar import render_navbar

st.set_page_config(page_title="Adjustments", page_icon="🧮", layout="wide")
load_css()
db.init_db()
auth.ensure_default_user()
auth.require_login()
render_sidebar()

render_navbar("Stock Adjustments", "Reconcile physical counts and system stock")

products = db.fetch_all("SELECT id, name, sku FROM products ORDER BY name")
product_options = {f"{p['name']} ({p['sku']})": p["id"] for p in products}
product_labels = list(product_options.keys()) or ["No products available"]

st.markdown("<div class='glass-card fade-up'>", unsafe_allow_html=True)
st.markdown("<h3>Adjustment Entry</h3>", unsafe_allow_html=True)

with st.form("adjustment_form"):
    product_label = st.selectbox("Product", product_labels, disabled=not product_options)
    warehouse_name = st.text_input("Warehouse", placeholder="Main Warehouse")
    location_name = st.text_input("Location", placeholder="Rack A")
    counted_qty = st.number_input("Counted Quantity", min_value=0, step=1)
    reason = st.text_input("Reason", placeholder="Cycle count variance")
    status = st.selectbox("Status", ["Draft", "Waiting", "Ready", "Done", "Canceled"], index=2)
    adjusted_at = st.date_input("Adjustment Date")
    submit = st.form_submit_button("Apply Adjustment")

    if submit:
        if not product_options:
            st.error("Add a product before adjusting stock.")
        elif status == "Canceled":
            st.error("Canceled adjustments cannot be validated.")
        else:
            product_id = product_options[product_label]
            warehouse_id = ensure_warehouse(warehouse_name or "Main Warehouse")
            location_id = ensure_location(warehouse_id, location_name or "Rack A")
            system_qty = get_stock(product_id, location_id)
            delta = int(counted_qty) - int(system_qty)

            db.execute(
                "INSERT INTO adjustments (product_id, quantity, reason, adjusted_at, status, location_id) VALUES (?, ?, ?, ?, ?, ?)",
                (product_id, delta, reason, str(adjusted_at), status, location_id),
            )

            if status in ["Ready", "Done"]:
                adjust_stock(product_id, location_id, delta)
                db.execute(
                    "INSERT INTO inventory_movements (product_id, movement_type, quantity, reference, note, document_type, location_id, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (product_id, "ADJUSTMENT", delta, "Adjustment", reason, "Adjustment", location_id, status),
                )

            st.success(f"Adjustment applied: {delta}")

st.markdown("</div>", unsafe_allow_html=True)

history = db.fetch_all(
    """
    SELECT a.created_at, p.name, a.quantity, a.reason, a.adjusted_at, a.status
    FROM adjustments a
    JOIN products p ON a.product_id = p.id
    ORDER BY a.created_at DESC
    LIMIT 10
    """
)

st.markdown("<div class='glass-card table-card fade-up' style='margin-top:1rem;'>", unsafe_allow_html=True)
st.markdown("<h3>Adjustment History</h3>", unsafe_allow_html=True)

if history:
    rows = "".join(
        f"<tr><td>{h['created_at']}</td><td>{h['name']}</td><td>{h['quantity']}</td><td>{h['reason']}</td><td>{h['adjusted_at']}</td><td><span class='status-pill {h['status'].lower()}'>{h['status']}</span></td></tr>"
        for h in history
    )
    table = f"""
    <table>
      <thead>
        <tr><th>Timestamp</th><th>Product</th><th>Delta</th><th>Reason</th><th>Date</th><th>Status</th></tr>
      </thead>
      <tbody>{rows}</tbody>
    </table>
    """
    st.markdown(table, unsafe_allow_html=True)
else:
    st.info("No adjustments yet.")

st.markdown("</div>", unsafe_allow_html=True)
