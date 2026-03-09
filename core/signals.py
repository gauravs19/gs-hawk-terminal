import pandas as pd
import numpy as np

class SignalEngine:
    @staticmethod
    def calculate_all(df: pd.DataFrame) -> dict:
        if df.empty or len(df) < 200:
            return {}
        
        close = df['close']
        high = df['high']
        low = df['low']
        open_p = df['open']
        volume = df['volume']
        
        metrics = {}
        metrics['price'] = close.iloc[-1]
        metrics['history_20'] = close.tail(20).tolist()
        
        # --- MOVING AVERAGES ---
        metrics['ma25'] = close.rolling(25).mean().iloc[-1]
        metrics['ma50'] = close.rolling(50).mean().iloc[-1]
        metrics['ma200'] = close.rolling(200).mean().iloc[-1]
        
        prev_ma25 = close.rolling(25).mean().iloc[-2]
        prev_ma50 = close.rolling(50).mean().iloc[-2]
        
        metrics['ma25_crossed_above_ma50'] = bool((prev_ma25 <= prev_ma50) and (metrics['ma25'] > metrics['ma50']))
        metrics['ma25_crossed_below_ma50'] = bool((prev_ma25 >= prev_ma50) and (metrics['ma25'] < metrics['ma50']))
        metrics['price_above_ma200'] = bool(metrics['price'] > metrics['ma200'])
        metrics['price_crossed_above_ma50'] = bool((close.iloc[-2] <= prev_ma50) and (metrics['price'] > metrics['ma50']))

        # --- RSI & STOCH RSI ---
        delta = close.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        current_rsi = rsi.iloc[-1]
        metrics['rsi_14'] = current_rsi if not pd.isna(current_rsi) else 50
        
        rsi_min = rsi.rolling(14).min()
        rsi_max = rsi.rolling(14).max()
        stoch_rsi = (rsi - rsi_min) / (rsi_max - rsi_min)
        metrics['stoch_rsi'] = stoch_rsi.iloc[-1] * 100 if not pd.isna(stoch_rsi.iloc[-1]) else 50

        # --- MACD ---
        ema12 = close.ewm(span=12, adjust=False).mean()
        ema26 = close.ewm(span=26, adjust=False).mean()
        macd = ema12 - ema26
        signal_line = macd.ewm(span=9, adjust=False).mean()
        metrics['macd_bullish_cross'] = bool((macd.iloc[-2] <= signal_line.iloc[-2]) and (macd.iloc[-1] > signal_line.iloc[-1]))
        metrics['macd_bearish_cross'] = bool((macd.iloc[-2] >= signal_line.iloc[-2]) and (macd.iloc[-1] < signal_line.iloc[-1]))

        # --- VOLUME ---
        avg_vol = volume.rolling(20).mean().iloc[-1]
        metrics['volume_ratio'] = float(volume.iloc[-1] / avg_vol) if avg_vol and avg_vol > 0 else 0.0
        
        # --- VOLATILITY (ATR / BB) ---
        tr1 = high - low
        tr2 = (high - close.shift()).abs()
        tr3 = (low - close.shift()).abs()
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(14).mean()
        metrics['atr'] = atr.iloc[-1]
        
        std20 = close.rolling(20).std().iloc[-1]
        sma20 = close.rolling(20).mean().iloc[-1]
        bb_width = (std20 * 4) / sma20 if sma20 else 0
        metrics['bb_squeeze'] = bool(bb_width < 0.05)
        
        # --- SUPERTREND (Simplified) ---
        multiplier = 3
        hl2 = (high + low) / 2
        upper_band = hl2 + (multiplier * atr)
        lower_band = hl2 - (multiplier * atr)
        # For prototype, we just check if price is above the median upper/lower
        metrics['supertrend_bullish'] = bool(close.iloc[-1] > hl2.iloc[-1])

        # --- PRICE LEVELS ---
        high_52w = high.rolling(252).max().iloc[-1]
        low_52w = low.rolling(252).min().iloc[-1]
        metrics['near_52w_high'] = bool(metrics['price'] >= high_52w * 0.98)
        metrics['near_52w_low'] = bool(metrics['price'] <= low_52w * 1.03)
        
        # --- PATTERNS ---
        body = abs(open_p.iloc[-1] - close.iloc[-1])
        range_hl = high.iloc[-1] - low.iloc[-1]
        metrics['doji'] = bool(body <= (range_hl * 0.1) and range_hl > 0)
        
        l_shadow = min(open_p.iloc[-1], close.iloc[-1]) - low.iloc[-1]
        u_shadow = high.iloc[-1] - max(open_p.iloc[-1], close.iloc[-1])
        metrics['hammer'] = bool(l_shadow >= 2 * body and u_shadow <= body * 0.5 and body > 0)
        
        ranges = high - low
        metrics['nr7'] = bool(ranges.iloc[-1] <= ranges.iloc[-7:].min())
        metrics['inside_bar'] = bool(high.iloc[-1] < high.iloc[-2] and low.iloc[-1] > low.iloc[-2])

        return metrics
