import os
import logging
import sqlite3
from logging.handlers import RotatingFileHandler
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from dotenv import load_dotenv
from database_utils import (
    get_products_by_category,
    get_products_by_partial_category,
    get_product_price_by_name,
)
from linebot.models import (
    MessageEvent,
    TextMessage,
    TextSendMessage,
    ButtonsTemplate,
    TemplateSendMessage,
    PostbackAction,
    URIAction,
    FlexSendMessage,
    PostbackEvent,
)
from linebot.models import PostbackEvent
load_dotenv()

# ... [残りのコードは変更なし]


app = Flask(__name__)

line_bot_api = LineBotApi(os.environ["ACCESS_TOKEN"])
handler = WebhookHandler(os.environ["CHANNEL_SECRET"])


@app.route("/")
def index():
    return "You call index()"


@app.route("/push_sample")
def push_sample():
    """プッシュメッセージを送る"""
    user_id = os.environ["USER_ID"]
    line_bot_api.push_message(user_id, TextSendMessage(text="Hello World!"))

    return "OK"


@app.route("/callback", methods=["POST"])
def callback():
    """Messaging APIからの呼び出し関数"""
    signature = request.headers["X-Line-Signature"]
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError as e:
        abort(400)

    return "OK"


@handler.add(MessageEvent, message=TextMessage)
def handle_message_combined(event):
    received_msg = event.message.text
    user_id = event.source.user_id

    if received_msg.isdigit():
        # 前回のメッセージを last_received_message 辞書から取得
        previous_msg = last_received_message.get(user_id, "")
        reply = handle_quantity_message(event, int(received_msg), previous_msg)
    else:
        products_by_category = get_products_by_category(received_msg)

        if products_by_category:
            reply_msg = "\n".join([f"{product[0]}: {product[1]}円" for product in products_by_category])
            reply = TextSendMessage(text=reply_msg)
        else:
            products_by_exact_name = get_products_by_partial_category(received_msg)
            if any(product[0] == received_msg for product in products_by_exact_name):
                # received_msg を last_received_message 辞書に保存
                last_received_message[user_id] = received_msg
                reply = handle_quantity_message(event, 1, received_msg)  # 1はデフォルトの数量として設定しています。
            else:
                reply_msg = "製品が見つかりませんでした。"
                reply = TextSendMessage(text=reply_msg)

    # 返信処理
    line_bot_api.reply_message(event.reply_token, reply)


def handle_quantity_message(event, quantity, received_msg):
    # ボタンテンプレートの作成
    buttons_template = ButtonsTemplate(
        thumbnail_image_url="https://example.com/bot/images/image.jpg",
        title="選択した商品",
        text=f"{received_msg}を{quantity}つでよろしいでしょうか？",
        actions=[
            PostbackAction(label="買う", data=f"action=buy&quantity={quantity}"),
            PostbackAction(label="カートにいれる", data=f"action=add&quantity={quantity}"),
            PostbackAction(label="カートを確認", data="action=view_cart"),
            URIAction(label="商品の詳細", uri="https://idouichiba.onrender.com"),
        ],
    )

    # テンプレートメッセージの作成
    template_message = TemplateSendMessage(alt_text=f"{quantity}でよろしいでしょうか？", template=buttons_template)

    # テンプレートメッセージを返す
    return template_message


last_received_message = {}
user_carts = {}

DATABASE_NAME = "mydatabase.db"
@handler.add(PostbackEvent)
# カートを模倣する簡易的なデータ構造
def add_to_cart(user_id, product_id, quantity):
    """
    ユーザーのカートにアイテムを追加する関数
    """
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()

    # Check if the item already exists in the user's cart
    cursor.execute("SELECT quantity FROM user_carts WHERE user_id=? AND product_id=?", (user_id, product_id))
    existing_quantity = cursor.fetchone()

    if existing_quantity:
        # Update the quantity if the item already exists
        new_quantity = existing_quantity[0] + quantity
        cursor.execute("UPDATE user_carts SET quantity=? WHERE user_id=? AND product_id=?", (new_quantity, user_id, product_id))
    else:
        # Insert a new item if it doesn't exist
        cursor.execute("INSERT INTO user_carts (user_id, product_id, quantity) VALUES (?, ?, ?)", (user_id, product_id, quantity))

    conn.commit()
    conn.close()



def remove_from_cart(user_id, product_id):
    """
    ユーザーのカートからアイテムを削除する関数
    """
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()

    cursor.execute("DELETE FROM user_carts WHERE user_id=? AND product_id=?", (user_id, product_id))

    conn.commit()
    conn.close()


def update_cart_quantity(user_id, product_id, quantity):
    """
    ユーザーのカートのアイテムの数量を更新する関数
    """
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()

    cursor.execute("UPDATE user_carts SET quantity=? WHERE user_id=? AND product_id=?", (quantity, user_id, product_id))

    conn.commit()
    conn.close()


def get_user_cart_from_db(user_id):
    """
    ユーザーのカートの内容を取得する関数
    """
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()

    cursor.execute("SELECT product_id, quantity FROM user_carts WHERE user_id=?", (user_id,))
    cart_items = cursor.fetchall()

    conn.close()
    return cart_items

def get_cart_contents(user_id):
    """カートの中身を取得する関数"""
    return user_carts.get(user_id, {})


