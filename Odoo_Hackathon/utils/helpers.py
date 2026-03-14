from pathlib import Path
import streamlit as st
import streamlit.components.v1 as components
from database import db


def load_css():
    base = Path(__file__).resolve().parents[1] / "assets"
    styles = (base / "styles.css").read_text()
    animations = (base / "animations.css").read_text()
    st.markdown(f"<style>{styles}\n{animations}</style>", unsafe_allow_html=True)


def inject_counter_js():
    components.html(
        """
        <script>
        const counters = window.parent.document.querySelectorAll('.count');
        counters.forEach((el) => {
          const target = parseInt(el.textContent.replace(/,/g,''), 10) || 0;
          let current = 0;
          const step = Math.max(1, Math.floor(target / 60));
          const timer = setInterval(() => {
            current += step;
            if (current >= target) {
              current = target;
              clearInterval(timer);
            }
            el.textContent = current.toLocaleString();
          }, 16);
        });
        </script>
        """,
        height=0,
        width=0,
    )


def ensure_warehouse(name: str, region: str = "") -> int:
    row = db.fetch_one("SELECT id FROM warehouses WHERE name = ?", (name,))
    if row:
        return row["id"]
    db.execute("INSERT INTO warehouses (name, region) VALUES (?, ?)", (name, region))
    return db.fetch_one("SELECT id FROM warehouses WHERE name = ?", (name,))["id"]


def ensure_location(warehouse_id: int, name: str) -> int:
    row = db.fetch_one(
        "SELECT id FROM locations WHERE warehouse_id = ? AND name = ?",
        (warehouse_id, name),
    )
    if row:
        return row["id"]
    db.execute(
        "INSERT INTO locations (warehouse_id, name) VALUES (?, ?)",
        (warehouse_id, name),
    )
    return db.fetch_one(
        "SELECT id FROM locations WHERE warehouse_id = ? AND name = ?",
        (warehouse_id, name),
    )["id"]


def get_stock(product_id: int, location_id: int) -> int:
    row = db.fetch_one(
        "SELECT quantity FROM stock_levels WHERE product_id = ? AND location_id = ?",
        (product_id, location_id),
    )
    return int(row["quantity"]) if row else 0


def set_stock(product_id: int, location_id: int, quantity: int):
    row = db.fetch_one(
        "SELECT id FROM stock_levels WHERE product_id = ? AND location_id = ?",
        (product_id, location_id),
    )
    if row:
        db.execute(
            "UPDATE stock_levels SET quantity = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (quantity, row["id"]),
        )
    else:
        db.execute(
            "INSERT INTO stock_levels (product_id, location_id, quantity) VALUES (?, ?, ?)",
            (product_id, location_id, quantity),
        )


def adjust_stock(product_id: int, location_id: int, delta: int):
    current = get_stock(product_id, location_id)
    set_stock(product_id, location_id, current + delta)
    db.execute(
        "UPDATE products SET stock_qty = (SELECT COALESCE(SUM(quantity),0) FROM stock_levels WHERE product_id = ?) WHERE id = ?",
        (product_id, product_id),
    )
