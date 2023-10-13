import os
import logging
from logging.handlers import RotatingFileHandler
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from dotenv import load_dotenv
from database_utils import get_products_by_category
from database_utils import get_products_by_partial_category
from linebot.models import (
    MessageEvent,
    TextMessage,
    TextSendMessage,
    ButtonsTemplate,
    TemplateSendMessage,
    PostbackAction,
    URIAction,
)
from linebot.models import FlexSendMessage
from database_utils import get_product_price_by_name

load_dotenv()

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

    if received_msg.isdigit():
        # ここで、前回のメッセージ（商品名）を取得するロジックが必要です。
        # 例えば、セッションやデータベースを使用して前回のメッセージを保存しておくなどの方法が考えられます。
        previous_msg = "前回のメッセージを取得するロジック"
        reply = handle_quantity_message(event, int(received_msg), previous_msg)
    else:
        products_by_category = get_products_by_category(received_msg)

        if products_by_category:
            reply_msg = "\n".join([f"{product[0]}: {product[1]}" for product in products_by_category])
            reply = TextSendMessage(text=reply_msg)
        else:
            products_by_exact_name = get_products_by_partial_category(received_msg)
            if any(product[0] == received_msg for product in products_by_exact_name):
                # ここで、商品名をhandle_quantity_message関数に渡します。
                reply = handle_quantity_message(event, 1, received_msg)  # 1はデフォルトの数量として設定しています。
            else:
                reply_msg = "製品が見つかりませんでした。"
                reply = TextSendMessage(text=reply_msg)
    if isinstance(reply, TemplateSendMessage):
        line_bot_api.reply_message(event.reply_token, reply)
    else:
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply.text))


def handle_quantity_message(event, quantity, received_msg):
    # ボタンテンプレートの作成
    buttons_template = ButtonsTemplate(
        thumbnail_image_url="https://example.com/bot/images/image.jpg",
        title="選択した商品",
        text=f"{received_msg}を{quantity}つでよろしいでしょうか？",
        actions=[
            PostbackAction(label="買う", data=f"action=buy&quantity={quantity}"),
            PostbackAction(label="カートにいれる", data=f"action=add&quantity={quantity}"),
            URIAction(label="商品の詳細", uri="http://example.com/page/123"),
        ],
    )

    # テンプレートメッセージの作成
    template_message = TemplateSendMessage(alt_text=f"{quantity}でよろしいでしょうか？", template=buttons_template)

    # テンプレートメッセージを返す
    line_bot_api.reply_message(event.reply_token, template_message)


# Pseudo code to demonstrate the process


def handle_buy_action(event, product_name, quantity):
    # 1. Display Confirmation Screen using Flex Message
    product_price = get_product_price_by_name(product_name)
    total_price = product_price * quantity

    # Create a Flex Message content for the confirmation screen
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

    # Send the Flex Message
    line_bot_api.reply_message(event.reply_token, flex_message)

    # 2. If user clicks on the payment button (in this case, the "支払う" button),
    #    the postback data "action=pay" will be sent, which you can handle in another function.


# This is just a demonstration. The actual integration will need more considerations and details.


log_handler = RotatingFileHandler("flask_app.log", maxBytes=10000, backupCount=3)
log_handler.setLevel(logging.INFO)
app.logger.addHandler(log_handler)


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
