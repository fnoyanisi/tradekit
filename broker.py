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
        if self.position.status == "PENDING":
            ##################################################################
            # submit the order to the broker API
            ##################################################################
            if (self.position.position_type == "LONG" and self.position.action == "BUY") or \
               (self.position.position_type == "SHORT" and self.position.action == "SELL"):
                self.position.status = "PENDING"
                self.position.entry_submit_date = datetime.now()
                self.position.entry_submit_price = self.position.entry_submit_price
            elif (self.position.position_type == "SHORT" and self.position.action == "BUY") or \
                 (self.position.position_type == "LONG" and self.position.action == "SELL"):
                self.position.status = "PENDING"
                self.position.exit_submit_date = datetime.now()
                self.position.exit_submit_price = self.position.exit_submit_price
            self.db.update_position(self.position)

            ##################################################################
            # execute the order throught the broker API
            ##################################################################
            if self.position.action == "BUY":
                if self.position.position_type == "LONG":
                    self.position.status = "OPEN"
                    self.position.entry_date = datetime.now()
                    self.position.entry_price = self.position.entry_submit_price
                elif self.position.position_type == "SHORT":
                    self.position.status = "CLOSED"
                    self.position.exit_date = datetime.now()
                    self.position.exit_price = self.position.exit_submit_price
                self.db.update_position(self.position)
                p = self.position.exit_submit_price or self.position.entry_submit_price
                print(f"Executed BUY order for {self.position.ticker} at {p}")
            elif self.position.action == "SELL":
                if self.position.position_type == "LONG":
                    self.position.status = "CLOSED"
                    self.position.exit_date = datetime.now()
                    self.position.exit_price = self.position.exit_submit_price  
                elif self.position.position_type == "SHORT":
                    self.position.status = "OPEN"
                    self.position.entry_date = datetime.now()
                    self.position.entry_price = self.position.entry_submit_price
                self.db.update_position(self.position)
                p = self.position.entry_submit_price or self.position.exit_submit_price
                print(f"Executed SELL order for {self.position.ticker} at {p}")
        else:
            print(f"Order for position id: {self.position.id} is not in PENDING status")
