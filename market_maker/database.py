import sys
import os
# sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils import Order, Snapshot
from market_maker.clearing_house import ClearingHouse
from pydantic import BaseModel
from datetime import datetime
from collections import deque
from queue import Queue
import heapq



class Database:
    """A single database for the entire market maker.
    Contains all the order queues, heaps, and other data structures for both the order service and the data service.
    """
    def __init__(self):
        self.order_queue = OrderQueue()
        self.bid_heap = BidHeap()
        self.ask_heap = AskHeap()
        self.clearing_house = ClearingHouse()

        self.market_snapshot_queue = Queue()
        self.last_trade = (None, None)    # Price, volume
    
    def get_reference_price(self) -> float:
        """Get the reference price of the order book.
        Returns the midpoint of the highest bid and lowest ask.
        """
        if self.bid_heap.peek_top_bid() is None:
            return self.ask_heap.peek_bottom_ask().price
        
        if self.ask_heap.peek_bottom_ask() is None:
            return self.bid_heap.peek_top_bid().price
        
        reference_price = (self.bid_heap.peek_top_bid().price + self.ask_heap.peek_bottom_ask().price) / 2
        return round(reference_price, 3)
    
    def get_snapshot(self) -> dict:
        """Get a snapshot of the market.
        Returns a dictionary containing the reference price, last trade info, top bid and ask, and timestamp.
        """
        return Snapshot(
            reference_price=self.get_reference_price(),
            last_trade_price=self.last_trade[0],
            last_trade_volume=self.last_trade[1],
            top_bid=self.bid_heap.peek_top_bid(),
            top_ask=self.ask_heap.peek_bottom_ask(),
            timestamp=datetime.now()
        )
    
    def snapshot(self):
        """Snapshot the market and add it to the queue."""
        snapshot = self.get_snapshot()
        self.market_snapshot_queue.put(snapshot)


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
    
    def get_sorted_prices(self):
        """Get a list of prices sorted in descending order.
        
        Returns:
            list: List of prices sorted in descending order
        """
        return sorted(self.order_dict.keys(), reverse=True)

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
    
    def get_sorted_prices(self):
        """Get a list of prices sorted in descending order.
        
        Returns:
            list: List of prices sorted in descending order
        """
        return sorted(self.order_dict.keys(), reverse=True)
