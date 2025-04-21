from enum import Enum
from pydantic import BaseModel
from datetime import datetime
import uuid
from faker import Faker
faker = Faker()

from enums import OrderSide, OrderType

def mini_uuid():
    return str(uuid.uuid4())[:6]
    # return faker.name()

class MessageType(str, Enum):
    ORDER = "order"
    ORCHESTRATOR_COMMAND = "orchestrator_command"
    ORCHESTRATOR_RESPONSE = "orchestrator_response"
    DATA_SNAPSHOT = "data_snapshot"



class Order(BaseModel):
    """A model representing a trading order in the system.
    Supports both market and limit orders for buying and selling,
    with optional price and timestamp fields. Implements serialization
    methods for network transmission.
    
    Attributes:
        account_id (str): ID of the account placing the order
        side (OrderSide): Buy or sell indicator
        quantity (int): Number of shares to trade
        order_type (OrderType): Market or limit order type
        price (float | None): Limit price, or None for market orders
        timestamp (datetime | None): When the order was created
    """
    account_id: str
    side: OrderSide
    quantity: int
    order_type: OrderType
    price: float | None = None
    timestamp: datetime | None = None

    def __str__(self):
        if self.timestamp is not None:
            if self.order_type == OrderType.MARKET:
                return f"([{self.timestamp.strftime('%H:%M:%S.%f')}] ({self.account_id}) {self.side.name} {self.quantity} MARKET)"
            else:
                return f"([{self.timestamp.strftime('%H:%M:%S.%f')}] ({self.account_id}) {self.side.name} {self.quantity} LIMIT ${self.price:.2f})"
        else:
            if self.order_type == OrderType.MARKET:
                return f"(({self.account_id}) {self.side.name} {self.quantity} MARKET)"
            else:
                return f"(({self.account_id}) {self.side.name} {self.quantity} LIMIT ${self.price:.2f})"
            
    def model_dump(self):
        """Convert the order to a dictionary format for serialization.
        Timestamp is converted to ISO format.
        
        Returns:
            dict: Dictionary representation of the order
        """
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
        """Class method to create an Order instance from a dictionary representation.
        Timestamp is converted from an ISO format string back to a datetime object.

        Args:
            order_dict (dict): Dictionary containing order data
            
        Returns:
            Order: New Order instance
        """
        account_id = order_dict["account_id"]
        side = OrderSide[order_dict["side"]]
        quantity = order_dict["quantity"]
        order_type = OrderType[order_dict["order_type"]]
        price = order_dict["price"]
        # timestamp = datetime.strptime(order_dict["timestamp"], '%H:%M:%S.%f') if order_dict["timestamp"] is not None else None
        timestamp = datetime.fromisoformat(order_dict["timestamp"]) if order_dict["timestamp"] is not None else None
        return cls(account_id=account_id, side=side, quantity=quantity, order_type=order_type, price=price, timestamp=timestamp)
    

    
class Snapshot(BaseModel):
    timestamp: datetime
    reference_price: float
    last_trade_price: float
    last_trade_volume: int
    top_bid: Order
    top_ask: Order

    def __str__(self):
        return f"{self.timestamp}: ${self.reference_price:.3f} (BID ({self.top_bid.quantity} @ ${self.top_bid.price:.2f}) / ASK ({self.top_ask.quantity} @ ${self.top_ask.price:.2f})) - TRADE {self.last_trade_volume} @ ${self.last_trade_price:.2f} "
    
    def model_dump(self):
        return {
            "timestamp": self.timestamp.isoformat(),
            "reference_price": self.reference_price,
            "last_trade_price": self.last_trade_price,
            "last_trade_volume": self.last_trade_volume,
            "top_bid": self.top_bid.model_dump(),
            "top_ask": self.top_ask.model_dump()
        }



class Message(BaseModel):
    message_type: MessageType
    data: dict | Order | Snapshot

    def __str__(self):
        return f"{self.message_type}: {self.data}"
    
    def model_dump(self):
        return {
            "message_type": self.message_type.name,
            "data": self.data.model_dump()
        }



