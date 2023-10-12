import sqlite3

DATABASE_PATH = 'mydatabase.db'

def get_products_by_category(category):
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT product_name, price FROM products WHERE category LIKE ?", ('%' + category + '%',))
    products = cursor.fetchall()
    conn.close()
    return products
