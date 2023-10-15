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

DATABASE_PATH = '' 

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


@handler.add(PostbackEvent)
# カートを模倣する簡易的なデータ構造


def add_to_cart(user_id, product_name, quantity):
    """カートに商品を追加する関数"""
    cart = user_carts.get(user_id, {})
    cart[product_name] = cart.get(product_name, 0) + quantity
    user_carts[user_id] = cart
    app.logger.info(f"Updated cart for user {user_id}: {cart}")


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
# 既存のPostbackイベントのハンドラ
@handler.add(PostbackEvent)
def handle_postback(event):
    postback_data = event.postback.data

    # Postbackデータからaction, product, およびquantityを取得
    params = dict([item.split('=') for item in postback_data.split('&')])
    action = params.get('action')
    product = params.get('product')
    quantity = int(params.get('quantity', 0))
    if action == "increase":
        # 数量を1つ増やす
        update_cart_quantity(event.source.user_id, product, quantity + 1)
    elif action == "decrease" and quantity > 0:
        # 数量を1つ減らす
        update_cart_quantity(event.source.user_id, product, quantity - 1)
    # 更新されたカートの内容を表示
        send_updated_cart(event, event.source.user_nid)

def send_updated_cart(event, user_id):
    cart_contents = get_cart_contents(user_id)
    if not cart_contents:
        # カートが空の場合のメッセージを送信
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text="カートは空です。"))
        return

    # カートの内容を表示するためのメッセージを作成・送信
    # ここで modified_handle_view_cart 関数のようなロジックを利用して、
    # Flexメッセージを作成・送信することができます。

def update_cart_quantity(user_id, product_name, new_quantity):
    # データベースに接続
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    # 指定されたuser_idとproduct_nameに一致するエントリの数量を取得
    cursor.execute("""
        SELECT quantity FROM cart WHERE user_id = ? AND product_name = ?
    """, (user_id, product_name))

    result = cursor.fetchone()

    if result:
        # 既にエントリが存在する場合は、数量を更新
        cursor.execute("""
            UPDATE cart
            SET quantity = ?
            WHERE user_id = ? AND product_name = ?
        """, (new_quantity, user_id, product_name))
    else:
        # エントリが存在しない場合は、新しいエントリを追加
        cursor.execute("""
            INSERT INTO cart (user_id, product_name, quantity)
            VALUES (?, ?, ?)
        """, (user_id, product_name, new_quantity))

    # 変更をコミット
    conn.commit()

    # データベース接続を閉じる
    conn.close()


def modified_handle_view_cart(event, user_id):
    cart_contents = get_cart_contents(user_id)
    
    if not cart_contents:
        # カートが空の場合の既存のコード
        return

    receipt_cart_items = []
    for product, qty in cart_contents.items():
        product_price = get_product_price_by_name(product)
        subtotal = product_price * qty
        
        # Add the buttons for increasing and decreasing the quantity
        quantity_buttons = {
            "type": "box",
            "layout": "horizontal",
            "contents": [
                {
                    "type": "button",
                    "action": {
                        "type": "postback",
                        "label": "-",
                        "data": f"action=decrease&product={product}&quantity={qty}"
                    },
                    "style": "primary",
                    "color": "#ff0000"
                },
                {
                    "type": "text",
                    "text": f"{qty}つ",
                    "gravity": "center"
                },
                {
                    "type": "button",
                    "action": {
                        "type": "postback",
                        "label": "+",
                        "data": f"action=increase&product={product}&quantity={qty}"
                    },
                    "style": "primary",
                    "color": "#00ff00"
                }
            ]
        }
        
        receipt_cart_items.extend([
            {"type": "text", "text": f"商品名: {product}"},
            {"type": "text", "text": f"価格: {product_price}円"},
            quantity_buttons,
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

# Since the function refers to external methods, we won't be able to execute it here directly.
# We are providing the modified function as a code snippet.



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
