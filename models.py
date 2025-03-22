from datetime import datetime
from typing import Optional

class TradeKitPosition:
    def __init__(
        self, 
        bot_name: str, 
        ticker: str, 
        position_type: str,  # 'LONG' or 'SHORT'
        quantity: int, 
        action: str,  # 'BUY' or 'SELL'
        entry_submit_price: float, 
        order_type: str = "MARKET",  # 'LIMIT' or 'MARKET'
        status: str = "PENDING",  # 'PENDING', 'OPEN', 'PARTIAL', 'CLOSED', 'CANCELED', 'FAILED'
        entry_submit_date: Optional[datetime] = None, 
        entry_date: Optional[datetime] = None, 
        entry_price: Optional[float] = None, 
        exit_submit_date: Optional[datetime] = None, 
        exit_submit_price: Optional[float] = None, 
        exit_date: Optional[datetime] = None, 
        exit_price: Optional[float] = None,
        id: Optional[int] = None, 
        observed_date: Optional[datetime] = None
    ):
        self.id = id  # Primary Key, can be None for new trades before DB assignment
        self.bot_name = bot_name
        self.ticker = ticker
        self.position_type = position_type  # 'LONG' or 'SHORT'
        self.quantity = quantity
        self.action = action  # 'BUY' or 'SELL'
        self.observed_date = observed_date or datetime.now()
        
        # Order details
        self.entry_submit_price = entry_submit_price
        self.entry_submit_date = entry_submit_date or datetime.now()
        
        # Trade execution details
        self.entry_date = entry_date
        self.entry_price = entry_price
        
        # Close details
        self.exit_submit_date = exit_submit_date
        self.exit_submit_price = exit_submit_price
        self.exit_date = exit_date
        self.exit_price = exit_price

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
            "position_type": self.position_type,
            "quantity": self.quantity,
            "action": self.action,
            "entry_submit_date": self.entry_submit_date.strftime('%Y-%m-%d %H:%M:%S') if self.entry_submit_date else None,
            "entry_submit_price": self.entry_submit_price,
            "entry_date": self.entry_date.strftime('%Y-%m-%d %H:%M:%S') if self.entry_date else None,
            "entry_price": self.entry_price,
            "exit_submit_date": self.exit_submit_date.strftime('%Y-%m-%d %H:%M:%S') if self.exit_submit_date else None,
            "exit_submit_price": self.exit_submit_price,
            "exit_date": self.exit_date.strftime('%Y-%m-%d %H:%M:%S') if self.exit_date else None,
            "exit_price": self.exit_price,
            "order_type": self.order_type,
            "status": self.status
        }

    def __repr__(self):
        return f"TradeKitPosition({self.bot_name}, {self.ticker}, {self.observed_date}, {self.position_type}, {self.action}, {self.quantity}, Status: {self.status})"
