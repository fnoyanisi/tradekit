import pandas as pd
from typing import Optional
from .models import TradeKitPosition
from .database import TradeKitDB

class TradeKitBroker:
    def __init__(self, db: TradeKitDB):
        self.db = db

    def execute_order(self, position: TradeKitPosition, price: float):
        """Execute the given order and update its status."""
        if position.status == "PENDING":
            if position.action == "BUY":
                position.execute_open_order(price)
                self.db.execute_open_trade(position, price, datetime.now())
                print(f"Executed BUY order for {position.ticker} at {price}")
            elif position.action == "SELL":
                position.execute_close_order(price)
                self.db.execute_close_trade(position, price, datetime.now())
                print(f"Executed SELL order for {position.ticker} at {price}")
        else:
            print(f"Order for {position.ticker} is not in PENDING status")

    def cancel_order(self, position: TradeKitPosition):
        """Cancel the given order."""
        if position.status == "PENDING":
            position.cancel_order()
            self.db.update_order_status(position.id, "CANCELED")
            print(f"Canceled order for {position.ticker}")
        else:
            print(f"Order for {position.ticker} is not in PENDING status")

    def fail_order(self, position: TradeKitPosition):
        """Mark the given order as failed."""
        if position.status == "PENDING":
            position.fail_order()
            self.db.update_order_status(position.id, "FAILED")
            print(f"Failed order for {position.ticker}")
        else:
            print(f"Order for {position.ticker} is not in PENDING status")