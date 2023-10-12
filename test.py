from database_utils import get_products_by_category


def main():
    received_msg = "納豆"
    products = get_products_by_category(received_msg)

    if products:
        reply_msg = "\n".join([f"{product[0]}: {product[1]}" for product in products])
    else:
        reply_msg = "該当する商品が見つかりませんでした。"

    print(reply_msg)

if __name__ == '__main__':
    main()
