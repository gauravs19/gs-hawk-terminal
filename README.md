# 🦅 GS Hawk Terminal (v1.1)

> **Professional High-Frequency Pattern Scanner & Market Intelligence Station**

GS Hawk Terminal is a high-performance, Bloomberg-inspired Terminal User Interface (TUI) for Indian Equity markets (NSE/BSE). It combines advanced technical analysis with real-time global macro data and sector strength analysis to surface high-conviction trade setups.

![Terminal UI Screenshot](https://raw.githubusercontent.com/gauravs19/gs-hawk-terminal/main/docs/ui_preview.png) *(Preview placeholder)*

## 🚀 Core Pillars

### 1. Bloomberg-Inspired UX
* **High Information Density**: Full-width dashboard with real-time pulsing status indicators.
* **Ticker-Style Sparklines**: 20-day trend visualization using Unicode bar characters (` ▂▃▄▅▆▇█`).
* **Sector Grouping**: Automatic clustering of trade plans by industry (BANKING, IT, PHARMA, etc.).
* **Live Refresh Loop**: Continuous monitoring mode with a real-time countdown timer.

### 2. Multi-Dimensional Signal Engine
* **Technical Breadth**: RSI-14, Stochastic RSI, MACD Crosses, Supertrend, and MA Crosses (Golden Cross/Death Cross).
* **Price Action**: Hammer, Doji, Inside Bar, and NR7 (Narrow Range 7) detection.
* **Trend Filtering**: Automatic conviction adjustments based on moving averages (MA50/MA200).

### 3. Market Intelligence Unit
* **Macro Engine**: Live tracking of global indices (S&P 500, Nasdaq, HSI, Nikkei) and commodities (Brent Crude).
* **Sector Pulse**: Real-time relative strength heatmap identifying market leaders and laggards.
* **Convergence Scoring**: Scores are dynamically boosted by global moods and sector tailwinds.

---

## 🛠️ Installation

1. **Clone and Install**:
   ```bash
   git clone https://github.com/gauravs19/gs-hawk-terminal.git
   cd gs-hawk-terminal
   pip install .
   ```

2. **Run Anywhere**:
   Once installed, you can simply run:
   ```bash
   gs-hawk --watch
   ```

3. **Configure Settings**:
   Edit `config/config.yaml` to set your preferences.

---

## 🎮 Usage

### Standard Scan
Scan the core Tier-1 universe once:
```bash
python scanner.py
```

### Strategic Watch Mode
Run the terminal as a continuous monitoring station (refreshes every 5 mins):
```bash
python scanner.py --watch
```

### Focused Single-Screen Execution
Filter for a specific pattern (e.g., only "Golden Cross"):
```bash
python scanner.py --screen "Golden Cross MA25/50"
```

### Custom Watchlist
Scan a specific list of tickers:
```bash
python scanner.py --stocks RELIANCE.NS,TCS.NS,HDFCBANK.NS,SBIN.NS
```

---

## 📂 Architecture

* `core/signals.py`: The powerhouse for pattern and indicator logic.
* `core/macro.py`: Global factor fetching and market mood scoring.
* `core/sectors.py`: Sector-wise membership and relative strength tracking.
* `core/display.py`: The Rich-based TUI engine (Bloomberg/Ticker aesthetic).
* `config/screeners.yaml`: Highly configurable screening criteria.

---

## 🦅 Shortcuts
* `Q`: Exit Terminal
* `R`: Clear Cache & Reset
* `F1`: Help Context

---

## 📝 Disclaimer
*This tool is for educational purposes only. Always consult a financial advisor before making any investment decisions. The signals generated are based on historical data and do not guarantee future performance.*

---
**Crafted for Traders on the Edge.**
