from datetime import datetime
from typing import Optional

class TradeKitPosition:
    def __init__(
        self, 
        bot_name: str, 
        ticker: str, 
        observed_date: Optional[datetime], 
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
        self.observed_date = observed_date or datetime.now()
        
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

    def to_dict(self):
        """Converts trade details into a dictionary for database storage."""
        return {
            "id": self.id,
            "bot_name": self.bot_name,
            "ticker": self.ticker,
            "observed_date": self.observed_date.strftime('%Y-%m-%d %H:%M:%S') if self.observed_date else None,
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
        return f"TradePosition({self.bot_name}, {self.ticker}, {self.observed_date}, {self.trade_type}, {self.action}, {self.quantity}, Status: {self.status})"
