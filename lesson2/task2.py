def write_order_to_json(file, order):
    import json

    with open(file, 'r', encoding='utf-8') as f:
        orders = json.load(f)
    orders['orders'].append(order)
    with open(file, 'w', encoding='utf-8') as f:
        json.dump(orders, f, indent=4)


if __name__ == '__main__':
    file = 'orders.json'
    order = {
        'item': 'трансформатор тока 200 А 6 кВ',
        'quantity': 18,
        'price': 21000,
        'buyer': 'ПАО "РОССЕТИ ЦЕНТР"',
        'date': "20.12.2021"
    }
    write_order_to_json(file, order)
