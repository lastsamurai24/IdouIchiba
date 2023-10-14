import sqlite3
import csv
import os

DATABASE_NAME = "mydatabase.db"


def create_table():
    """
    データベースにテーブルを作成する関数
    """
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY,
        category TEXT NOT NULL,
        product_id TEXT NOT NULL,
        product_name TEXT NOT NULL,
        price INTEGER NOT NULL,
        stock INTEGER NOT NULL
    )
    """)

    conn.commit()
    conn.close()


def insert_csv_to_db(csv_file_path):
    """
    CSVファイルの内容をデータベースに保存する関数
    """
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()

    with open(csv_file_path, 'r', encoding="utf-8") as file:
        reader = csv.DictReader(file)
        for row in reader:
            cursor.execute("INSERT INTO products (category, product_id, product_name, price, stock) VALUES (?, ?, ?, ?, ?)", 
                           (row["分類"], row["商品ID"], row["商品名"], row["単価"], row["在庫数"]))

    conn.commit()
    conn.close()


if __name__ == "__main__":
    # テーブルを作成
    create_table()

    # CSVファイルのパスを指定して、その内容をデータベースに保存
    csv_path = os.path.join(os.getcwd(), "products.csv")  # ここにCSVファイルのパスを指定
    insert_csv_to_db(csv_path)
