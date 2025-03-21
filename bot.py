import pandas as pd
from typing import Callable, Optional
from .models import TradeKitPosition
from .database import TradeKitDB
from .broker import TradeKitBroker

class TradeKitBot:
    def __init__(self, name: str, ticker: str, db: TradeKitDB, broker: TradeKitBroker):
        self.name = name
        self.ticker = ticker
        self.data = pd.DataFrame()
        self.broker = broker
        self.commission = 0
        self.db = db
        self.position = None
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

    def deposit(self, amount: float):
        if amount < 0:
            raise ValueError("Deposit amount must be positive.")
        self.cash += amount

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

    def get_position(self):
        """Return the current trade position."""
        return self.position

    def run(self, strategy: Optional[Callable[['TradeKitBot'], None]] = None):
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

    def buy(self, position_type: str, price: float, observed_date: Optional[str] = None):
        """Place a buy order."""
        quantity = self.calculate_quantity(price)
        if quantity > 0:
            if not self.position:
                self.position = TradeKitPosition(
                    bot_name=self.name,
                    ticker=self.ticker,
                    position_type=position_type,
                    quantity=quantity,
                    observed_date=observed_date,
                    entry_submit_price=price,
                    action="BUY"
                )
            # the order hasn't been executed yet
            self.submit_order(position_type=position_type, price=price)
            return quantity
        else:
            print("Not enough cash to place a trade: " + str(self.cash))
            return -1

    def sell(self, position_type:str, quantity: int, price: float, observed_date: Optional[str] = None):
        """Place a sell order."""
        if not self.position:
            self.position = TradeKitPosition(
                bot_name=self.name,
                ticker=self.ticker,
                position_type=position_type,
                quantity=quantity,
                observed_date=observed_date,
                entry_submit_price=price,
                action="SELL"
            )
            return quantity
        self.submit_order(position_type=position_type, price=price)

    def submit_order(self, position_type: str, price: float):
        #Based on the position and order types, either update the database or create a new entry
        action = self.position.action
        position_type = self.position.position_type

        if action == "BUY" and position_type == "LONG":
            self.position.id = self.db.create_position(self.position)
        elif action == "BUY" and position_type == "SHORT":
            self.db.update_position(self.position)
        elif action == "SELL" and position_type == "LONG":
            self.position.id = self.db.create_position(self.position)
        elif action == "SELL" and position_type == "SHORT":
            self.db.update_position(self.position)

        # execute the order
        self.broker.execute_order(trade_position=self.position)    

