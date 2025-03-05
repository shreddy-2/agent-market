import heapq
import random
from collections import deque
from rich.table import Table
from rich.console import Console

from clearing_house import ClearingHouse, ClearingOrder
from utils import Order, Logger
from enums import *

class OrderQueue:
    """A queue to store orders at a specific price level in the order book.
    Implements FIFO (First In, First Out) ordering for orders at the same price level,
    maintaining time priority. Uses a deque for O(1) append and pop operations.
    
    Attributes:
        order_queue (deque): Collection of orders at this price level
    """
    def __init__(self):
        """Initialize an order queue to store orders at a specific price level.
        Uses a deque data structure to maintain FIFO order of orders at the same price.
        """
        self.order_queue = deque()

    def add_order(self, order: Order):
        """Add an order to the back of the queue.
        
        Args:
            order (Order): The order to be added to the queue
        """
        self.order_queue.append(order)

    def peek_top_order(self) -> Order:
        """Return the first order in the queue without removing it.
        
        Returns:
            Order: The first order in the queue
        
        Raises:
            IndexError: If the queue is empty
        """
        return self.order_queue[0]
    
    def pop_top_order(self) -> Order:
        """Remove and return the first order in the queue.
        
        Returns:
            Order: The first order in the queue
        
        Raises:
            IndexError: If the queue is empty
        """
        return self.order_queue.popleft()

    def get_volume(self) -> int:
        """Calculate the total volume of all orders in the queue.
        
        Returns:
            int: Sum of quantities of all orders in the queue
        """
        return sum(order.quantity for order in self.order_queue)

class AskHeap:
    """A specialized heap structure for managing sell-side orders.
    Implements a min-heap to maintain price priority for ask orders (lowest price first),
    combined with a dictionary of OrderQueues to maintain time priority at each price level.
    
    Attributes:
        price_heap (list): Min-heap of prices for O(1) access to best ask
        order_dict (dict): Maps prices to OrderQueues containing orders at that price
    """
    def __init__(self):
        """Initialize an ask-side order heap.
        Uses a min-heap (ordered lowest to highest) to maintain price priority for asks, 
        with a dictionary mapping prices to OrderQueues for maintaining time priority at 
        each price level. The heap only contains prices, which point to the OrderQueue of
        orders at that price in the dictionary.
        """
        self.price_heap = []
        self.order_dict = {}

    def add_ask(self, order: Order):
        """Add a sell order to the ask heap.
        Creates a new price level if it doesn't exist, then adds the order to
        the appropriate OrderQueue maintaining price-time priority.
        
        Args:
            order (Order): The sell order to be added
        """
        order_price = order.price
        # Check if price exists
        if order_price not in self.order_dict:
            heapq.heappush(self.price_heap, order_price)
            self.order_dict[order_price] = OrderQueue()

        # Add the order to the OrderQueue
        self.order_dict[order_price].add_order(order)
        
    def peek_bottom_ask(self) -> Order | None:
        """Return the lowest-priced ask order without removing it.
        
        Returns:
            Order | None: The lowest-priced ask order, or None if no asks exist
        """
        if len(self.price_heap) == 0:
            return None
        order_price = self.price_heap[0]
        return self.order_dict[order_price].peek_top_order()

    def pop_bottom_ask(self) -> Order | None:
        """Remove and return the lowest-priced ask order.
        First pop order from OrderQueue, then remove the price from the heap if the OrderQueue is empty.
        
        Returns:
            Order | None: The lowest-priced ask order, or None if no asks exist
        """
        if len(self.price_heap) == 0:
            return None
        order_price = self.price_heap[0]
        order = self.order_dict[order_price].pop_top_order()
        
        # If OrderQueue is now empty, remove the price from the dictionary and heap
        if len(self.order_dict[order_price].order_queue) == 0:
            del self.order_dict[order_price]
            heapq.heappop(self.price_heap)
            
        return order
    
    def get_volume(self, price: float) -> int | None:
        """Get the total volume of orders at a specific price level.
        
        Args:
            price (float): The price level to check
            
        Returns:
            int | None: Total volume at the price level, or None if price doesn't exist
        """
        if price not in self.order_dict:
            return None
        return self.order_dict[price].get_volume()

