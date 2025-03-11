import pandas as pd
from typing import Callable
from typing import Optional
from .trade_position import TradePosition
from .trade_db import TradeDB

class TradeBot:
    def __init__(self, name: str, ticker: str, db: TradeDB):
        self.name = name
        self.ticker = ticker
        self.data = pd.DataFrame()
        self.commission = 0
        self.db = db
        self.position = None
        self.position_updated = False

    def load_data(self, data):
        """Load the historic trade data. Must include OHCL and volume information"""
        self.data = data.copy()
    
    def load_position(self):
        """Load the latest open position from the database"""
        self.position = self.db.get_latest_open_position(self.name, self.ticker)
        if self.position:
            self.position_updated = True

    def get_position(self):
        """Return the current trade position."""
        return self.position if self.position_updated else None

    def run(self, strategy: Optional[Callable[['TradeBot'], None]] = None):
        """
        Loads the latest position from the database and runs the strategy. 
        The strategy object is a function that expects exactly one argument of type 
        TradeBot and returns nothing. 
        """
        if strategy:
            self.strategy = strategy
            self.load_position()
            self.strategy(self)

    def strategy(self):
        """Implement your trading strategy here."""
        pass

    def buy(self, position_type: str, quantity: int, price: float):
        """Place a buy order. Only position_type is mandatory."""
        quantity = quantity or -1
        price = price or -1.0
        
        if position_type == "LONG":
            self.position = TradePosition(
                id=None,
                bot_name=self.name,
                ticker=self.ticker,
                trade_type=position_type,
                quantity=quantity,
                open_order_price=price,
                action="BUY"
                )
            self.position_updated = True
            print(self.position.to_dict())
            self.db.open_order(self.position)
        elif position_type == "SHORT":
            if self.position:
                self.position.place_order(price)
                self.position_updated = True
                self.db.close_trade(self.position)

    def sell(self, position_type: str, quantity: Optional[int] = None, price: Optional[float] = None):
        """Place a sell order. Only position_type is mandatory."""
        quantity = quantity or -1
        price = price or -1.0
        
        if position_type == "LONG":
            if self.position:
                self.position.place_order(price)
                self.position_updated = True
                self.db.close_trade(self.position)
        elif position_type == "SHORT":
            self.position = TradePosition(
                id=None,
                bot_name=self.name,
                ticker=self.ticker,
                trade_type=position_type,
                quantity=quantity,
                open_order_price=price,
                action="SELL"
            )
            self.position_updated = True
            self.db.open_order(self.position)
