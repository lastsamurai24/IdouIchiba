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
    
    # First, perform the original handle_message process
    products_by_category = get_products_by_category(received_msg)
    
    if products_by_category:
        reply_msg = "\n".join([f"{product[0]}: {product[1]}" for product in products_by_category])
    else:
        # If no products found with the original method, try handle_message_updated process
        products_by_exact_name = get_products_by_partial_category(received_msg)
        if any(product[0] == received_msg for product in products_by_exact_name):
            reply_msg = f"いくつ{received_msg}を買いますか？"
        else:
            reply_msg = "製品が見つかりませんでした。"
    
    # Send the reply message
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_msg))

# Displaying the combined function for reference
handle_message_combined


log_handler = RotatingFileHandler("flask_app.log", maxBytes=10000, backupCount=3)
log_handler.setLevel(logging.INFO)
app.logger.addHandler(log_handler)


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
