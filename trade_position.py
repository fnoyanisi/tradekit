from datetime import datetime

class TradePosition:
    def __init__(self, pid:int, bot_name: str, ticker: str, quantity: float, price: float, action: str):
        self.pid = None # Primary Key
        self.bot_name = bot_name
        self.ticker = ticker  # Stock symbol (e.g., AAPL)
        self.quantity = quantity  # Number of shares
        self.price = price  # Buy/Sell price
        self.action = action  # "BUY" or "SELL"
        self.open_date = datetime.now()  # Time when position was opened
        self.close_date = None  # Time when position is closed
        self.close_price = None  # Price when closed
        self.status = "OPEN"  # "OPEN" or "CLOSED"

    def close(self, close_price: float):
        """Closes the trade position and records the closing price & time."""
        self.close_date = datetime.now()
        self.close_price = close_price
        self.status = "CLOSED"

    def to_dict(self):
        """Converts the object to a dictionary (useful for database storage)."""
        return {
            "pid": self.pid,
            "bot_name": self.bot_name,
            "ticker": self.ticker,
            "quantity": self.quantity,
            "price": self.price,
            "action": self.action,
            "open_date": self.open_date.strftime('%Y-%m-%d %H:%M:%S'),
            "close_date": self.close_date.strftime('%Y-%m-%d %H:%M:%S') if self.close_date else None,
            "close_price": self.close_price,
            "status": self.status
        }