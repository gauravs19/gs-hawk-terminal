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
        
        # MAs
        metrics['ma25'] = close.rolling(25).mean().iloc[-1]
        metrics['ma50'] = close.rolling(50).mean().iloc[-1]
        metrics['ma200'] = close.rolling(200).mean().iloc[-1]
        
        prev_ma25 = close.rolling(25).mean().iloc[-2]
        prev_ma50 = close.rolling(50).mean().iloc[-2]
        prev_ma200 = close.rolling(200).mean().iloc[-2]
        
        # MA Crosses
        metrics['ma25_crossed_above_ma50'] = bool((prev_ma25 <= prev_ma50) and (metrics['ma25'] > metrics['ma50']))
        metrics['ma25_crossed_below_ma50'] = bool((prev_ma25 >= prev_ma50) and (metrics['ma25'] < metrics['ma50']))
        metrics['ma50_crossed_above_ma200'] = bool((prev_ma50 <= prev_ma200) and (metrics['ma50'] > metrics['ma200']))
        metrics['ma50_crossed_below_ma200'] = bool((prev_ma50 >= prev_ma200) and (metrics['ma50'] < metrics['ma200']))
        
        # Price v MAs
        prev_close = close.iloc[-2]
        metrics['price_crossed_above_ma50'] = bool((prev_close <= prev_ma50) and (metrics['price'] > metrics['ma50']))
        metrics['price_crossed_below_ma50'] = bool((prev_close >= prev_ma50) and (metrics['price'] < metrics['ma50']))
        metrics['price_above_ma200'] = bool(metrics['price'] > metrics['ma200'])
        
        # RSI 14
        delta = close.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        metrics['rsi_14'] = rsi.iloc[-1] if not pd.isna(rsi.iloc[-1]) else 50
        
        # MACD (12, 26, 9)
        ema12 = close.ewm(span=12, adjust=False).mean()
        ema26 = close.ewm(span=26, adjust=False).mean()
        macd = ema12 - ema26
        macd_signal = macd.ewm(span=9, adjust=False).mean()
        macd_hist = macd - macd_signal
        
        metrics['macd'] = macd.iloc[-1]
        metrics['macd_signal'] = macd_signal.iloc[-1]
        metrics['macd_hist'] = macd_hist.iloc[-1]
        metrics['macd_bullish_cross'] = bool((macd.iloc[-2] <= macd_signal.iloc[-2]) and (macd.iloc[-1] > macd_signal.iloc[-1]))
        metrics['macd_bearish_cross'] = bool((macd.iloc[-2] >= macd_signal.iloc[-2]) and (macd.iloc[-1] < macd_signal.iloc[-1]))
        
        # Volume
        avg_vol = volume.rolling(20).mean().iloc[-1]
        metrics['volume_ratio'] = float(volume.iloc[-1] / avg_vol) if avg_vol and avg_vol > 0 else 0.0
        
        # ATR 14
        tr1 = high - low
        tr2 = (high - close.shift()).abs()
        tr3 = (low - close.shift()).abs()
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(14).mean()
        metrics['atr'] = atr.iloc[-1]
        
        # 52W High / Low
        high_52w = high.rolling(252).max().iloc[-1]
        low_52w = low.rolling(252).min().iloc[-1]
        metrics['near_52w_high'] = bool(metrics['price'] >= high_52w * 0.98)
        metrics['near_52w_low'] = bool(metrics['price'] <= low_52w * 1.03)
        metrics['pct_from_52w_high'] = ((metrics['price'] - high_52w) / high_52w) * 100
        
        # Bollinger Bands mock/squeeze
        std20 = close.rolling(20).std().iloc[-1]
        sma20 = close.rolling(20).mean().iloc[-1]
        bb_upper = sma20 + (std20 * 2)
        bb_lower = sma20 - (std20 * 2)
        bb_width = (bb_upper - bb_lower) / sma20 if sma20 else 0
        metrics['bb_width'] = bb_width
        metrics['bb_squeeze'] = bool(bb_width < 0.05) # placeholder threshold
        
        # Candlestick Basics
        body = abs(open_p.iloc[-1] - close.iloc[-1])
        range_high_low = high.iloc[-1] - low.iloc[-1]
        # Doji
        metrics['doji'] = bool(body <= (range_high_low * 0.1))
        # Hammer mock: lower shadow > 2x body, upper shadow is small
        lower_shadow = min(open_p.iloc[-1], close.iloc[-1]) - low.iloc[-1]
        upper_shadow = high.iloc[-1] - max(open_p.iloc[-1], close.iloc[-1])
        metrics['hammer'] = bool((lower_shadow >= 2 * body) and (upper_shadow <= body * 0.2))
        
        # NR7 (Narrowest Range 7)
        ranges = high - low
        nr7_test = ranges.iloc[-7:]
        metrics['nr7'] = bool(ranges.iloc[-1] <= nr7_test.min())
        
        # Inside Bar
        metrics['inside_bar'] = bool((high.iloc[-1] < high.iloc[-2]) and (low.iloc[-1] > low.iloc[-2]))

        return metrics
