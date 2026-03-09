import yfinance as yf
import pandas as pd
import yaml
from datetime import datetime, timedelta

class SectorEngine:
    def __init__(self, config_path="config/sectors.yaml"):
        with open(config_path, "r") as f:
            self.config = yaml.safe_load(f)
        self.indices = self.config.get('indices', {})
        self.mappings = self.config.get('mappings', {})
        self.sector_data = {}

    def fetch_performance(self):
        """Fetches 1-day and 5-day performance for all sector indices."""
        results = {}
        for sector, ticker in self.indices.items():
            try:
                # Fetch 7 days to ensure we have context for changes
                data = yf.download(ticker, period="7d", progress=False)
                if data.empty: continue
                
                # Get the last two close prices
                closes = data['Close']
                if len(closes) < 2: continue
                
                curr = closes.iloc[-1]
                prev = closes.iloc[-2]
                
                # Handle pandas multi-index if necessary (happens in newer yfinance versions for single ticker sometimes)
                if isinstance(curr, pd.Series): curr = curr.iloc[0]
                if isinstance(prev, pd.Series): prev = prev.iloc[0]
                
                change_1d = (float(curr) - float(prev)) / float(prev) * 100
                
                # 5-day performance
                start_5d = closes.iloc[0]
                if isinstance(start_5d, pd.Series): start_5d = start_5d.iloc[0]
                change_5d = (float(curr) - float(start_5d)) / float(start_5d) * 100
                
                results[sector] = {
                    'ticker': ticker,
                    'price': float(curr),
                    'change_1d': change_1d,
                    'change_5d': change_5d
                }
            except Exception as e:
                print(f"Error fetching {sector}: {e}")
                
        self.sector_data = results
        return results

    def get_stock_sector(self, symbol):
        """Returns the sector for a given stock symbol."""
        return self.mappings.get(symbol, "OTHER")

    def get_sector_relative_strength(self, symbol):
        """Returns the performance metrics of the sector for a specific stock."""
        sector = self.get_stock_sector(symbol)
        return self.sector_data.get(sector, None)

    def get_summary(self):
        """Returns sorted leading and lagging sectors."""
        if not self.sector_data:
            self.fetch_performance()
            
        sorted_sectors = sorted(
            self.sector_data.items(), 
            key=lambda item: item[1]['change_1d'], 
            reverse=True
        )
        
        return {
            'leaders': sorted_sectors[:3],
            'laggards': sorted_sectors[-3:],
            'all': self.sector_data
        }

if __name__ == "__main__":
    # Test logic
    se = SectorEngine()
    print("Fetching sector performance...")
    summary = se.get_summary()
    print("\nLeaders:")
    for name, data in summary['leaders']:
        print(f"{name}: {data['change_1d']:.2f}%")
    
    print("\nLaggards:")
    for name, data in summary['laggards']:
        print(f"{name}: {data['change_1d']:.2f}%")
