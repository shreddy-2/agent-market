import time
import random

from enums import *

from order_book import OrderBook, Order
from clearing_house import ClearingHouse

if __name__ == "__main__":
    clearing_house = ClearingHouse()
    order_book = OrderBook()
    order_book.set_clearing_house(clearing_house)
    
    # order_book.populate_randomly(center_price=100, deviance=0.005, num_orders=20)
    order_book.populate_for_testing()

    print(f"\n{order_book}\n")
    order_book.print_table()

    market_order = Order(side=OrderSide.SELL, quantity=350, order_type=OrderType.MARKET, account_id=98)
    print(f"\nSending market order: {market_order}")
    order_book.send_order(market_order)
    market_order = Order(side=OrderSide.BUY, quantity=150, order_type=OrderType.MARKET, account_id=99)
    print(f"\nSending market order: {market_order}")
    order_book.send_order(market_order)
    # market_order = Order(side=OrderSide.SELL, quantity=100, order_type=OrderType.LIMIT, price=99.70)
    # print(f"\nSending market order: {market_order}")
    # order_book.send_order(market_order)
    
    # order_book.print_table()
    # market_order = Order(side=OrderSide.BUY, quantity=300, order_type=OrderType.LIMIT, price=100.20)
    # print(f"\nSending market order: {market_order}")
    # order_book.send_order(market_order)

    # order_book.print_table()
    # market_order = Order(side=OrderSide.SELL, quantity=250, order_type=OrderType.LIMIT, price=99.70)
    # print(f"\nSending market order: {market_order}")
    # order_book.send_order(market_order)

    print(f"\n{order_book}\n")
    order_book.print_table()

    clearing_house.clear_orders()