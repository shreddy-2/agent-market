from pydantic import BaseModel


class ClearingOrder(BaseModel):
    """A model representing a matched trade ready for clearing.
    
    Contains all necessary information for processing the transfer of
    assets between the buyer and seller accounts.
    
    Attributes:
        buyside_account_id (int): Account ID of the buyer
        sellside_account_id (int): Account ID of the seller
        price (float): Execution price of the trade
        quantity (int): Number of shares traded
    """
    buyside_account_id: int
    sellside_account_id: int
    price: float
    quantity: int

class ClearingHouse:
    """A clearing house that processes matched trades.
    Manages the settlement process for trades matched in the order book,
    ensuring proper transfer of assets between accounts. Currently implements
    a simple printing of trades, but designed to be extended with actual
    clearing functionality.
    
    Attributes:
        clearing_orders (list): Collection of trades waiting to be cleared
    """
    def __init__(self):
        """Initialize the clearing house for processing matched trades. 
        Orders to be cleared are stored in a standard list.
        """
        self.clearing_orders = []

    def add_clearing_order(self, order: ClearingOrder):
        """Add a matched trade for clearing.
        
        Args:
            order (ClearingOrder): The matched trade to be cleared
        """
        self.clearing_orders.append(order)

    def clear_orders(self):
        """Process all pending clearing orders.
        Executes the transfer of shares and funds between accounts,
        skipping self-trades where buyer and seller are the same.
        Currently just prints the order.
        """
        for order in self.clearing_orders:
            if order.buyside_account_id == order.sellside_account_id:
                continue
        
            # TODO: Implement an actual clearing system connected to TradingAgent accounts
            print(f"Clearing order -> Sending {order.quantity} shares from {order.sellside_account_id} to {order.buyside_account_id} at ${order.price:.2f} for ${order.quantity * order.price:.2f}")
        
        self.clearing_orders = []