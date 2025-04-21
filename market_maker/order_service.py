import logging
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils import OrderSide, OrderType, mini_uuid
from market_maker.database import Database, Order
from market_maker.clearing_house import ClearingOrder, ClearingHouse

import random

logger = logging.getLogger(__name__)

class OrderBook:
    """A limit order book implementation with price-time priority.
    Maintains separate heaps for bids and asks, providing efficient order matching
    and market making operations. Supports both limit and market orders, with
    automatic matching of crossed orders.
    
    Attributes:
        bid_heap (BidHeap): Manages all buy orders
        ask_heap (AskHeap): Manages all sell orders
        clearing_house (ClearingHouse): Processes matched trades
        logger (Logger): Handles logging of order book operations
    """
    def __init__(self, database: Database):
        """Initialize the order book with separate heaps for bids and asks.
        The order book maintains price-time priority using heap structures containing queues of orders at each price level.
        """
        self.bid_heap = database.bid_heap
        self.ask_heap = database.ask_heap
        self.clearing_house = database.clearing_house
        # self.logger = Logger()

    def set_clearing_house(self, clearing_house: ClearingHouse):
        """Set the clearing house for the order book.
        All matched trades are sent to this clearing house for processing.
        
        Args:
            clearing_house (ClearingHouse): The clearing house to be set
        """
        self.clearing_house = clearing_house

    def send_order(self, order: Order):
        """Process an incoming order and route it to appropriate handler.
        
        Args:
            order (Order): The order to be processed
            
        Raises:
            ValueError: If the order type is invalid
        """
        if order.order_type == OrderType.LIMIT:
            self.handle_limit_order(order)
        elif order.order_type == OrderType.MARKET:
            self.handle_market_order(order)

    def handle_limit_order(self, order: Order):
        """Process a limit order, either adding it to the book or executing it.
        If the order does not cross the spread, it is added to the appropriate side of the book,
        otherwise it is treated as a market order and executed immediately.
        
        Args:
            order (Order): The limit order to be processed
            
        Raises:
            ValueError: If the order side is invalid
        """
        if order.side == OrderSide.BUY:
            if not self.crossed_spread(order):
                self.bid_heap.add_bid(order)
            else:
                self.handle_market_order(order)

        elif order.side == OrderSide.SELL:
            if not self.crossed_spread(order):
                self.ask_heap.add_ask(order)
            else:
                self.handle_market_order(order)

        else:
            raise ValueError("Invalid order side")

    def handle_market_order(self, order: Order):
        """Execute a market order against existing orders in the book.
        Matches the order against the best available prices until either the order
        is fully filled or no matching orders remain.
        
        Args:
            order (Order): The market order to be executed
            
        Raises:
            ValueError: If no matching orders exist to fill the market order
        """
        if order.side == OrderSide.SELL:
            while order.quantity > 0:
                top_bid = self.bid_heap.peek_top_bid()
                
                # If order has a price, then a limit order
                # Stop processing if the order price is greater than the top bid and add the order to the order book
                if order.price is not None:
                    if order.price > top_bid.price:
                        self.handle_limit_order(order)
                        return

                if top_bid is None:
                    raise ValueError("No bids to fill market order")
                
                if top_bid.quantity == order.quantity:
                    logger.info(f"MARKET MAKER: Selling {order.quantity} at {top_bid.price:.2f}")
                    co = ClearingOrder(buyside_account_id=top_bid.account_id, sellside_account_id=order.account_id, price=top_bid.price, quantity=order.quantity)
                    self.clearing_house.add_clearing_order(co)
                    self.bid_heap.pop_top_bid()
                    order.quantity = 0

                elif top_bid.quantity > order.quantity:
                    logger.info(f"MARKET MAKER: Selling {order.quantity} at {top_bid.price:.2f}")
                    co = ClearingOrder(buyside_account_id=top_bid.account_id, sellside_account_id=order.account_id, price=top_bid.price, quantity=order.quantity)
                    self.clearing_house.add_clearing_order(co)
                    # Edit the top bid quantity in place in the heap
                    self.bid_heap.order_dict[top_bid.price].order_queue[0].quantity -= order.quantity
                    order.quantity = 0

                elif top_bid.quantity < order.quantity:
                    logger.info(f"MARKET MAKER: Selling {top_bid.quantity} at {top_bid.price:.2f}")
                    co = ClearingOrder(buyside_account_id=top_bid.account_id, sellside_account_id=order.account_id, price=top_bid.price, quantity=top_bid.quantity)
                    self.clearing_house.add_clearing_order(co)
                    order.quantity -= top_bid.quantity
                    self.bid_heap.pop_top_bid()

        elif order.side == OrderSide.BUY:
            while order.quantity > 0:
                bottom_ask = self.ask_heap.peek_bottom_ask()
                
                # If order has a price, then a limit order
                # Stop processing if the order price is less than the bottom ask and add the order to the order book
                if order.price is not None:
                    if order.price < bottom_ask.price:
                        self.handle_limit_order(order)
                        return

                if bottom_ask is None:
                    raise ValueError("No asks to fill market order")
                
                if bottom_ask.quantity == order.quantity:
                    logger.info(f"MARKET MAKER: Buying {order.quantity} at {bottom_ask.price:.2f}")
                    co = ClearingOrder(buyside_account_id=order.account_id, sellside_account_id=bottom_ask.account_id, price=bottom_ask.price, quantity=order.quantity)
                    self.clearing_house.add_clearing_order(co)
                    self.ask_heap.pop_bottom_ask()
                    order.quantity = 0

                elif bottom_ask.quantity > order.quantity:
                    logger.info(f"MARKET MAKER: Buying {order.quantity} at {bottom_ask.price:.2f}")
                    co = ClearingOrder(buyside_account_id=order.account_id, sellside_account_id=bottom_ask.account_id, price=bottom_ask.price, quantity=order.quantity)
                    self.clearing_house.add_clearing_order(co)
                    # Edit the top bid quantity in place in the heap
                    self.ask_heap.order_dict[bottom_ask.price].order_queue[0].quantity -= order.quantity
                    order.quantity = 0
                    
                elif bottom_ask.quantity < order.quantity:
                    logger.info(f"MARKET MAKER: Buying {bottom_ask.quantity} at {bottom_ask.price:.2f}")
                    co = ClearingOrder(buyside_account_id=order.account_id, sellside_account_id=bottom_ask.account_id, price=bottom_ask.price, quantity=bottom_ask.quantity)
                    self.clearing_house.add_clearing_order(co)
                    order.quantity -= bottom_ask.quantity
                    self.ask_heap.pop_bottom_ask()

    def crossed_spread(self, order: Order) -> bool:
        """Check if an order crosses the current bid-ask spread,
        i.e., if a buy order is at a price greater than the lowest ask or a sell order is at a price less than the highest bid.
        
        Args:
            order (Order): The order to check
            
        Returns:
            bool: True if the order crosses the spread, False otherwise
        """
        if order.side == OrderSide.BUY:
            bottom_ask = self.ask_heap.peek_bottom_ask()
            if bottom_ask is None:
                return False
            return order.price > bottom_ask.price
        
        elif order.side == OrderSide.SELL:
            top_bid = self.bid_heap.peek_top_bid()
            if top_bid is None:
                return False
            return order.price < top_bid.price
        
    def get_reference_price(self) -> float:
        """Get the reference price of the order book.
        Returns the midpoint of the highest bid and lowest ask.
        """
        if self.bid_heap.peek_top_bid() is None:
            return self.ask_heap.peek_bottom_ask().price
        
        if self.ask_heap.peek_bottom_ask() is None:
            return self.bid_heap.peek_top_bid().price
        
        return (self.bid_heap.peek_top_bid().price + self.ask_heap.peek_bottom_ask().price) / 2

    # ----------------- POPULATING ORDER BOOK -----------------
    def populate_randomly(self, center_price: float, deviance: float, num_orders: int):
        """Populate the order book with random orders around a center price.
        Creates a balanced book with both buy and sell orders, randomly distributed
        around the center price within the specified deviance. It is guaranteed that 
        none of the orders will cross the spread.
        
        Args:
            center_price (float): The middle price point for order distribution
            deviance (float): Maximum percentage deviation from center price
            num_orders (int): Total number of orders to generate
        """
        for _ in range(num_orders):
            side = random.choice([OrderSide.BUY, OrderSide.SELL])

            price_offset = random.uniform(0, center_price * deviance)
            if side == OrderSide.BUY:
                price = center_price - price_offset
            else:
                price = center_price + price_offset
            price = round(price, 2)

            quantity = random.randint(2, 50) * 10
            self.send_order(Order(side=side, quantity=quantity, order_type=OrderType.LIMIT, price=price))

    def populate_for_testing(self):
        """Populate the order book with a predetermined set of orders.
        Creates a symmetric order book with equal numbers of buy and sell orders
        at regular price intervals, useful for testing order matching logic and
        easy to read as a human.
        """
        center_price = 100
        num_sell_orders = 10
        num_buy_orders = 10

        # Generate two orders at each price
        ask_prices = [round(center_price + ((i + 1) * 0.10), 2) for i in range(num_sell_orders // 2)] * 2
        bid_prices = [round(center_price - ((i + 1) * 0.10), 2) for i in range(num_buy_orders // 2)] * 2

        for price in ask_prices:
            self.send_order(Order(side=OrderSide.SELL, quantity=100, order_type=OrderType.LIMIT, price=price, account_id=mini_uuid()))
            # agent_counter += 1
        for price in bid_prices:
            self.send_order(Order(side=OrderSide.BUY, quantity=100, order_type=OrderType.LIMIT, price=price, account_id=mini_uuid()))
            # agent_counter += 1

        logger.info(f"MARKET MAKER: Order book populated for testing\n {self} \n")

    # ----------------- PRINTING METHODS -----------------  
    # def print_table(self) -> Table:
    #     """Create a formatted table representation of the order book.
    #     Generates a rich Table object showing bid and ask volumes at each price level,
    #     with color coding to distinguish between bid, ask, and crossed prices.
        
    #     Returns:
    #         Table: A rich Table object containing the formatted order book
    #     """
    #     table = Table(title="Order Book")
    #     table.add_column("Bid Volume", justify="right", header_style="bold")
    #     table.add_column("Price", justify="center", header_style="bold")
    #     table.add_column("Ask Volume", justify="left", header_style="bold")
        
    #     # Get all unique prices from both heaps
    #     prices = set()
    #     for price in self.bid_heap.price_heap:
    #         prices.add(-price)  # Convert back to positive price
    #     for price in self.ask_heap.price_heap:
    #         prices.add(price)
        
    #     # Calculate midpoint if we have both bids and asks
    #     if self.bid_heap.price_heap and self.ask_heap.price_heap:
    #         highest_bid = -min(self.bid_heap.price_heap)  # Convert back to positive
    #         lowest_ask = min(self.ask_heap.price_heap)
    #         midpoint = (highest_bid + lowest_ask) / 2
    #         midpoint = round(midpoint, 2)  # Round to 2 decimal places
    #         prices.add(midpoint)

    #     # Sort prices in descending order
    #     sorted_prices = sorted(prices, reverse=True)
        
    #     # Add rows to table
    #     for price in sorted_prices:
    #         bid_volume = self.bid_heap.get_volume(price)
    #         ask_volume = self.ask_heap.get_volume(price)
            
    #         # Convert volumes to strings, empty if None
    #         bid_vol_str = str(bid_volume) if bid_volume is not None else ""
    #         ask_vol_str = str(ask_volume) if ask_volume is not None else ""

    #         if bid_vol_str == "" and ask_vol_str != "":
    #             table.add_row(f"{bid_vol_str}", f"[red]${price:.2f}[/red]", f"{ask_vol_str}")
    #         elif bid_vol_str != "" and ask_vol_str == "":
    #             table.add_row(f"{bid_vol_str}", f"[green]${price:.2f}[/green]", f"{ask_vol_str}")
    #         elif bid_vol_str != "" and ask_vol_str != "":
    #             table.add_row(f"{bid_vol_str}", f"[white]${price:.2f}[/white]", f"{ask_vol_str}")
    #         else:
    #             table.add_row(f"{bid_vol_str}", f"[sandy_brown]${price:.2f}[/sandy_brown]", f"{ask_vol_str}")
            
    #     return table
        
    def __str__(self) -> str:
        """Create a string representation of the order book.
        Shows all the individual orders at each price level for both the bid and ask sides.
        Useful for debugging and understanding the order book structure.
        Prices are sorted in descending order, top to bottom.
        
        Returns:
            str: A detailed string showing all orders in both the bid and ask sides
        """
        output_str = ""

        output_str += "Asks:"
        idx = 0
        for price in self.ask_heap.get_sorted_prices():
            if idx == 0:
                output_str += f"  ${price:.2f}: "
            else:
                output_str += f"\n\t${price:.2f}: "
            for order in self.ask_heap.order_dict[price].order_queue:
                output_str += f"{order} "
            idx += 1

        output_str += f"\nRef:    ${self.get_reference_price():.3f}"

        output_str += f"\nBids:"
        idx = 0
        for price in self.bid_heap.get_sorted_prices():
            if idx == 0:
                output_str += f"   ${price:.2f}: "
            else:
                output_str += f"\n\t${price:.2f}: "
            for order in self.bid_heap.order_dict[price].order_queue:
                output_str += f"{order} "
            idx += 1
       
        return output_str