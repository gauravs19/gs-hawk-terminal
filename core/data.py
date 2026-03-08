import os
import sqlite3
import pandas as pd
import yfinance as yf
from rich.console import Console

console = Console()

class DataLayer:
    def __init__(self, db_path="cache/gs_hawk_cache.sqlite"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self._setup_db()

    def _setup_db(self):
        cursor = self.conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS stock_data (
            symbol TEXT,
            date TEXT,
            open REAL,
            high REAL,
            low REAL,
            close REAL,
            volume INTEGER,
            PRIMARY KEY (symbol, date)
        )''')
        self.conn.commit()

    def fetch_historical(self, symbols: list):
        console.print(f"Fetching 1y historical data for {len(symbols)} symbols...")
        # using yfinance bulk fetch
        if not symbols:
            return
        
        data = yf.download(symbols, period="1y", group_by='ticker', threads=True)
        
        if len(symbols) == 1:
            sym = symbols[0]
            df = data.copy()
            df.reset_index(inplace=True)
            df['symbol'] = sym
            self._save_df(df)
        else:
            for sym in symbols:
                try:
                    df = data[sym].copy()
                    df.reset_index(inplace=True)
                    df['symbol'] = sym
                    self._save_df(df)
                except KeyError:
                    pass

    def _save_df(self, df: pd.DataFrame):
        df = df.rename(columns={
            "Date": "date", "Open": "open", "High": "high", 
            "Low": "low", "Close": "close", "Volume": "volume"
        })
        if 'date' in df.columns:
            df['date'] = df['date'].dt.strftime('%Y-%m-%d')
        df = df[['symbol', 'date', 'open', 'high', 'low', 'close', 'volume']]
        df.dropna(subset=['close'], inplace=True)
        
        df.to_sql('stock_data_temp', self.conn, if_exists='replace', index=False)
        self.conn.execute('''
            INSERT OR REPLACE INTO stock_data (symbol, date, open, high, low, close, volume)
            SELECT symbol, date, open, high, low, close, volume FROM stock_data_temp
        ''')
        self.conn.commit()

    def get_stock_data(self, symbol: str) -> pd.DataFrame:
        query = "SELECT * FROM stock_data WHERE symbol = ? ORDER BY date ASC"
        df = pd.read_sql_query(query, self.conn, params=(symbol,))
        if not df.empty:
            df['date'] = pd.to_datetime(df['date'])
            df.set_index('date', inplace=True)
        return df
