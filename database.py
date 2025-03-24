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
            print(f"{self.__class__.__name__} : Connected to the database successfully.")
        except psycopg.Error as e:
            print(f"{self.__class__.__name__} : Error connecting to database: {e}")

    def create_table(self):
        """Create a trades table if it doesn't exist."""
        create_table_query = """
        CREATE TABLE IF NOT EXISTS trades (
            id SERIAL PRIMARY KEY,
            bot_name VARCHAR(50) NOT NULL,
            ticker VARCHAR(10) NOT NULL,
            observed_entry_date TIMESTAMP NULL,
            observed_exit_date TIMESTAMP NULL,
            position_type VARCHAR(5) CHECK (position_type IN ('LONG', 'SHORT')) NOT NULL DEFAULT 'LONG',
            position_size INT NOT NULL,
            action VARCHAR(4) CHECK (action IN ('BUY', 'SELL')) NOT NULL,
            entry_submit_date TIMESTAMP NULL,
            entry_submit_price NUMERIC(10,2) NOT NULL,
            entry_date TIMESTAMP NULL,
            entry_price NUMERIC(10, 2) NULL,
            exit_submit_date TIMESTAMP NULL,
            exit_submit_price NUMERIC(10,2) NULL,
            exit_date TIMESTAMP NULL,
            exit_price NUMERIC(10, 2) NULL,
            order_type VARCHAR(6) CHECK (order_type IN ('LIMIT', 'MARKET')) NOT NULL DEFAULT 'MARKET',
            status VARCHAR(9) CHECK (status IN ('PENDING', 'OPEN', 'PARTIAL', 'CLOSED', 'CANCELED', 'FAILED')) NOT NULL
        );
        """
        with self.conn.cursor() as cur:
            cur.execute(create_table_query)
            self.conn.commit()

    def update_position(self, trade_position: TradeKitPosition):
        """ Generates the UPDATE SQL statement dynamically for an existing position. """
        if trade_position.id is None:
            raise ValueError("Position ID is required for updating the database.")

        fields_to_update = {}
        
        # convert the passed object's attributes into a dictionary
        position_data = vars(trade_position)

        # create an UPDATE statement with only the fields that have values, i.e. not None
        for field, value in position_data.items():
            if value is not None and field != "id":
                fields_to_update[field] = value

        if not fields_to_update:
            raise ValueError("No fields to update.")
        
        set_clause = ", ".join([f"{key} = %s" for key in fields_to_update.keys()])
        values = list(fields_to_update.values())

        sql_query = f"""
        UPDATE trades
        SET {set_clause}
        WHERE id = %s
        """

        values.append(trade_position.id)
        try:
            cursor = self.conn.cursor()
            cursor.execute(sql_query, values)
            self.conn.commit()
            print(f"{self.__class__.__name__} : Trade position {trade_position.id} updated successfully.")
        except Exception as e:
            print(f"{self.__class__.__name__} : Error updating trade position {trade_position.id}: {e}")

    def create_position(self, trade_position: TradeKitPosition):        
        """Insert a new open trade position into the database."""
        
        insert_query = """
        INSERT INTO trades (bot_name, ticker, position_type, position_size, entry_submit_price, action, entry_submit_date, status)
        VALUES (%(bot_name)s, %(ticker)s, %(position_type)s, %(position_size)s, %(entry_submit_price)s, %(action)s, %(entry_submit_date)s, %(status)s)
        RETURNING id;
        """

        params = {
            "bot_name": trade_position.bot_name,
            "ticker": trade_position.ticker,
            "position_type": trade_position.position_type,
            "position_size": trade_position.position_size,
            "entry_submit_price": trade_position.entry_submit_price,
            "action": trade_position.action,
            "entry_submit_date": trade_position.entry_submit_date if trade_position.entry_submit_date else None,  # NULL handling
            "status": trade_position.status if trade_position.status else "PENDING",  # default status is PENDING
        }

        try:
            with self.conn.cursor() as cur:
                cur.execute(insert_query, params)
                trade_id = cur.fetchone()["id"]
                self.conn.commit()
                return trade_id
        
        except Exception as e:
            self.conn.rollback()  # Ensure rollback on failure
            print(f"{self.__class__.__name__} : Error creating trade position: {e}")
            return None

    def get_latest_open_position(self, bot_name, ticker):
        """Fetch the latest open trade position for a bot on a specific ticker."""
        query = """
        SELECT id, bot_name, ticker, observed_entry_date, observed_exit_date, position_type, position_size, action, 
            entry_submit_date, entry_submit_price, entry_date, entry_price, 
            exit_submit_date, exit_submit_price, exit_date, exit_price, 
            order_type, status
        FROM trades
        WHERE bot_name = %s AND ticker = %s AND status = 'OPEN'
        ORDER BY entry_date DESC
        LIMIT 1;
        """
        with self.conn.cursor() as cur:
            cur.execute(query, (bot_name, ticker))
            row = cur.fetchone()
            
            if row:
                return TradeKitPosition(
                    id=row["id"],
                    bot_name=row["bot_name"],
                    ticker=row["ticker"],
                    observed_entry_date=row["observed_entry_date"],
                    observed_exit_date=row["observed_exit_date"],
                    position_type=row["position_type"],
                    position_size=row["position_size"],
                    action=row["action"],
                    entry_submit_date=row["entry_submit_date"],
                    entry_submit_price=row["entry_submit_price"],
                    entry_date=row["entry_date"],
                    entry_price=row["entry_price"],
                    exit_submit_date=row["exit_submit_date"],
                    exit_submit_price=row["exit_submit_price"],
                    exit_date=row["exit_date"],
                    exit_price=row["exit_price"],
                    order_type=row["order_type"],
                    status=row["status"]
                )
            else:
                return None


    def get_last_position(self, bot_name, ticker):
        """Fetch the latest trade position for a bot on a specific ticker, excluding CLOSED status."""
        query = """
        SELECT id, bot_name, ticker, observed_entry_date, observed_exit_date, position_type, position_size, action, 
            entry_submit_date, entry_submit_price, entry_date, entry_price, 
            exit_submit_date, exit_submit_price, exit_date, exit_price, 
            order_type, status
        FROM trades
        WHERE bot_name = %s AND ticker = %s AND status != 'CLOSED'
        ORDER BY entry_date DESC
        LIMIT 1;
        """
        with self.conn.cursor() as cur:
            cur.execute(query, (bot_name, ticker))
            row = cur.fetchone()
            
            if row:
                return TradeKitPosition(
                    id=row["id"],
                    bot_name=row["bot_name"],
                    ticker=row["ticker"],
                    observed_entry_date=row["observed_entry_date"],
                    observed_exit_date=row["observed_exit_date"],
                    position_type=row["position_type"],
                    position_size=row["position_size"],
                    action=row["action"],
                    entry_submit_date=row["entry_submit_date"],
                    entry_submit_price=row["entry_submit_price"],
                    entry_date=row["entry_date"],
                    entry_price=row["entry_price"],
                    exit_submit_date=row["exit_submit_date"],
                    exit_submit_price=row["exit_submit_price"],
                    exit_date=row["exit_date"],
                    exit_price=row["exit_price"],
                    order_type=row["order_type"],
                    status=row["status"]
                )
            else:
                return None

    def get_last_observed_exit_date(self):
        """Fetch the observed_exit_date of the most recent CLOSED trade."""
        query = """
        SELECT observed_exit_date 
        FROM trades 
        WHERE status = 'CLOSED' 
        ORDER BY observed_exit_date DESC 
        LIMIT 1;
        """
        try:
            with self.conn.cursor() as cursor:
                cursor.execute(query)
                result = cursor.fetchone()
                return result['observed_exit_date'] if result else None
        except Exception as e:
            print(f"Error fetching last closed trade exit date: {e}")
            return None


    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
            print(f"{self.__class__.__name__} : Database connection closed.")