from pydantic import BaseModel
from datetime import datetime

from enums import *

class Order(BaseModel):
    """A model representing a trading order in the system.
    Supports both market and limit orders for buying and selling,
    with optional price and timestamp fields. Implements serialization
    methods for network transmission.
    
    Attributes:
        account_id (int): ID of the account placing the order
        side (OrderSide): Buy or sell indicator
        quantity (int): Number of shares to trade
        order_type (OrderType): Market or limit order type
        price (float | None): Limit price, or None for market orders
        timestamp (datetime | None): When the order was created
    """
    account_id: int
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
    


class Logger:
    """A simple file-based logging system.
    
    Provides timestamped logging of system events to a file,
    with automatic file creation and cleanup on startup.
    
    Attributes:
        filename (str): Path to the log file
    """
    def __init__(self, filename="logs.txt"):
        """Initialize the logger with a specified output file.
        Creates or clears the log file and writes an initial timestamp.
        
        Args:
            filename (str, optional): Path to the log file. Defaults to "logs.txt"
        """
        self.filename = filename
        # Clear the file on startup
        with open(self.filename, 'w') as f:
            f.write(f"=== Log started at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===\n\n")
    
    def log(self, message: str):
        """Write a timestamped message to the log file.
        
        Args:
            message (str): The message to be logged
        """
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        log_message = f"[{timestamp}] {message}\n"
        with open(self.filename, 'a') as f:
            f.write(log_message) 