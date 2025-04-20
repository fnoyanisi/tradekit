from datetime import datetime
from typing import Optional, Literal

class TradeKitPosition:
    VALID_POSITION_TYPES = ["LONG", "SHORT"]
    VALID_ACTIONS = ["BUY", "SELL"]
    VALID_STATUSES = ["PENDING", "OPEN", "PARTIAL", "CLOSED", "CANCELED", "FAILED"]
    VALID_ORDER_TYPES = ["LIMIT", "MARKET"]

    def __init__(
        self, 
        bot_name: str, 
        ticker: str, 
        position_type: Literal["LONG", "SHORT"],
        position_size: int, 
        action: Literal["BUY", "SELL"],
        entry_submit_price: float, 
        order_type: Literal["LIMIT", "MARKET"] = "MARKET",
        status: Literal["PENDING", "OPEN", "PARTIAL", "CLOSED", "CANCELED", "FAILED"] = "PENDING",
        entry_submit_date: Optional[datetime] = None, 
        entry_date: Optional[datetime] = None, 
        entry_price: Optional[float] = None, 
        exit_submit_date: Optional[datetime] = None, 
        exit_submit_price: Optional[float] = None, 
        exit_date: Optional[datetime] = None, 
        exit_price: Optional[float] = None,
        exit_reason: Optional[str] = None,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None,
        id: Optional[int] = None, 
        observed_entry_date: Optional[datetime] = None,
        observed_exit_date: Optional[datetime] = None
    ):
        self.id = id  # Primary Key, can be None for new trades before DB assignment
        if not (1 <= len(bot_name) <= 50):  
            raise ValueError("Bot name must be between 1 and 50 characters")
        self.bot_name = bot_name
        if not (1 <= len(ticker) <= 30):  
            raise ValueError("Ticker must be between 1 and 30 characters")
        if not ticker.isalnum():
            raise ValueError("Ticker must be alphanumeric")
        self.ticker = ticker
        if position_type not in self.VALID_POSITION_TYPES:
            raise ValueError(f"Invalid position_type: {position_type}. Must be one of {self.VALID_POSITION_TYPES}")
        self.position_type = position_type
        if position_size <= 0:
            raise ValueError(f"Invalid position_size: {position_size}. Must be greater than 0")
        self.position_size = position_size
        if action not in self.VALID_ACTIONS:
            raise ValueError(f"Invalid action: {action}. Must be one of {self.VALID_ACTIONS}")
        self.action = action
        self.observed_entry_date = observed_entry_date or datetime.now()
        self.observed_exit_date = observed_exit_date or None

        # risk management
        self.stop_loss = stop_loss  # Optional stop loss price
        self.take_profit = take_profit  # Optional take profit price

        # order details
        if entry_submit_price and entry_submit_price <= 0:
            raise ValueError(f"Invalid entry_submit_price: {entry_submit_price}. Must be greater than 0")
        self.entry_submit_price = entry_submit_price
        self.entry_submit_date = entry_submit_date or datetime.now()
        
        # trade execution details
        self.entry_date = entry_date
        if entry_price and entry_price <= 0:
            raise ValueError(f"Invalid entry_price: {entry_price}. Must be greater than 0")
        self.entry_price = entry_price
        
        # close details
        self.exit_submit_date = exit_submit_date
        if exit_submit_price and exit_submit_price <= 0:
            raise ValueError(f"Invalid exit_submit_price: {exit_submit_price}. Must be greater than 0")
        self.exit_submit_price = exit_submit_price
        self.exit_date = exit_date
        if exit_price and exit_price <= 0:
            raise ValueError(f"Invalid exit_price: {exit_price}. Must be greater than 0")
        self.exit_price = exit_price
        if exit_reason and not (1 <= len(exit_reason) <= 50):  
            raise ValueError("Exit reason must be between 1 and 50 characters")
        self.exit_reason = exit_reason or None

        # order type & status
        if order_type not in self.VALID_ORDER_TYPES:
            raise ValueError(f"Invalid order_type: {order_type}. Must be one of {self.VALID_ORDER_TYPES}")  
        self.order_type = order_type
        if status not in self.VALID_STATUSES:
            raise ValueError(f"Invalid status: {status}. Must be one of {self.VALID_STATUSES}") 
        self.status = status

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
            "stop_loss": self.stop_loss,
            "take_profit": self.take_profit,
            "entry_submit_date": self.entry_submit_date.strftime('%Y-%m-%d %H:%M:%S') if self.entry_submit_date else None,
            "entry_submit_price": self.entry_submit_price,
            "entry_date": self.entry_date.strftime('%Y-%m-%d %H:%M:%S') if self.entry_date else None,
            "entry_price": self.entry_price,
            "exit_submit_date": self.exit_submit_date.strftime('%Y-%m-%d %H:%M:%S') if self.exit_submit_date else None,
            "exit_submit_price": self.exit_submit_price,
            "exit_date": self.exit_date.strftime('%Y-%m-%d %H:%M:%S') if self.exit_date else None,
            "exit_price": self.exit_price,
            "exit_reason": self.exit_reason,
            "order_type": self.order_type,
            "status": self.status
        }

    def __repr__(self):
        return f"TradeKitPosition(id: {self.id}, \
                                    name: {self.bot_name}, \
                                    ticker: {self.ticker}, \
                                    type: {self.position_type}, \
                                    action:{self.action},\
                                    Status: {self.status} \
        )"
