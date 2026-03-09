import pandas as pd
import numpy as np
from core.signals import SignalEngine
from core.strategies import StrategyEngine

class BacktestEngine:
    def __init__(self, strategy_config="config/strategies.yaml"):
        self.se = SignalEngine()
        self.ste = StrategyEngine(strategy_config)

    def run(self, symbol: str, df: pd.DataFrame, initial_capital=100000):
        """
        Runs a backtest on a single symbol.
        Iterates through the dataframe from start + 100 periods to end.
        """
        if df.empty or len(df) < 150:
            return None

        trades = []
        balance = initial_capital
        position = None  # None or {entry_price, sl, target, qty, entry_date}
        
        # Step 1: Pre-calculate indicators (simplified approach: slice and call SignalEngine)
        # For better performance, a vectorized approach is preferred, but we'll use 
        # the existing logic to ensure consistency with the live scanner.
        
        for i in range(100, len(df)):
            current_date = df.index[i]
            hist_slice = df.iloc[:i+1] # All data up to current point i
            
            # 1. Manage existing position
            if position:
                curr_price = df['close'].iloc[i]
                low_p = df['low'].iloc[i]
                high_p = df['high'].iloc[i]
                
                # Check Stop Loss
                if low_p <= position['sl']:
                    exit_price = position['sl']
                    pnl = (exit_price - position['entry_price']) * position['qty']
                    trades.append({
                        'symbol': symbol,
                        'entry_date': position['entry_date'],
                        'exit_date': current_date,
                        'entry_price': position['entry_price'],
                        'exit_price': exit_price,
                        'pnl': pnl,
                        'result': 'SL',
                        'return_pct': (pnl / (position['entry_price'] * position['qty'])) * 100
                    })
                    balance += pnl
                    position = None
                    continue # Can't enter on same bar as exit
                
                # Check Target
                elif high_p >= position['target']:
                    exit_price = position['target']
                    pnl = (exit_price - position['entry_price']) * position['qty']
                    trades.append({
                        'symbol': symbol,
                        'entry_date': position['entry_date'],
                        'exit_date': current_date,
                        'entry_price': position['entry_price'],
                        'exit_price': exit_price,
                        'pnl': pnl,
                        'result': 'TP',
                        'return_pct': (pnl / (position['entry_price'] * position['qty'])) * 100
                    })
                    balance += pnl
                    position = None
                    continue

            # 2. Look for Entry (if no position)
            if not position:
                # Calculate signals at this point in time
                metrics = self.se.calculate_all(hist_slice)
                if not metrics: continue
                
                # Matches patterns from screeners? (simulated via metrics)
                matches = []
                # Re-simulating screener logic for backtest accurately
                if metrics.get('volume_ratio', 0) > 2.0: matches.append("Volume Spike")
                if metrics.get('rsi_14', 50) < 30: matches.append("RSI Oversold <30")
                if metrics.get('rsi_14', 50) < 20: matches.append("RSI Extreme Oversold <20")
                if metrics.get('stoch_rsi', 50) < 20: matches.append("Stoch RSI Bullish")
                if metrics.get('inside_bar'): matches.append("Inside Bar")
                if metrics.get('nr7'): matches.append("NR7 Range")
                
                if matches:
                    plans = self.ste.evaluate(symbol, metrics['price'], matches)
                    if plans:
                        # Enter Trade
                        plan = plans[0]
                        risk_per_trade = initial_capital * 0.02 # 2% risk
                        stop_dist = abs(plan['entry'] - plan['stop_loss'])
                        if stop_dist > 0:
                            qty = int(risk_per_trade / stop_dist)
                            if qty > 0:
                                position = {
                                    'entry_price': plan['entry'],
                                    'sl': plan['stop_loss'],
                                    'target': plan['target_1'],
                                    'qty': qty,
                                    'entry_date': current_date
                                }

        return self.calculate_stats(trades, initial_capital)

    def calculate_stats(self, trades, initial_capital):
        if not trades:
            return {
                'total_trades': 0,
                'win_rate': 0,
                'pnl': 0,
                'roi': 0
            }

        df_trades = pd.DataFrame(trades)
        wins = df_trades[df_trades['pnl'] > 0]
        losses = df_trades[df_trades['pnl'] <= 0]
        
        total_pnl = df_trades['pnl'].sum()
        
        return {
            'total_trades': len(df_trades),
            'wins': len(wins),
            'losses': len(losses),
            'win_rate': (len(wins) / len(df_trades)) * 100,
            'pnl': total_pnl,
            'roi': (total_pnl / initial_capital) * 100,
            'avg_win': wins['pnl'].mean() if not wins.empty else 0,
            'avg_loss': losses['pnl'].mean() if not losses.empty else 0,
            'max_win': df_trades['pnl'].max(),
            'max_loss': df_trades['pnl'].min(),
            'trades_list': trades
        }
