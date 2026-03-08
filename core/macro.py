import yfinance as yf
import pandas as pd
from rich.console import Console
from rich.table import Table

console = Console()

class MacroEngine:
    FACTORS = {
        "S&P 500": "^GSPC",
        "Nasdaq": "^IXIC",
        "Nikkei 225": "^N225",
        "Hang Seng": "^HSI",
        "India VIX": "^INDIAVIX",
        "USD/INR": "INR=X",
        "Brent Crude": "BZ=F",
        "Nifty 50": "^NSEI"
    }

    def __init__(self):
        self.data = {}

    def fetch_data(self):
        """Fetch latest data for all macro factors."""
        tickers = list(self.FACTORS.values())
        try:
            # Fetch last 5 days to ensure we have at least 2 trading days
            df = yf.download(tickers, period="5d", interval="1d", group_by='ticker', progress=False)
            
            for name, ticker in self.FACTORS.items():
                try:
                    ticker_data = df[ticker]
                    if len(ticker_data) >= 2:
                        prev_close = ticker_data['Close'].iloc[0]
                        curr_close = ticker_data['Close'].iloc[1]
                        change_pct = ((curr_close - prev_close) / prev_close) * 100
                        self.data[name] = {
                            "value": curr_close,
                            "change": change_pct,
                            "is_bullish": self._evaluate_bullish(name, curr_close, change_pct)
                        }
                except Exception:
                    self.data[name] = {"value": 0, "change": 0, "is_bullish": False}
        except Exception as e:
            console.print(f"[red]Error fetching macro data: {e}[/red]")

    def _evaluate_bullish(self, name, value, change):
        if name in ["S&P 500", "Nasdaq", "Nikkei 225", "Hang Seng", "Nifty 50"]:
            return change > 0
        if name == "India VIX":
            return value < 15 or change < 0
        if name == "USD/INR":
            return change < 0  # INR strengthening
        if name == "Brent Crude":
            return value < 85 or change < 0
        return False

    def get_market_mood_score(self):
        """Returns score 0-9 and multiplier."""
        bullish_count = sum(1 for f in self.data.values() if f.get("is_bullish", False))
        
        # Mapping as per spec
        if bullish_count >= 8: return bullish_count, 1.3
        if bullish_count >= 6: return bullish_count, 1.1
        if bullish_count >= 4: return bullish_count, 1.0
        if bullish_count >= 2: return bullish_count, 0.8
        return bullish_count, 0.6

    def get_macro_mood(self) -> float:
        """Helper for compatibility with older calls."""
        self.fetch_data()
        _, multiplier = self.get_market_mood_score()
        return multiplier

    def get_summary(self):
        """Returns summary for display."""
        score, multiplier = self.get_market_mood_score()
        mood_text = "STRONG BULLISH" if score >= 8 else \
                    "CAUTIOUSLY BULLISH" if score >= 6 else \
                    "MIXED / NEUTRAL" if score >= 4 else \
                    "HEADWINDS" if score >= 2 else "STRONG BEARISH"
        
        return {
            "score": score,
            "multiplier": multiplier,
            "mood": mood_text,
            "factors": self.data
        }
