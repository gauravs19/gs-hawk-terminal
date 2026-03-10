class ScoringEngine:
    def __init__(self):
        pass
        
    def calculate_base_score(self, matches: list, metrics: dict) -> float:
        score = 0
        
        # Tier 1 (High Impact)
        if "RSI Extreme Oversold <20" in matches: score += 5
        if "Supertrend Bullish" in matches: score += 3
        if "Golden Cross MA25/50" in matches: score += 4
        
        # Tier 2 (Momentum)
        if "RSI Oversold <30" in matches: score += 2
        if "Stoch RSI Bullish" in matches: score += 2
        if "Volume Spike" in matches: score += 2
        
        # Tier 3 (Pattern)
        if "Inside Bar" in matches: score += 1
        if "NR7 Range" in matches: score += 1
        
        # --- CONFLUENCE BONUS ---
        # If multiple indicators align, boost the conviction
        if len(matches) > 2:
            confluence_bonus = (len(matches) - 2) * 2.0
            score += confluence_bonus
        
        # Trend Filter
        if metrics.get('price', 0) < metrics.get('ma200', 0): 
            score -= 2 # Penalize buying below MA200
        else:
            score += 1 # Reward trend-following
            
        return score

    def apply_macro_multiplier(self, score: float, macro_mood: float) -> float:
        return score * macro_mood

    def apply_sector_influence(self, score: float, sector_metrics: dict) -> float:
        """Boosts score if stock's sector is strong, penalizes if weak."""
        if not sector_metrics:
            return score
            
        change = sector_metrics.get('change_1d', 0)
        
        if change > 1.5:
            return score + 2.0  # Euphoric sector
        elif change > 0.5:
            return score + 1.0  # Strong sector
        elif change < -1.5:
            return score - 2.0  # Crashing sector
        elif change < -0.5:
            return score - 1.0  # Weak sector
            
        return score
