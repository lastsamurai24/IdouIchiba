from database_utils import get_products_by_category
from database_utils import get_products_by_partial_category
from linebot.models import TemplateSendMessage, CarouselTemplate, CarouselColumn# Mocking the required imports and functions for the example
class TextSendMessage:
    def __init__(self, text):
        self.text = text

class MockEvent:
    def __init__(self, message_text, reply_token):
        self.message = type("Message", (object,), {"text": message_text})
        self.reply_token = reply_token

def line_bot_api_reply_message(token, message):
    print(f"[Reply to {token}]: {message.text}")

line_bot_api = type("LineBotAPI", (object,), {"reply_message": line_bot_api_reply_message})

# Actual combined function
def handle_message_combined(event):
    received_msg = event.message.text
    
    # Check if received message is a number (quantity)
    if received_msg.isdigit():
        reply_msg = handle_quantity_message(event, int(received_msg))
    else: 
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

# Mocking the handle_quantity_message for the demonstration
def handle_quantity_message(event, quantity):
    return f"Mocked response for quantity {quantity}"

# Test the combined function
mock_event = MockEvent(message_text="5", reply_token="testToken")
handle_message_combined(mock_event)
