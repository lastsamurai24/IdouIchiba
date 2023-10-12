from database_utils import get_products_by_category
from database_utils import get_products_by_category
from database_utils import get_products_by_partial_category

def main():
    received_msg = "納豆の極み"
    products = get_products_by_partial_category(received_msg)
    
    # If there's an exact match in the products list
    if any(product[0] == received_msg for product in products):
        reply_msg = f"いくつ{received_msg}を買いますか？"
    else:
        reply_msg = "製品が見つかりませんでした。"

    print(reply_msg)

if __name__ == '__main__':
    main()
