from database_utils import get_products_by_category
from database_utils import get_products_by_category
from database_utils import get_products_by_partial_category
from database_utils import get_product_price_by_name
from linebot.models import FlexSendMessage
def main(event, product_name, quantity):
    product_price = get_product_price_by_name(product_name)
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
   


    print()

if __name__ == '__main__':
