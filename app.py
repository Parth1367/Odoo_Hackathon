import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

# -----------------------
# DATABASE CONNECTION
# -----------------------

conn = sqlite3.connect("inventory.db", check_same_thread=False)
cursor = conn.cursor()

# -----------------------
# CREATE TABLES
# -----------------------

cursor.execute("""
CREATE TABLE IF NOT EXISTS users(
id INTEGER PRIMARY KEY AUTOINCREMENT,
username TEXT,
password TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS products(
id INTEGER PRIMARY KEY AUTOINCREMENT,
name TEXT,
sku TEXT,
category TEXT,
unit TEXT,
stock INTEGER
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS movements(
id INTEGER PRIMARY KEY AUTOINCREMENT,
product TEXT,
type TEXT,
quantity INTEGER,
date TEXT
)
""")

conn.commit()

# -----------------------
# DEFAULT USER
# -----------------------

cursor.execute("SELECT * FROM users WHERE username='admin'")
if not cursor.fetchone():
    cursor.execute("INSERT INTO users(username,password) VALUES('admin','admin')")
    conn.commit()

# -----------------------
# LOGIN SYSTEM
# -----------------------

def login():

    st.title("Inventory Management System")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):

        cursor.execute(
            "SELECT * FROM users WHERE username=? AND password=?",
            (username,password)
        )

        user = cursor.fetchone()

        if user:
            st.session_state.logged_in = True
        else:
            st.error("Invalid credentials")

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    login()
    st.stop()

# -----------------------
# SIDEBAR MENU
# -----------------------

menu = st.sidebar.selectbox(
    "Navigation",
    [
        "Dashboard",
        "Products",
        "Receipts",
        "Deliveries",
        "Stock Adjustment",
        "Move History"
    ]
)

# -----------------------
# DASHBOARD
# -----------------------

if menu == "Dashboard":

    st.title("Inventory Dashboard")

    products = pd.read_sql("SELECT * FROM products", conn)
    movements = pd.read_sql("SELECT * FROM movements", conn)

    total_products = len(products)
    total_stock = products["stock"].sum() if not products.empty else 0

    low_stock = len(products[products["stock"] < 10]) if not products.empty else 0

    col1,col2,col3 = st.columns(3)

    col1.metric("Total Products", total_products)
    col2.metric("Total Stock", total_stock)
    col3.metric("Low Stock Items", low_stock)

    st.subheader("Recent Movements")
    st.dataframe(movements.tail(10))

# -----------------------
# PRODUCT MANAGEMENT
# -----------------------

elif menu == "Products":

    st.title("Product Management")

    name = st.text_input("Product Name")
    sku = st.text_input("SKU")
    category = st.text_input("Category")
    unit = st.text_input("Unit")
    stock = st.number_input("Initial Stock", min_value=0)

    if st.button("Add Product"):

        cursor.execute("""
        INSERT INTO products(name,sku,category,unit,stock)
        VALUES(?,?,?,?,?)
        """,(name,sku,category,unit,stock))

        conn.commit()

        st.success("Product Added")

    st.subheader("Product List")

    df = pd.read_sql("SELECT * FROM products", conn)
    st.dataframe(df)

# -----------------------
# RECEIPTS
# -----------------------

elif menu == "Receipts":

    st.title("Incoming Stock")

    df = pd.read_sql("SELECT * FROM products", conn)

    product = st.selectbox("Product", df["name"])
    qty = st.number_input("Quantity Received", min_value=1)

    if st.button("Receive"):

        cursor.execute("""
        UPDATE products
        SET stock = stock + ?
        WHERE name = ?
        """,(qty,product))

        cursor.execute("""
        INSERT INTO movements(product,type,quantity,date)
        VALUES(?,?,?,?)
        """,(product,"Receipt",qty,str(datetime.now())))

        conn.commit()

        st.success("Stock Updated")

# -----------------------
# DELIVERIES
# -----------------------

elif menu == "Deliveries":

    st.title("Outgoing Delivery")

    df = pd.read_sql("SELECT * FROM products", conn)

    product = st.selectbox("Product", df["name"])
    qty = st.number_input("Quantity Delivered", min_value=1)

    if st.button("Deliver"):

        cursor.execute("""
        UPDATE products
        SET stock = stock - ?
        WHERE name = ?
        """,(qty,product))

        cursor.execute("""
        INSERT INTO movements(product,type,quantity,date)
        VALUES(?,?,?,?)
        """,(product,"Delivery",-qty,str(datetime.now())))

        conn.commit()

        st.success("Delivery Completed")

# -----------------------
# STOCK ADJUSTMENT
# -----------------------

elif menu == "Stock Adjustment":

    st.title("Stock Adjustment")

    df = pd.read_sql("SELECT * FROM products", conn)

    product = st.selectbox("Product", df["name"])
    qty = st.number_input("Adjustment Quantity")

    if st.button("Adjust"):

        cursor.execute("""
        UPDATE products
        SET stock = stock + ?
        WHERE name = ?
        """,(qty,product))

        cursor.execute("""
        INSERT INTO movements(product,type,quantity,date)
        VALUES(?,?,?,?)
        """,(product,"Adjustment",qty,str(datetime.now())))

        conn.commit()

        st.success("Stock Adjusted")

# -----------------------
# MOVE HISTORY
# -----------------------

elif menu == "Move History":

    st.title("Inventory Movement History")

    df = pd.read_sql("SELECT * FROM movements ORDER BY date DESC", conn)

    st.dataframe(df)