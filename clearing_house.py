from pydantic import BaseModel


class ClearingOrder(BaseModel):
    buyside_account_id: int
    sellside_account_id: int
    price: float
    quantity: int

class ClearingHouse:
    def __init__(self):
        self.clearing_orders = []

    def add_clearing_order(self, order: ClearingOrder):
        self.clearing_orders.append(order)

    def clear_orders(self):
        for order in self.clearing_orders:
            if order.buyside_account_id == order.sellside_account_id:
                continue
        
            print(f"Clearing order -> Sending {order.quantity} shares from {order.sellside_account_id} to {order.buyside_account_id} at ${order.price:.2f} for ${order.quantity * order.price:.2f}")
        
        self.clearing_orders = []