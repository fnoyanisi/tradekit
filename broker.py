from datetime import datetime
import pandas as pd
from typing import Optional
from .models import TradeKitPosition
from .database import TradeKitDB

class TradeKitBroker:
    def __init__(self, db: TradeKitDB):
        self.db = db
        self.position = None

    def execute_order(self, trade_position: TradeKitPosition):
        """Execute the given order and update its status."""
        self.position = trade_position

        if self.position.status not in {"PENDING", "OPEN"}:
            raise ValueError(f"Order for position id: {self.position.id} is not in PENDING or OPEN status")

        try:
            self._submit_order_to_broker()
            self._finalize_order_execution()
        except Exception as e:
            raise RuntimeError(f"Error executing order for position id: {self.position.id}. Error: {e}")
        return self.position.position_size

    def _submit_order_to_broker(self):
        """Submit the order to the broker API."""
        self.position.status = "PENDING"
        if self.position.action == "BUY":
            self.position.entry_submit_date = datetime.now()
        elif self.position.action == "SELL":
            self.position.exit_submit_date = datetime.now()
        self.db.update_position(self.position)

    def _finalize_order_execution(self):
        """Finalize the order execution."""
        if self.position.action == "BUY":
            self._handle_buy_execution()
        elif self.position.action == "SELL":
            self._handle_sell_execution()

    def _handle_buy_execution(self):
        """Handle BUY order execution."""
        if self.position.position_type == "LONG":
            self.position.status = "OPEN"
            self.position.entry_date = datetime.now()
            self.position.entry_price = self.position.entry_submit_price
        elif self.position.position_type == "SHORT":
            self.position.status = "CLOSED"
            self.position.exit_date = datetime.now()
            self.position.exit_price = self.position.exit_submit_price
        self.db.update_position(self.position)

    def _handle_sell_execution(self):
        """Handle SELL order execution."""
        if self.position.position_type == "LONG":
            self.position.status = "CLOSED"
            self.position.exit_date = datetime.now()
            self.position.exit_price = self.position.exit_submit_price
        elif self.position.position_type == "SHORT":
            self.position.status = "OPEN"
            self.position.entry_date = datetime.now()
            self.position.entry_price = self.position.entry_submit_price
        self.db.update_position(self.position)

