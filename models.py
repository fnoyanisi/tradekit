from datetime import datetime
from typing import Optional

class TradeKitPosition:
    def __init__(
        self, 
        bot_name: str, 
        ticker: str, 
        position_type: str,  # 'LONG' or 'SHORT'
        position_size: int, 
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
        observed_entry_date: Optional[datetime] = None,
        observed_exit_date: Optional[datetime] = None
    ):
        self.id = id  # Primary Key, can be None for new trades before DB assignment
        self.bot_name = bot_name
        self.ticker = ticker
        self.position_type = position_type  # 'LONG' or 'SHORT'
        self.position_size = position_size
        self.action = action  # 'BUY' or 'SELL'
        self.observed_entry_date = observed_entry_date or datetime.now()
        self.observed_exit_date = observed_exit_date or None
        
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
            "observed_entry_date": self.observed_entry_date.strftime('%Y-%m-%d %H:%M:%S') if self.observed_entry_date else None,
            "observed_exit_date": self.observed_exit_date.strftime('%Y-%m-%d %H:%M:%S') if self.observed_exit_date else None,
            "position_type": self.position_type,
            "position_size": self.position_size,
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
        return f"TradeKitPosition({self.bot_name}, {self.ticker}, {self.observed_entry_date}, {self.observed_entry_date}, {self.position_type}, {self.action}, {self.position_size}, Status: {self.status})"
