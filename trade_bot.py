import pandas as pd
from typing import Callable, Optional
from .trade_position import TradePosition
from .trade_db import TradeDB
from .trade_broker import TradeBroker

class TradeBot:
    def __init__(self, name: str, ticker: str, db: TradeDB, broker: TradeBroker):
        self.name = name
        self.ticker = ticker
        self.data = pd.DataFrame()
        self.broker = broker
        self.commission = 0
        self.db = db
        self.position = None
        self.position_updated = False
        self.cash = 0.0

        # determines the % of cash that can be spent 
        # on a single trade. Default is "moderate"
        self.aggressiveness_levels = {
            "max": 1.0,         # 100%
            "moderate": 0.6,    # 60%
            "conservative": 0.4 # 40%
        }
        self.aggressiveness = "moderate"

    def set_aggressiveness(self, level: str):
        if level in self.aggressiveness_levels:
            self.aggressiveness = level
        else:
            raise ValueError(f"Invalid aggressiveness level: {level}")
    
    def set_aggressiveness_ratios(self, max_ratio: float, moderate_ratio: float, conservative_ratio: float):
        self.aggressiveness_levels = {
            "max": max_ratio,
            "moderate": moderate_ratio,
            "conservative": conservative_ratio
        }

    def load_data(self, data):
        """Load the historic trade data. Must include OHLC and volume information."""
        if not isinstance(data, pd.DataFrame):
            raise ValueError("Data must be a Pandas DataFrame")

        required_columns = {'open', 'high', 'low', 'close', 'volume'}
        if not required_columns.issubset(data.columns):
            raise ValueError(f"Data must contain the following columns: {required_columns}")

        if not isinstance(data.index, pd.DatetimeIndex):
            try:
                data.index = pd.to_datetime(data.index)
            except Exception as e:
                raise ValueError("Index must be a datetime format.") from e

        self.data = data.copy()

    
    def load_position(self):
        """Load the latest open position from the database"""
        self.position = self.db.get_last_position(self.name, self.ticker)
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

    def calculate_quantity(self, price: float) -> int:
        """Determine how many shares to buy based on available cash and aggressiveness level."""
        ratio = self.aggressiveness_levels[self.aggressiveness]
        budget = self.cash * ratio
        budget_after_commission = budget * (1 - self.commission)
        quantity = int(budget_after_commission / price)
        return max(quantity, 0)

    def place_buy_order(self, position_type: str, price: float):
        """Place a buy order."""
        quantity = self.calculate_quantity(price)
        if quantity > 0:
            if position_type == "LONG":
                self.position = TradePosition(
                    bot_name=self.name,
                    ticker=self.ticker,
                    trade_type=position_type,
                    quantity=quantity,
                    open_order_price=price,
                    action="BUY"
                )
                self.position.place_open_order(price)
                self.position_updated = True
                self.db.open_order(self.position)
            elif position_type == "SHORT":
                if self.position:
                    self.position.place_close_order(price)
                    self.position_updated = True
                    self.db.close_trade(self.position)
        else:
            print("Not enough cash to place a trade: " + str(self.cash))

    def place_sell_order(self, position_type: str, quantity: int, price: float):
        """Place a sell order."""
        if position_type == "LONG":
            if self.position:
                self.position.place_close_order(price)
                self.position_updated = True
                self.db.close_trade(self.position)
        elif position_type == "SHORT":
            self.position = TradePosition(
                bot_name=self.name,
                ticker=self.ticker,
                trade_type=position_type,
                quantity=quantity,
                open_order_price=price,
                action="SELL"
            )
            self.position.place_open_order(price)
            self.position_updated = True
            self.db.open_order(self.position)

    def execute_order(self):
        """Execute the current order using the broker."""
        if self.position:
            self.broker.execute_order(self.position)
