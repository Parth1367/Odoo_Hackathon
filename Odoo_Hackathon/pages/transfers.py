import streamlit as st
from database import db
from utils import auth
from utils.helpers import load_css, ensure_warehouse, ensure_location, adjust_stock, get_stock
from components.sidebar import render_sidebar
from components.navbar import render_navbar

st.set_page_config(page_title="Transfers", page_icon="🔁", layout="wide")
load_css()
db.init_db()
auth.ensure_default_user()
auth.require_login()
render_sidebar()

render_navbar("Internal Transfers", "Move stock between warehouse locations")

products = db.fetch_all("SELECT id, name, sku FROM products ORDER BY name")
product_options = {f"{p['name']} ({p['sku']})": p["id"] for p in products}
product_labels = list(product_options.keys()) or ["No products available"]

st.markdown("<div class='glass-card fade-up'>", unsafe_allow_html=True)
st.markdown("<h3>Transfer Stock</h3>", unsafe_allow_html=True)

with st.form("transfer_form"):
    source_wh = st.text_input("Source Warehouse", placeholder="Main Warehouse")
    source_loc = st.text_input("Source Location", placeholder="Rack A")
    dest_wh = st.text_input("Destination Warehouse", placeholder="Production Floor")
    dest_loc = st.text_input("Destination Location", placeholder="Rack B")
    product_label = st.selectbox("Product", product_labels, disabled=not product_options)
    qty = st.number_input("Quantity", min_value=1, step=1)
    status = st.selectbox("Status", ["Draft", "Waiting", "Ready", "Done", "Canceled"], index=2)
    transferred_at = st.date_input("Transfer Date")
    submit = st.form_submit_button("Create Transfer")

    if submit:
        if not product_options:
            st.error("Add a product before transferring.")
        elif status == "Canceled":
            st.error("Canceled transfers cannot be validated.")
        else:
            product_id = product_options[product_label]
            source_wh_id = ensure_warehouse(source_wh or "Main Warehouse")
            source_loc_id = ensure_location(source_wh_id, source_loc or "Rack A")
            dest_wh_id = ensure_warehouse(dest_wh or "Production Floor")
            dest_loc_id = ensure_location(dest_wh_id, dest_loc or "Rack B")

            db.execute(
                "INSERT INTO transfers (product_id, quantity, source_location, dest_location, transferred_at, status, source_location_id, dest_location_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (product_id, qty, source_loc, dest_loc, str(transferred_at), status, source_loc_id, dest_loc_id),
            )

            if status in ["Ready", "Done"]:
                available = get_stock(product_id, source_loc_id)
                if qty > available:
                    st.error("Insufficient stock at source location.")
                else:
                    adjust_stock(product_id, source_loc_id, -int(qty))
                    adjust_stock(product_id, dest_loc_id, int(qty))
                    db.execute(
                        "INSERT INTO inventory_movements (product_id, movement_type, quantity, reference, note, document_type, location_id, dest_location_id, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                        (product_id, "TRANSFER", qty, "Transfer", f"{source_loc} -> {dest_loc}", "Internal", source_loc_id, dest_loc_id, status),
                    )
                    st.success("Transfer logged")
            else:
                st.success("Transfer recorded")

st.markdown("</div>", unsafe_allow_html=True)

history = db.fetch_all(
    """
    SELECT t.created_at, p.name, t.quantity, t.source_location, t.dest_location, t.transferred_at, t.status
    FROM transfers t
    JOIN products p ON t.product_id = p.id
    ORDER BY t.created_at DESC
    LIMIT 10
    """
)

st.markdown("<div class='glass-card table-card fade-up' style='margin-top:1rem;'>", unsafe_allow_html=True)
st.markdown("<h3>Transfer Log</h3>", unsafe_allow_html=True)

if history:
    rows = "".join(
        f"<tr><td>{h['created_at']}</td><td>{h['name']}</td><td>{h['quantity']}</td><td>{h['source_location']}</td><td>{h['dest_location']}</td><td>{h['transferred_at']}</td><td><span class='status-pill {h['status'].lower()}'>{h['status']}</span></td></tr>"
        for h in history
    )
    table = f"""
    <table>
      <thead>
        <tr><th>Timestamp</th><th>Product</th><th>Qty</th><th>From</th><th>To</th><th>Date</th><th>Status</th></tr>
      </thead>
      <tbody>{rows}</tbody>
    </table>
    """
    st.markdown(table, unsafe_allow_html=True)
else:
    st.info("No transfers yet.")

st.markdown("</div>", unsafe_allow_html=True)
