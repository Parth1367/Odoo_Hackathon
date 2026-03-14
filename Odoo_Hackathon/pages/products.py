import streamlit as st
from database import db
from utils import auth
from utils.helpers import load_css, ensure_warehouse, ensure_location, adjust_stock
from components.sidebar import render_sidebar
from components.navbar import render_navbar

st.set_page_config(page_title="Products", page_icon="📦", layout="wide")
load_css()
db.init_db()
auth.ensure_default_user()
auth.require_login()
render_sidebar()

render_navbar("Products", "Manage SKUs, categories, reorder rules, and stock by location")


def dialog_or_expander(title: str):
    if hasattr(st, "dialog"):
        return st.dialog(title)
    return st.expander(title, expanded=True)

search = st.text_input("Search products", placeholder="Search by name or SKU")

categories = [row["category"] for row in db.fetch_all("SELECT DISTINCT category FROM products WHERE category IS NOT NULL")]
category_filter = st.selectbox("Category filter", ["All"] + categories)

col_add, _ = st.columns([1, 4])
with col_add:
    if st.button("Add Product", use_container_width=True):
        st.session_state["show_add_modal"] = True

if st.session_state.get("show_add_modal"):
    with dialog_or_expander("Add New Product"):
        name = st.text_input("Product Name")
        sku = st.text_input("SKU / Code")
        category = st.text_input("Category")
        uom = st.text_input("Unit of Measure")
        reorder_level = st.number_input("Reorder Level", min_value=1, step=1, value=20)

        st.markdown("**Initial Stock (optional)**")
        init_qty = st.number_input("Initial Stock Quantity", min_value=0, step=1)
        warehouse_name = st.text_input("Warehouse", placeholder="Main Warehouse")
        location_name = st.text_input("Location", placeholder="Rack A")

        if st.button("Save Product"):
            if name and sku:
                db.execute(
                    "INSERT INTO products (name, sku, category, uom, stock_qty, reorder_level) VALUES (?, ?, ?, ?, ?, ?)",
                    (name, sku, category, uom, 0, reorder_level),
                )
                product_id = db.fetch_one("SELECT id FROM products WHERE sku = ?", (sku,))["id"]

                if init_qty and warehouse_name and location_name:
                    warehouse_id = ensure_warehouse(warehouse_name)
                    location_id = ensure_location(warehouse_id, location_name)
                    adjust_stock(product_id, location_id, int(init_qty))
                    db.execute(
                        "INSERT INTO inventory_movements (product_id, movement_type, quantity, reference, note, document_type, location_id, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                        (product_id, "RECEIPT", init_qty, "Initial Stock", warehouse_name, "Receipt", location_id, "Done"),
                    )

                st.session_state["show_add_modal"] = False
                st.success("Product added")
                st.experimental_rerun()
            else:
                st.error("Name and SKU are required")

query = "SELECT * FROM products WHERE 1=1"
params = []

if search:
    query += " AND (name LIKE ? OR sku LIKE ?)"
    params.extend([f"%{search}%", f"%{search}%"])

if category_filter != "All":
    query += " AND category = ?"
    params.append(category_filter)

products = db.fetch_all(query, params)

st.markdown("<div class='glass-card table-card fade-up'>", unsafe_allow_html=True)
st.markdown("<h3>Product List</h3>", unsafe_allow_html=True)

if not products:
    st.info("No products found. Add your first product.")
else:
    header = st.columns([2, 2, 2, 2, 1, 1, 2])
    header[0].markdown("**Name**")
    header[1].markdown("**SKU**")
    header[2].markdown("**Category**")
    header[3].markdown("**UOM**")
    header[4].markdown("**Stock**")
    header[5].markdown("**Reorder**")
    header[6].markdown("**Actions**")

    for product in products:
        cols = st.columns([2, 2, 2, 2, 1, 1, 2])
        cols[0].write(product["name"])
        cols[1].write(product["sku"])
        cols[2].write(product["category"] or "-")
        cols[3].write(product["uom"] or "-")
        cols[4].write(product["stock_qty"])
        cols[5].write(product.get("reorder_level", 20))

        with cols[6]:
            edit_key = f"edit_{product['id']}"
            delete_key = f"delete_{product['id']}"
            col_a, col_b = st.columns(2)
            with col_a:
                if st.button("Edit", key=edit_key):
                    st.session_state["edit_id"] = product["id"]
            with col_b:
                if st.button("Delete", key=delete_key):
                    db.execute("DELETE FROM products WHERE id = ?", (product["id"],))
                    st.success("Product deleted")
                    st.experimental_rerun()

st.markdown("</div>", unsafe_allow_html=True)

if st.session_state.get("edit_id"):
    product = db.fetch_one("SELECT * FROM products WHERE id = ?", (st.session_state["edit_id"],))
    if product:
        with dialog_or_expander("Edit Product"):
            name = st.text_input("Product Name", value=product["name"])
            sku = st.text_input("SKU", value=product["sku"])
            category = st.text_input("Category", value=product["category"] or "")
            uom = st.text_input("Unit of Measure", value=product["uom"] or "")
            reorder_level = st.number_input("Reorder Level", min_value=1, step=1, value=int(product.get("reorder_level") or 20))
            if st.button("Save Changes"):
                db.execute(
                    "UPDATE products SET name = ?, sku = ?, category = ?, uom = ?, reorder_level = ? WHERE id = ?",
                    (name, sku, category, uom, reorder_level, product["id"]),
                )
                st.session_state["edit_id"] = None
                st.success("Product updated")
                st.experimental_rerun()

st.markdown("<div class='glass-card table-card fade-up' style='margin-top:1rem;'>", unsafe_allow_html=True)
st.markdown("<h3>Stock By Location</h3>", unsafe_allow_html=True)

stock_rows = db.fetch_all(
    """
    SELECT p.name AS product, w.name AS warehouse, l.name AS location, s.quantity
    FROM stock_levels s
    JOIN products p ON s.product_id = p.id
    JOIN locations l ON s.location_id = l.id
    JOIN warehouses w ON l.warehouse_id = w.id
    ORDER BY p.name, w.name, l.name
    """
)

if stock_rows:
    rows = "".join(
        f"<tr><td>{r['product']}</td><td>{r['warehouse']}</td><td>{r['location']}</td><td>{r['quantity']}</td></tr>"
        for r in stock_rows
    )
    table = f"""
    <table>
      <thead>
        <tr><th>Product</th><th>Warehouse</th><th>Location</th><th>Qty</th></tr>
      </thead>
      <tbody>{rows}</tbody>
    </table>
    """
    st.markdown(table, unsafe_allow_html=True)
else:
    st.info("No location stock recorded yet.")

st.markdown("</div>", unsafe_allow_html=True)