class BidHeap:
    """A specialized heap structure for managing buy-side orders.
    Implements a max-heap (via negated values in a min-heap) to maintain price priority 
    for bid orders (highest price first), combined with a dictionary of OrderQueues 
    to maintain time priority at each price level.
    
    Attributes:
        price_heap (list): Min-heap of negated prices for O(1) access to best bid
        order_dict (dict): Maps prices to OrderQueues containing orders at that price
    """
    def __init__(self):
        """Initialize an buy-side order heap.
        Uses a min-heap (ordered highest to lowest) to maintain price priority for bids, 
        with a dictionary mapping prices to OrderQueues for maintaining time priority at 
        each price level. The heap only contains prices, which point to the OrderQueue of
        orders at that price in the dictionary.
        """
        self.price_heap = []
        self.order_dict = {}

    def add_bid(self, order: Order):
        """Add a buy order to the bid heap.
        Creates a new price level if it doesn't exist, then adds the order to
        the appropriate OrderQueue maintaining price-time priority.
        
        Args:
            order (Order): The buy order to be added
        """
        order_price = order.price
        # Check if price exists
        if order_price not in self.order_dict:
            heapq.heappush(self.price_heap, -order_price)   # Mult by -1 to convert min heap to max heap
            self.order_dict[order_price] = OrderQueue()

        # Add the order to the OrderQueue
        self.order_dict[order_price].add_order(order)
        
    def peek_top_bid(self) -> Order | None:
        """Return the highest-priced bid order without removing it.
        
        Returns:
            Order | None: The highest-priced bid order, or None if no bids exist
        """
        if len(self.price_heap) == 0:
            return None
        order_price = -1 * self.price_heap[0]
        return self.order_dict[order_price].peek_top_order()

    def pop_top_bid(self) -> Order | None:
        """Remove and return the highest-priced bid order.
        First pop order from OrderQueue, then remove the price from the heap if the OrderQueue is empty.
        
        Returns:
            Order | None: The highest-priced bid order, or None if no bids exist
        """
        if len(self.price_heap) == 0:
            return None
        order_price = -1 * self.price_heap[0]
        order = self.order_dict[order_price].pop_top_order()
        
        # If OrderQueue is now empty, remove the price from the dictionary and heap
        if len(self.order_dict[order_price].order_queue) == 0:
            del self.order_dict[order_price]
            heapq.heappop(self.price_heap)
            
        return order

    def get_volume(self, price: float) -> int | None:
        """Get the total volume of orders at a specific price level.
        
        Args:
            price (float): The price level to check
            
        Returns:
            int | None: Total volume at the price level, or None if price doesn't exist
        """
        if price not in self.order_dict:
            return None
        return self.order_dict[price].get_volume()


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
    def __init__(self):
        """Initialize the order book with separate heaps for bids and asks.
        The order book maintains price-time priority using heap structures containing queues of orders at each price level.
        """
        self.bid_heap = BidHeap()
        self.ask_heap = AskHeap()
        self.clearing_house = None
        self.logger = Logger()

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
                    self.logger.log(f"MARKET MAKER: Selling {order.quantity} at {top_bid.price:.2f}")
                    # print(f"Selling {order.quantity} at {top_bid.price:.2f}", end="\r")
                    co = ClearingOrder(buyside_account_id=top_bid.account_id, sellside_account_id=order.account_id, price=top_bid.price, quantity=order.quantity)
                    self.clearing_house.add_clearing_order(co)
                    self.bid_heap.pop_top_bid()
                    order.quantity = 0

                elif top_bid.quantity > order.quantity:
                    self.logger.log(f"MARKET MAKER: Selling {order.quantity} at {top_bid.price:.2f}")
                    # print(f"Selling {order.quantity} at {top_bid.price:.2f}", end="\r")
                    co = ClearingOrder(buyside_account_id=top_bid.account_id, sellside_account_id=order.account_id, price=top_bid.price, quantity=order.quantity)
                    self.clearing_house.add_clearing_order(co)
                    # Edit the top bid quantity in place in the heap
                    self.bid_heap.order_dict[top_bid.price].order_queue[0].quantity -= order.quantity
                    order.quantity = 0

                elif top_bid.quantity < order.quantity:
                    self.logger.log(f"MARKET MAKER: Selling {top_bid.quantity} at {top_bid.price:.2f}")
                    # print(f"Selling {top_bid.quantity} at {top_bid.price:.2f}", end="\r")
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
                    self.logger.log(f"MARKET MAKER: Buying {order.quantity} at {bottom_ask.price:.2f}")
                    # print(f"Buying {order.quantity} at {bottom_ask.price:.2f}", end="\r")
                    co = ClearingOrder(buyside_account_id=order.account_id, sellside_account_id=bottom_ask.account_id, price=bottom_ask.price, quantity=order.quantity)
                    self.clearing_house.add_clearing_order(co)
                    self.ask_heap.pop_bottom_ask()
                    order.quantity = 0

                elif bottom_ask.quantity > order.quantity:
                    self.logger.log(f"MARKET MAKER: Buying {order.quantity} at {bottom_ask.price:.2f}")
                    # print(f"Buying {order.quantity} at {bottom_ask.price:.2f}", end="\r")
                    co = ClearingOrder(buyside_account_id=order.account_id, sellside_account_id=bottom_ask.account_id, price=bottom_ask.price, quantity=order.quantity)
                    self.clearing_house.add_clearing_order(co)
                    # Edit the top bid quantity in place in the heap
                    self.ask_heap.order_dict[bottom_ask.price].order_queue[0].quantity -= order.quantity
                    order.quantity = 0
                    
                elif bottom_ask.quantity < order.quantity:
                    self.logger.log(f"MARKET MAKER: Buying {bottom_ask.quantity} at {bottom_ask.price:.2f}")
                    # print(f"Buying {bottom_ask.quantity} at {bottom_ask.price:.2f}", end="\r")
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

        id_counter = 1
        for price in ask_prices:
            self.send_order(Order(side=OrderSide.SELL, quantity=100, order_type=OrderType.LIMIT, price=price, account_id=id_counter))
            id_counter += 1
        for price in bid_prices:
            self.send_order(Order(side=OrderSide.BUY, quantity=100, order_type=OrderType.LIMIT, price=price, account_id=id_counter))
            id_counter += 1

    # ----------------- PRINTING METHODS -----------------  
    def print_table(self) -> Table:
        """Create a formatted table representation of the order book.
        Generates a rich Table object showing bid and ask volumes at each price level,
        with color coding to distinguish between bid, ask, and crossed prices.
        
        Returns:
            Table: A rich Table object containing the formatted order book
        """
        table = Table(title="Order Book")
        table.add_column("Bid Volume", justify="right", header_style="bold")
        table.add_column("Price", justify="center", header_style="bold")
        table.add_column("Ask Volume", justify="left", header_style="bold")
        
        # Get all unique prices from both heaps
        prices = set()
        for price in self.bid_heap.price_heap:
            prices.add(-price)  # Convert back to positive price
        for price in self.ask_heap.price_heap:
            prices.add(price)
        
        # Calculate midpoint if we have both bids and asks
        if self.bid_heap.price_heap and self.ask_heap.price_heap:
            highest_bid = -min(self.bid_heap.price_heap)  # Convert back to positive
            lowest_ask = min(self.ask_heap.price_heap)
            midpoint = (highest_bid + lowest_ask) / 2
            midpoint = round(midpoint, 2)  # Round to 2 decimal places
            prices.add(midpoint)

        # Sort prices in descending order
        sorted_prices = sorted(prices, reverse=True)
        
        # Add rows to table
        for price in sorted_prices:
            bid_volume = self.bid_heap.get_volume(price)
            ask_volume = self.ask_heap.get_volume(price)
            
            # Convert volumes to strings, empty if None
            bid_vol_str = str(bid_volume) if bid_volume is not None else ""
            ask_vol_str = str(ask_volume) if ask_volume is not None else ""

            if bid_vol_str == "" and ask_vol_str != "":
                table.add_row(f"{bid_vol_str}", f"[red]${price:.2f}[/red]", f"{ask_vol_str}")
            elif bid_vol_str != "" and ask_vol_str == "":
                table.add_row(f"{bid_vol_str}", f"[green]${price:.2f}[/green]", f"{ask_vol_str}")
            elif bid_vol_str != "" and ask_vol_str != "":
                table.add_row(f"{bid_vol_str}", f"[white]${price:.2f}[/white]", f"{ask_vol_str}")
            else:
                table.add_row(f"{bid_vol_str}", f"[sandy_brown]${price:.2f}[/sandy_brown]", f"{ask_vol_str}")
            
        return table
        
    def __str__(self) -> str:
        """Create a string representation of the order book.
        Shows all the individual orders at each price level for both the bid and ask sides.
        Useful for debugging and understanding the order book structure.
        
        Returns:
            str: A detailed string showing all orders in both the bid and ask sides
        """
        output_str = ""
        output_str += "Bids:"
        for price in self.bid_heap.price_heap:
            output_str += f"\n\t${-price}: "
            for order in self.bid_heap.order_dict[-price].order_queue:
                output_str += f"{order} "
        output_str += "\nAsks:"
        for price in self.ask_heap.price_heap:
            output_str += f"\n\t${price}: "
            for order in self.ask_heap.order_dict[price].order_queue:
                output_str += f"{order} "
        
        return output_str

            
            


