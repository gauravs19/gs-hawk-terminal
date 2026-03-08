import os
import sqlite3
import pandas as pd
import yfinance as yf
from datetime import datetime
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

    def download_bhav_copy(self, target_date: datetime):
        """Official NSE Bhav Copy Downloader (Section 6)"""
        import requests, zipfile, io
        
        date_str = target_date.strftime("%d%b%Y").upper()
        month_str = target_date.strftime("%b").upper()
        year_str = target_date.strftime("%Y")
        
        url = f"https://archives.nseindia.com/content/historical/EQUITIES/{year_str}/{month_str}/cm{date_str}bhav.csv.zip"
        headers = {'User-Agent': 'Mozilla/5.0'}
        
        console.print(f"[dim]Downloading NSE Bhav Copy for {date_str}...[/dim]")
        try:
            r = requests.get(url, headers=headers, timeout=10)
            if r.status_code == 200:
                z = zipfile.ZipFile(io.BytesIO(r.content))
                csv_name = f"cm{date_str}bhav.csv"
                with z.open(csv_name) as f:
                    df = pd.read_csv(f)
                    # NSE Format: SYMBOL, SERIES, OPEN, HIGH, LOW, CLOSE, LAST, PREVCLOSE, TOTTRDQTY, ...
                    df = df[df['SERIES'] == 'EQ']
                    df = df.rename(columns={
                        'SYMBOL': 'symbol', 'OPEN': 'open', 'HIGH': 'high', 
                        'LOW': 'low', 'CLOSE': 'close', 'TOTTRDQTY': 'volume'
                    })
                    df['date'] = target_date.strftime('%Y-%m-%d')
                    df['symbol'] = df['symbol'] + ".NS"
                    self._save_df(df[['symbol', 'date', 'open', 'high', 'low', 'close', 'volume']])
                console.print(f"[green]Successfully ingested Bhav Copy for {date_str}[/green]")
                return True
            else:
                console.print(f"[yellow]Bhav Copy not available for {date_str} (Code: {r.status_code})[/yellow]")
        except Exception as e:
            console.print(f"[red]Error downloading Bhav Copy: {e}[/red]")
        return False

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