# 既存のカートデータ構造
# user_carts = {}
def get_user_cart(user_id):
    """指定されたユーザーIDのカートの内容を返す関数"""
    return user_carts.get(user_id, {})

def get_cart_total_price(user_id):
    """カートの合計金額を計算する関数"""
    cart = user_carts.get(user_id, {})
    total_price = 0
    for product_name, quantity in cart.items():
        product_price = get_product_price_by_name(product_name)
        if product_price is not None:
            total_price += product_price * quantity
        else:
            app.logger.warning(f"Price not found for product: {product_name}")
    return total_price


@handler.add(PostbackEvent)
def handle_postback(event):
    data = event.postback.data
    params = dict([item.split("=") for item in data.split("&")])
    user_id = event.source.user_id

    action = params.get("action")
    quantity = int(params.get("quantity", 1))
    product_name = last_received_message.get(user_id, "")

    if action == "buy":
        handle_buy_action(event, product_name, quantity)
    elif action == "add":
        handle_add_action(event, user_id, quantity, product_name)
    elif action == "view_cart":
        handle_view_cart(event, user_id)

def handle_view_cart(event, user_id):
    cart_contents = get_cart_contents(user_id)
    
    if not cart_contents:
        # カートが空の場合の既存のコード
        return

    receipt_cart_items = []
    for product, qty in cart_contents.items():
        product_price = get_product_price_by_name(product)
        subtotal = product_price * qty
        receipt_cart_items.extend([
            {"type": "text", "text": f"商品名: {product}"},
            {"type": "text", "text": f"価格: {product_price}円"},
            {"type": "text", "text": f"数量: {qty}つ"},
            {"type": "text", "text": f"小計: {subtotal}円"},
            {"type": "separator"}  # 商品間のセパレーターを追加
        ])

    # 最後のセパレーターを削除して見た目をきれいにする
    receipt_cart_items.pop()

    # 最後に合計金額を追加
    total_price = get_cart_total_price(user_id)
    receipt_cart_items.append({"type": "text", "text": f"合計: {total_price}円"})

    # フッターを含むFlexメッセージの内容を作成
    receipt_flex_content = {
        "type": "bubble",
        "header": {
            "type": "box",
            "layout": "vertical",
            "contents": [{"type": "text", "text": "カートのレシート", "weight": "bold", "size": "xl"}]
        },
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": receipt_cart_items
        },
        "footer": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "button",
                    "action": {"type": "postback", "label": "支払う", "data": "action=pay"},
                    "style": "primary",
                }
            ],
        }
    }

    flex_message = FlexSendMessage(alt_text="カートのレシート", contents=receipt_flex_content)
    line_bot_api.reply_message(event.reply_token, flex_message)


def handle_add_action(event, user_id, quantity, product_name):
    add_to_cart(user_id, product_name, quantity)
    reply_msg = f"{product_name}を{quantity}つカートに追加しました。"
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_msg))



def handle_buy_action(event, product_name, quantity):
    product_price = get_product_price_by_name(product_name)

    if product_price is None:
        app.logger.error(f"Failed to get price for product: {product_name}")
        # ここでユーザーにエラーメッセージを返すなどの処理を追加することもできます。
        return

    total_price = product_price * quantity
    flex_content = {
        "type": "bubble",
        "header": {
            "type": "box",
            "layout": "vertical",
            "contents": [{"type": "text", "text": "購入確認", "weight": "bold", "size": "xl"}],
        },
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {"type": "text", "text": f"商品名: {product_name}"},
                {"type": "text", "text": f"数量: {quantity}つ"},
                {"type": "text", "text": f"合計: {total_price}円"},
            ],
        },
        "footer": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "button",
                    "action": {"type": "postback", "label": "支払う", "data": "action=pay"},
                    "style": "primary",
                }
            ],
        },
    }

    flex_message = FlexSendMessage(alt_text="購入確認", contents=flex_content)

    line_bot_api.reply_message(event.reply_token, flex_message)


log_handler = RotatingFileHandler("flask_app.log", maxBytes=10000, backupCount=3)
log_handler.setLevel(logging.INFO)
app.logger.addHandler(log_handler)


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)



import sqlite3

DATABASE_NAME = "mydatabase.db"


def modify_cart_table_for_product_name():
    """
    Modify the user_carts table to use product_name instead of product_id
    """
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()

    # Rename the existing user_carts table to a temporary table
    cursor.execute("ALTER TABLE user_carts RENAME TO temp_user_carts")

    # Create a new user_carts table with the product_name column
    cursor.execute(\"\""
    CREATE TABLE user_carts (
        user_id TEXT NOT NULL,
        product_name TEXT NOT NULL,
        quantity INTEGER NOT NULL,
        PRIMARY KEY (user_id, product_name)
    )
    \"\"")

    # Copy data from the temporary table to the new user_carts table
    cursor.execute("INSERT INTO user_carts (user_id, product_name, quantity) SELECT user_id, product_id, quantity FROM temp_user_carts")

    # Drop the temporary table
    cursor.execute("DROP TABLE temp_user_carts")

    conn.commit()
    conn.close()

    # Copy data from the temporary table to the new user_carts table
    cursor.execute("INSERT INTO user_carts (user_id, product_name, quantity) SELECT user_id, product_id, quantity FROM temp_user_carts")

    # Drop the temporary table
    cursor.execute("DROP TABLE temp_user_carts")

    conn.commit()
    conn.close()
