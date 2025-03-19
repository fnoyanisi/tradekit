from datetime import datetime
from typing import Optional

class TradeKitPosition:
    def __init__(
        self, 
        bot_name: str, 
        ticker: str, 
        trade_type: str,  # 'LONG' or 'SHORT'
        quantity: int, 
        action: str,  # 'BUY' or 'SELL'
        open_order_price: float, 
        order_type: str = "MARKET",  # 'LIMIT' or 'MARKET'
        status: str = "PENDING",  # 'PENDING', 'OPEN', 'PARTIAL', 'CLOSED', 'CANCELED', 'FAILED'
        open_order_date: Optional[datetime] = None, 
        open_date: Optional[datetime] = None, 
        open_price: Optional[float] = None, 
        close_order_date: Optional[datetime] = None, 
        close_order_price: Optional[float] = None, 
        close_date: Optional[datetime] = None, 
        close_price: Optional[float] = None,
        id: Optional[int] = None, 
    ):
        self.id = id  # Primary Key, can be None for new trades before DB assignment
        self.bot_name = bot_name
        self.ticker = ticker
        self.trade_type = trade_type  # 'LONG' or 'SHORT'
        self.quantity = quantity
        self.action = action  # 'BUY' or 'SELL'
        
        # Order details
        self.open_order_price = open_order_price
        self.open_order_date = open_order_date or datetime.now()
        
        # Trade execution details
        self.open_date = open_date
        self.open_price = open_price
        
        # Close details
        self.close_order_date = close_order_date
        self.close_order_price = close_order_price
        self.close_date = close_date
        self.close_price = close_price

        # Order type & status
        self.order_type = order_type  # 'LIMIT' or 'MARKET'
        self.status = status  # 'PENDING', 'OPEN', 'PARTIAL', 'CLOSED', 'CANCELED', 'FAILED'

    def place_open_order(self, price: float, order_type: str = "MARKET"):
        """Places an open order and updates order details."""
        self.open_order_price = price
        self.open_order_date = datetime.now()
        self.order_type = order_type
        self.status = "PENDING"

    def execute_open_order(self, price: float):
        """Executes the open order and updates open trade details."""
        self.open_price = price
        self.open_date = datetime.now()
        self.status = "OPEN"

    def place_close_order(self, price: float):
        """Places a close order and updates close order details."""
        self.close_order_price = price
        self.close_order_date = datetime.now()
        self.status = "PARTIAL" if self.status == "OPEN" else "PENDING"

    def execute_close_order(self, price: float):
        """Executes the close order and marks trade as closed."""
        self.close_price = price
        self.close_date = datetime.now()
        self.status = "CLOSED"

    def cancel_order(self):
        """Cancels an order before execution."""
        self.status = "CANCELED"

    def fail_order(self):
        """Marks an order as failed."""
        self.status = "FAILED"

    def to_dict(self):
        """Converts trade details into a dictionary for database storage."""
        return {
            "id": self.id,
            "bot_name": self.bot_name,
            "ticker": self.ticker,
            "trade_type": self.trade_type,
            "quantity": self.quantity,
            "action": self.action,
            "open_order_date": self.open_order_date.strftime('%Y-%m-%d %H:%M:%S') if self.open_order_date else None,
            "open_order_price": self.open_order_price,
            "open_date": self.open_date.strftime('%Y-%m-%d %H:%M:%S') if self.open_date else None,
            "open_price": self.open_price,
            "close_order_date": self.close_order_date.strftime('%Y-%m-%d %H:%M:%S') if self.close_order_date else None,
            "close_order_price": self.close_order_price,
            "close_date": self.close_date.strftime('%Y-%m-%d %H:%M:%S') if self.close_date else None,
            "close_price": self.close_price,
            "order_type": self.order_type,
            "status": self.status
        }

    def __repr__(self):
        return f"TradePosition({self.bot_name}, {self.ticker}, {self.trade_type}, {self.action}, {self.quantity}, Status: {self.status})"
