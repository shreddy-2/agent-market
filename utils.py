from pydantic import BaseModel
from datetime import datetime
import json

from enums import *

class Order(BaseModel):
    account_id: int
    side: OrderSide
    quantity: int
    order_type: OrderType
    price: float | None = None
    timestamp: datetime | None = None

    def __str__(self):
        if self.timestamp is not None:
            if self.order_type == OrderType.MARKET:
                return f"(({self.account_id}) [{self.timestamp.strftime('%H:%M:%S.%f')}] {self.side.name} {self.quantity} MARKET)"
            else:
                return f"(({self.account_id}) [{self.timestamp.strftime('%H:%M:%S.%f')}] {self.side.name} {self.quantity} LIMIT ${self.price:.2f})"
        else:
            if self.order_type == OrderType.MARKET:
                return f"(({self.account_id}) {self.side.name} {self.quantity} MARKET)"
            else:
                return f"(({self.account_id}) {self.side.name} {self.quantity} LIMIT ${self.price:.2f})"
            
    def model_dump(self):
        return {
            "account_id": self.account_id,
            "side": self.side.name,
            "quantity": self.quantity,
            "order_type": self.order_type.name,
            "price": self.price,
            "timestamp": self.timestamp.isoformat() if self.timestamp is not None else None
        }
    
    @classmethod
    def model_validate_json(cls, order_dict: dict):
        account_id = order_dict["account_id"]
        side = OrderSide[order_dict["side"]]
        quantity = order_dict["quantity"]
        order_type = OrderType[order_dict["order_type"]]
        price = order_dict["price"]
        # timestamp = datetime.strptime(order_dict["timestamp"], '%H:%M:%S.%f') if order_dict["timestamp"] is not None else None
        timestamp = datetime.fromisoformat(order_dict["timestamp"]) if order_dict["timestamp"] is not None else None
        return cls(account_id=account_id, side=side, quantity=quantity, order_type=order_type, price=price, timestamp=timestamp)