from enum import Enum

class OrderSide(Enum):
    BUY = "Buy"
    SELL = "Sell"

class OrderType(Enum):
    LIMIT = "Limit"
    MARKET = "Market"