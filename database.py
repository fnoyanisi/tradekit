import psycopg
from psycopg.rows import dict_row
from .models import TradeKitPosition

class TradeKitDB:
    def __init__(self, db_name, user, password, host="localhost", port=5432):
        self.db_name = db_name
        self.user = user
        self.password = password
        self.host = host
        self.port = port
        self.conn = None
        self.connect()
        self.create_table()

    def connect(self):
        """Establish database connection."""
        try:
            self.conn = psycopg.connect(
                dbname=self.db_name,
                user=self.user,
                password=self.password,
                host=self.host,
                port=self.port,
                row_factory=dict_row  # Fetch results as dictionaries
            )
            print("Connected to the database successfully.")
        except psycopg.Error as e:
            print(f"Error connecting to database: {e}")

    def create_table(self):
        """Create a trades table if it doesn't exist."""
        create_table_query = """
        CREATE TABLE IF NOT EXISTS trades (
            id SERIAL PRIMARY KEY,
            bot_name VARCHAR(50) NOT NULL,
            ticker VARCHAR(10) NOT NULL,
            trade_type VARCHAR(5) CHECK (trade_type IN ('LONG', 'SHORT')) NOT NULL DEFAULT 'LONG',
            quantity INT NOT NULL,
            action VARCHAR(4) CHECK (action IN ('BUY', 'SELL')) NOT NULL,
            open_order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            open_order_price NUMERIC(10,2) NOT NULL,
            open_date TIMESTAMP NULL,
            open_price NUMERIC(10, 2) NULL,
            close_order_date TIMESTAMP NULL,
            close_order_price NUMERIC(10,2) NULL,
            close_date TIMESTAMP NULL,
            close_price NUMERIC(10, 2) NULL,
            order_type VARCHAR(6) CHECK (order_type IN ('LIMIT', 'MARKET')) NOT NULL DEFAULT 'MARKET',
            status VARCHAR(9) CHECK (status IN ('PENDING', 'OPEN', 'PARTIAL', 'CLOSED', 'CANCELED', 'FAILED')) NOT NULL
        );
        """
        with self.conn.cursor() as cur:
            cur.execute(create_table_query)
            self.conn.commit()

    def open_order(self, trade_position : TradePosition):        
        """Insert a new open trade order into the database."""
        insert_query = """
        INSERT INTO trades (bot_name, ticker, trade_type, quantity, open_order_price, action, open_order_date, status)
        VALUES (%s, %s, %s, %s, %s, %s, %s, 'PENDING')
        RETURNING id;
        """
        with self.conn.cursor() as cur:
            cur.execute(insert_query, (trade_position.bot_name, 
                                       trade_position.ticker, 
                                       trade_position.trade_type,
                                       trade_position.quantity, 
                                       trade_position.open_order_price, 
                                       trade_position.action, 
                                       trade_position.open_order_date
                                    )
                        )
            trade_id = cur.fetchone()['id']
            self.conn.commit()
        return trade_id

    def close_order(self, trade_position: TradePosition, close_order_price, close_order_date):
        """Insert a new close trade order into the database."""
        update_query = """
        UPDATE trades
        SET close_order_price = %s, close_order_date = %s, status = 'PENDING'
        WHERE id = %s AND status = 'OPEN';
        """
        with self.conn.cursor() as cur:
            cur.execute(update_query, (close_order_price, close_order_date, trade_position.id))
            self.conn.commit()
            print(f"Close order placed for trade {trade_position.id} successfully.")

    def execute_open_trade(self, trade_position: TradePosition, open_price, open_date):
        """Update the trade with actual execution price and date for the open order."""
        update_query = """
        UPDATE trades
        SET open_price = %s, open_date = %s, status = 'OPEN'
        WHERE id = %s AND status = 'PENDING';
        """
        with self.conn.cursor() as cur:
            cur.execute(update_query, (open_price, open_date, trade_position.id))
            self.conn.commit()
            print(f"Open trade executed for {trade_position.id}.")

    def execute_close_trade(self, trade_position: TradePosition, close_price, close_date):
        """Update the trade with actual execution price and date for the close order."""
        update_query = """
        UPDATE trades
        SET close_price = %s, close_date = %s, status = 'CLOSED'
        WHERE id = %s AND status = 'PENDING';
        """
        with self.conn.cursor() as cur:
            cur.execute(update_query, (close_price, close_date, trade_position.id))
            self.conn.commit()
            print(f"Close trade executed for {trade_position.id}.")

    def get_latest_open_position(self, bot_name, ticker):
        """Fetch the latest open trade position for a bot on a specific ticker."""
        query = """
        SELECT id, bot_name, ticker, trade_type, quantity, action, open_order_date, open_order_price, 
            open_date, open_price, close_order_date, close_order_price, close_date, close_price, status
        FROM trades
        WHERE bot_name = %s AND ticker = %s AND status = 'OPEN'
        ORDER BY open_date DESC
        LIMIT 1;
        """
        with self.conn.cursor() as cur:
            cur.execute(query, (bot_name, ticker))
            row = cur.fetchone()
            
            if row:
                return TradePosition(
                    id=row["id"],
                    bot_name=row["bot_name"],
                    ticker=row["ticker"],
                    trade_type=row['trade_type'],
                    quantity=row["quantity"],
                    action=row["action"],
                    open_order_price=row["open_order_price"],
                    open_order_date=row["open_order_date"],
                    open_date=row["open_date"],
                    open_price=row["open_price"],
                    close_order_date=row["close_order_date"],
                    close_order_price=row["close_order_price"],
                    close_date=row["close_date"],
                    close_price=row["close_price"],
                    status=row["status"]
                )
            else:
                return None

    def get_last_position(self, bot_name, ticker):
        """Fetch the latest open trade position for a bot on a specific ticker."""
        query = """
        SELECT id, bot_name, ticker, trade_type, quantity, action, open_order_date, open_order_price, 
            open_date, open_price, close_order_date, close_order_price, close_date, close_price, status
        FROM trades
        WHERE bot_name = %s AND ticker = %s AND status != 'CLOSED'
        ORDER BY open_date DESC
        LIMIT 1;
        """
        with self.conn.cursor() as cur:
            cur.execute(query, (bot_name, ticker))
            row = cur.fetchone()
            
            if row:
                return TradePosition(
                    id=row["id"],
                    bot_name=row["bot_name"],
                    ticker=row["ticker"],
                    trade_type=row['trade_type'],
                    quantity=row["quantity"],
                    action=row["action"],
                    open_order_price=row["open_order_price"],
                    open_order_date=row["open_order_date"],
                    open_date=row["open_date"],
                    open_price=row["open_price"],
                    close_order_date=row["close_order_date"],
                    close_order_price=row["close_order_price"],
                    close_date=row["close_date"],
                    close_price=row["close_price"],
                    status=row["status"]
                )
            else:
                return None

    def get_all_trades(self):
        """Retrieve all trades from the database."""
        with self.conn.cursor() as cur:
            cur.execute("SELECT * FROM trades;")
            return cur.fetchall()

    def get_trades_by_bot(self, bot_name):
        """Retrieve trades made by a specific bot."""
        query = "SELECT * FROM trades WHERE bot_name = %s;"
        with self.conn.cursor() as cur:
            cur.execute(query, (bot_name,))
            return cur.fetchall()

    def get_trades_by_ticker(self, ticker):
        """Retrieve trades for a specific ticker."""
        query = "SELECT * FROM trades WHERE ticker = %s;"
        with self.conn.cursor() as cur:
            cur.execute(query, (ticker,))
            return cur.fetchall()

    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
            print("Database connection closed.")