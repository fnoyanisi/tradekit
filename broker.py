from datetime import datetime
import pandas as pd
from typing import Optional
from .models import TradeKitPosition
from .database import TradeKitDB

class TradeKitBroker:
    def __init__(self, db: TradeKitDB):
        self.db = db
        self.active_position = None
        self.cash = 0.0
        self.asset_holdings = 0
        self.commission = 0.0

    def deposit(self, amount: float):
        if amount < 0:
            raise ValueError("Deposit amount must be positive.")
        self.cash += amount

    def fund_assets(self, amount: float):
        if amount < 0:
            raise ValueError("Funding amount must be positive.")
        self.asset_holdings += amount

    def execute_order(self, trade_position: TradeKitPosition):
        """Execute the given order and update its status."""
        self.active_position = trade_position

        if self.active_position.status not in {"PENDING", "OPEN"}:
            raise ValueError(f"Order for position id: {self.active_position.id} is not in PENDING or OPEN status")

        try:
            self._submit_order_to_broker()
            self._finalize_order_execution()
        except Exception as e:
            raise RuntimeError(f"Error executing order for position id: {self.active_position.id}. Error: {e}")
        return self.active_position.position_size

    def _submit_order_to_broker(self):
        """Submit the order to the broker API."""
        self.active_position.status = "PENDING"
        if self.active_position.action == "BUY":
            self.active_position.entry_submit_date = datetime.now()
        elif self.active_position.action == "SELL":
            self.active_position.exit_submit_date = datetime.now()
        self.db.update_position(self.active_position)

    def _finalize_order_execution(self):
        """Finalize the order execution."""
        if self.active_position.action == "BUY":
            self._handle_buy_execution()
        elif self.active_position.action == "SELL":
            self._handle_sell_execution()

    def _handle_buy_execution(self):
        """Handle BUY order execution."""
        cost = self.active_position.entry_submit_price * self.active_position.position_size
        self.cash -= cost
        if self.cash < 0:
            self.cash += cost
            raise ValueError("Insufficient funds to execute the buy order.")
        self.asset_holdings += self.active_position.position_size

        if self.active_position.position_type == "LONG":
            self.active_position.status = "OPEN"
            self.active_position.entry_date = datetime.now()
            self.active_position.entry_price = self.active_position.entry_submit_price
        elif self.active_position.position_type == "SHORT":
            self.active_position.status = "CLOSED"
            self.active_position.exit_date = datetime.now()
            self.active_position.exit_price = self.active_position.exit_submit_price
        self.db.update_position(self.active_position)

    def _handle_sell_execution(self):
        """Handle SELL order execution."""
        proceeds = self.active_position.exit_submit_price * self.active_position.position_size
        self.asset_holdings -= self.active_position.position_size
        if self.asset_holdings < 0:
            self.asset_holdings += self.active_position.position_size
            raise ValueError("Insufficient shares to execute the sell order.")
        self.cash += proceeds

        if self.active_position.position_type == "LONG":
            self.active_position.status = "CLOSED"
            self.active_position.exit_date = datetime.now()
            self.active_position.exit_price = self.active_position.exit_submit_price
        elif self.active_position.position_type == "SHORT":
            self.active_position.status = "OPEN"
            self.active_position.entry_date = datetime.now()
            self.active_position.entry_price = self.active_position.entry_submit_price
        self.db.update_position(self.active_position)

