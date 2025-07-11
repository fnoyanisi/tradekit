import pandas as pd
from typing import Callable, Optional, Literal
from .models import TradeKitPosition
from .database import TradeKitDB
from .broker import TradeKitBroker

class TradeKitBot:
    def __init__(
        self,
        name: str,
        ticker: str,
        db: TradeKitDB,
        broker: TradeKitBroker,
        mode: Literal["live", "backtest"] = "live"
    ):
        """ 
        TradeKitBot is a class that represents a trading bot. It is responsible for managing the trading strategy,
        executing trades, and interacting with the broker and the database.
        It includes methods for loading data, calculating trade quantities, and placing orders.
        """
        self.name = name
        self.ticker = ticker
        self.broker = broker
        if mode not in ["live", "backtest"]:
            raise ValueError(f"Invalid mode: {mode}")
        self.mode = mode
        self.data = pd.DataFrame()
        self.db = db
        self.position = None

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

        # whether stop the trade or buy/sell with the available resurces
        # adjust - buy/sell with the available resources
        # skip - skip the trade
        # halt - stop the trade        
        self.insufficient_resources_policy_values = {
            "adjust",
            "skip",
            "halt"
        }
        self.insufficient_resources_policy = "adjust"

    def set_buy_aggressiveness(self, level: str):
        """Set the aggressiveness level for buying. Must be one of 'max', 'moderate', or 'conservative'."""
        if level in self.buy_aggressiveness_levels:
            self.buy_aggressiveness = level
        else:
            raise ValueError(f"Invalid aggressiveness level: {level}")
    
    def set_buy_aggressiveness_ratios(self, max_ratio: float, moderate_ratio: float, conservative_ratio: float):
        """Set the aggressiveness ratios for buying. Must be between 0 and 1."""
        if not (0 <= max_ratio <= 1 and 0 <= moderate_ratio <= 1 and 0 <= conservative_ratio <= 1):
            raise ValueError("Aggressiveness ratios must be between 0 and 1.")
        if not (max_ratio >= moderate_ratio >= conservative_ratio):
            raise ValueError("Aggressiveness ratios must be in descending order.")
        self.buy_aggressiveness_levels = {
            "max": max_ratio,
            "moderate": moderate_ratio,
            "conservative": conservative_ratio
        }

    def set_sell_aggressiveness(self, level: str):
        """Set the aggressiveness level for selling. Must be one of 'max', 'moderate', or 'conservative'."""
        if level in self.sell_aggressiveness_levels:
            self.sell_aggressiveness = level
        else:
            raise ValueError(f"Invalid aggressiveness level: {level}")
    
    def set_sell_aggressiveness_ratios(self, max_ratio: float, moderate_ratio: float, conservative_ratio: float):
        """Set the aggressiveness ratios for selling. Must be between 0 and 1."""
        if not (0 <= max_ratio <= 1 and 0 <= moderate_ratio <= 1 and 0 <= conservative_ratio <= 1):
            raise ValueError("Aggressiveness ratios must be between 0 and 1.")
        if not (max_ratio >= moderate_ratio >= conservative_ratio):
            raise ValueError("Aggressiveness ratios must be in descending order.")
        self.sell_aggressiveness_levels = {
            "max": max_ratio,
            "moderate": moderate_ratio,
            "conservative": conservative_ratio
        }

    def set_insufficient_resources_policy(self, policy: str):
        """
        Set the policy for handling insufficient resources. Must be one of 'adjust', 'skip', or 'halt'.
        'adjust' - buy/sell with the available resources
        'skip' - skip the trade
        'halt' - stop the trade
        """
        if policy not in self.insufficient_resources_policy_values:
            raise ValueError(f"Invalid policy: {policy}. Must be one of {self.insufficient_resources_policy_values}")
        self.insufficient_resources_policy = policy

    def load_data(self, data):
        """Load the historic trade data. The dataframe must include OHLC and volume information as well as an index of type datetime."""
        if not isinstance(data, pd.DataFrame):
            raise TypeError("Data must be a Pandas DataFrame")

        required_columns = {'open', 'high', 'low', 'close', 'volume'}
        if not required_columns.issubset(data.columns):
            raise KeyError(f"Data must contain the following columns: {required_columns}")

        if not isinstance(data.index, pd.DatetimeIndex):
            try:
                data.index = pd.to_datetime(data.index)
            except Exception as e:
                raise ValueError("Index must be a datetime format.") from e

        self.data = data.copy()

    def get_last_observed_exit_date(self):
        """Return the last observed exit date."""
        return self.db.get_last_observed_exit_date()

    def load_position(self):
        """Load the latest open position for the ticker symbol from the database."""
        self.position = self.db.get_last_position(self.name, self.ticker)

    def get_position(self):
        """Return the current trade position for the ticker symbol"""
        return self.position

    def get_latest_open_position(self):
        """Return the latest open position for the ticker symbol from the database."""
        return self.db.get_latest_open_position(self.name, self.ticker)

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

    def enforce_quantity_policy(self, quantity: int, trade_type: str) -> int:
        """It's not recommended to call this method directly. It is used internally to enforce the quantity policy."""
        if quantity > 0:
            return quantity

        policy = self.insufficient_resources_policy
        if policy == "adjust":
            return 0
        elif policy == "skip":
            return 0
        elif policy == "halt":
            raise RuntimeError(f"Cannot execute {trade_type} trade: insufficient resources.")
        else:
            raise ValueError(f"Invalid insufficient_resources_policy: {policy}")

    def calculate_buy_quantity(self, price: float) -> int:
        """Determine how many shares to buy based on available cash and aggressiveness level."""
        ratio = self.buy_aggressiveness_levels[self.buy_aggressiveness]
        budget = self.broker.cash * ratio
        budget_after_commission = budget * (1 - self.broker.commission)
        quantity = int(budget_after_commission / price)
        return self.enforce_quantity_policy(quantity, trade_type="buy")

    def calculate_sell_quantity(self) -> int:
        """Determine how many shares to sell based on position size and sell aggressiveness level."""
        if self.position is None and self.broker.asset_holdings == 0:
            raise RuntimeError("No open position to sell.")
        ratio = self.sell_aggressiveness_levels[self.sell_aggressiveness]
        q = self.position.quantity if self.position else self.broker.asset_holdings
        quantity = int(q * ratio)
        return self.enforce_quantity_policy(quantity, trade_type="sell")

    def buy(self, position_type: Literal["LONG","SHORT"], price: float, observed_date: Optional[str] = None, stop_loss: Optional[float] = None, take_profit: Optional[float] = None):
        """Place a buy order. Returns the number of assets bought or None if no assets were bought."""
        return self.place_order(   
            action="BUY",
            position_type=position_type,
            price=price,
            observed_date=observed_date,
            stop_loss=stop_loss,
            take_profit=take_profit
        )

    def sell(self, position_type: Literal["LONG","SHORT"], price: float, observed_date: Optional[str] = None, stop_loss: Optional[float] = None, take_profit: Optional[float] = None):
        """Place a sell order. Returns the number of assets sold or None if no assets were sold."""
        return self.place_order(
            action="SELL",
            position_type=position_type,
            price=price,
            observed_date=observed_date,
            stop_loss=stop_loss,
            take_profit=take_profit
        )

    def place_order(self, action: Literal["BUY","SELL"], position_type: Literal["LONG","SHORT"], price: float, observed_date: Optional[str] = None, stop_loss: Optional[float] = None, take_profit: Optional[float] = None):
        """Place a buy or sell order. It's not recommended to call this method directly."""
        if price <= 0:
            raise ValueError("Price must be greater than 0")

        quantity = self.calculate_buy_quantity(price) if action == "BUY" else self.calculate_sell_quantity()
        if quantity == 0 and self.insufficient_resources_policy == "skip":
            return

        if self.position is None or self.position.status == "CLOSED":
            # Open a new position
            self.position = TradeKitPosition(
                bot_name=self.name,
                ticker=self.ticker,
                position_type=position_type,
                quantity=quantity,
                observed_entry_date=observed_date,
                entry_submit_price=price,
                stop_loss=stop_loss,
                take_profit=take_profit,
                action=action
            )
        else:
            # Update existing position
            self.position.action = action
            self.position.observed_exit_date = observed_date

        try:
            executed_quantity = self.submit_order(position_type=position_type, price=price)
            self.position.quantity -= executed_quantity
            return executed_quantity
        except Exception as e:
            raise RuntimeError(f"Error placing {action} order: {e}")

    def submit_order(self, position_type: str, price: float)->int:
        """ Based on the position and order types, either update the database or create a new entry"""
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

