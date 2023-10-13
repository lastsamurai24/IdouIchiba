import sqlite3

DATABASE_PATH = "mydatabase.db"


def get_products_by_category(category):
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT product_name, price FROM products WHERE category LIKE ?", ("%" + category + "%",))
    products = cursor.fetchall()
    conn.close()
    return products


def get_products_by_partial_category(product_name):
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT product_name, price FROM products WHERE product_name LIKE ?", ("%" + product_name + "%",)
    )
    products = cursor.fetchall()
    conn.close()
    return products


import sqlite3


def get_product_price_by_name(product_name):
    
    conn = sqlite3.connect("mydatabase.db")  # Adjust the path if necessary
    cursor = conn.cursor()

    cursor.execute("SELECT price FROM products WHERE product_name=?", (product_name,))
    price = cursor.fetchone()

    
    conn.close()

    if price:
        return price[0]
    else:
        return None



