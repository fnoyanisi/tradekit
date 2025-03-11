import psycopg
from psycopg.rows import dict_row
from .trade_position import TradePosition

class TradeDB:
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
            quantity INT NOT NULL,
            price NUMERIC(10, 2) NOT NULL,
            action VARCHAR(4) CHECK (action IN ('BUY', 'SELL')) NOT NULL,
            open_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            close_date TIMESTAMP NULL,
            close_price NUMERIC(10, 2) NULL,
            status VARCHAR(6) CHECK (status IN ('OPEN', 'CLOSED')) NOT NULL
        );
        """
        with self.conn.cursor() as cur:
            cur.execute(create_table_query)
            self.conn.commit()

    def create_trade(self, bot_name, ticker, quantity, price, action, close_date=None, close_price=None):
        """Insert a new trade into the database."""
        insert_query = """
        INSERT INTO trades (bot_name, ticker, quantity, price, action, close_date, close_price, status)
        VALUES (%s, %s, %s, %s, %s, %s, %s, 'OPEN');
        """
        with self.conn.cursor() as cur:
            cur.execute(insert_query, (bot_name, ticker, quantity, price, action, close_date, close_price))
            self.conn.commit()


    def close_trade(self, trade_position:TradePosition):
        """Update the trade record to close it."""
        if trade_position:
            update_query = """
            UPDATE trades
            SET close_date = %s, close_price = %s, status = 'CLOSED'
            WHERE id = %s AND status = 'OPEN';
            """
            with self.conn.cursor() as cur:
                cur.execute(update_query, (trade_position.close_date, trade_position.close_price, trade_position.pid))
                self.conn.commit()
                print(f"Trade {trade_position.pid} closed successfully.")

    def get_latest_open_position(self, bot_name, ticker):
        """Fetch the latest open trade position for a bot on a specific ticker."""
        query = """
        SELECT id, bot_name, ticker, quantity, price, action, open_date, close_date, close_price, status
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
                    pid=row["id"],
                    bot_name=row["bot_name"],
                    ticker=row["ticker"],
                    quantity=row["quantity"],
                    price=row["price"],
                    action=row["action"]
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