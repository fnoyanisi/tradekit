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
        self.buy_aggressiveness_levels = {
            "max": 1.0,         # 100%
            "moderate": 0.6,    # 60%
            "conservative": 0.4 # 40%
        }
        self.buy_aggressiveness = "moderate"

        # determines the % of assets that can be sold 
        # on a single trade. Default is "max"
        self.sell_aggressiveness_levels = {
            "max": 1.0,         # 100%
            "moderate": 0.6,    # 60%
            "conservative": 0.4 # 40%
        }
        self.sell_aggressiveness = "max"

    def set_buy_aggressiveness(self, level: str):
        if level in self.buy_aggressiveness_levels:
            self.buy_aggressiveness = level
        else:
            raise ValueError(f"Invalid aggressiveness level: {level}")
    
    def set_buy_aggressiveness_ratios(self, max_ratio: float, moderate_ratio: float, conservative_ratio: float):
        self.buy_aggressiveness_levels = {
            "max": max_ratio,
            "moderate": moderate_ratio,
            "conservative": conservative_ratio
        }

    def set_sell_aggressiveness(self, level: str):
        if level in self.sell_aggressiveness_levels:
            self.sell_aggressiveness = level
        else:
            raise ValueError(f"Invalid aggressiveness level: {level}")
    
    def set_sell_aggressiveness_ratios(self, max_ratio: float, moderate_ratio: float, conservative_ratio: float):
        self.sell_aggressiveness_levels = {
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

    def get_last_observed_exit_date(self):
        """Return the last observed exit date"""
        return self.db.get_last_observed_exit_date()

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

    def calculate_buy_quantity(self, price: float) -> int:
        """Determine how many shares to buy based on available cash and aggressiveness level."""
        ratio = self.buy_aggressiveness_levels[self.buy_aggressiveness]
        budget = self.cash * ratio
        budget_after_commission = budget * (1 - self.commission)
        quantity = int(budget_after_commission / price)
        return max(quantity, 0)
    
    def calculate_sell_quantity(self) -> int:
        """Determine how many shares to sell based on position size and sell aggressiveness level."""
        ratio = self.sell_aggressiveness_levels[self.sell_aggressiveness]
        quantity = int(self.position.position_size * ratio)
        return max(quantity, 0)

    def buy(self, position_type: str, price: float, observed_date: Optional[str] = None):
        """Place a buy order."""
        quantity = self.calculate_buy_quantity(price)
        if quantity > 0:
            if not self.position:
                # open a new position
                self.position = TradeKitPosition(
                    bot_name=self.name,
                    ticker=self.ticker,
                    position_type=position_type,
                    position_size=quantity,
                    observed_entry_date=observed_date,
                    entry_submit_price=price,
                    action="BUY"
                )
            else:
                # existing position
                self.position.action = "BUY"
                self.position.observed_exit_date = observed_date
            # the order hasn't been executed yet
            q = self.submit_order(position_type=position_type, price=price)
            self.position.position_size += q
            return q
        else:
            print("Not enough cash to place a trade: " + str(self.cash))
            return -1

    def sell(self, position_type: str, price: float, observed_date: Optional[str] = None):
        """Place a sell order."""
        quantity = self.calculate_sell_quantity()
        if quantity > 0:
            if not self.position:
                # open a new position
                self.position = TradeKitPosition(
                    bot_name=self.name,
                    ticker=self.ticker,
                    position_type=position_type,
                    position_size=quantity,
                    observed_entry_date=observed_date,
                    entry_submit_price=price,
                    action="SELL"
                )
            else:
                # existing position
                self.position.action = "SELL"
                self.position.observed_exit_date = observed_date
            # The order hasn't been executed yet
            q = self.submit_order(position_type=position_type, price=price)
            self.position.position_size -= q
            return q
        else:
            print("Not enough shares to sell: " + str(self.position.position_size))
            return -1

    def submit_order(self, position_type: str, price: float)->int:
        #Based on the position and order types, either update the database or create a new entry
        action = self.position.action
        position_type = self.position.position_type

        if action == "BUY" and position_type == "LONG":
            self.position.id = self.db.create_position(self.position)
        elif action == "BUY" and position_type == "SHORT":
            self.position.exit_submit_price = price
            self.db.update_position(self.position)
        elif action == "SELL" and position_type == "LONG":
            self.position.exit_submit_price = price
            self.db.update_position(self.position)
        elif action == "SELL" and position_type == "SHORT":
            self.position.id = self.db.create_position(self.position)

        # execute the order
        return self.broker.execute_order(trade_position=self.position)    

