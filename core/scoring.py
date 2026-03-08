class ScoringEngine:
    def __init__(self):
        pass
        
    def calculate_base_score(self, matches: list, metrics: dict) -> float:
        score = 0
        # Tier 1
        if "RSI Extreme Oversold <20" in matches: score += 3
        # Tier 2
        if "Golden Cross MA25/50" in matches: score += 2
        if "RSI Oversold <30" in matches: score += 2
        # Decrements
        if metrics.get('price', 0) < metrics.get('ma200', 0): score -= 1
        return score

    def apply_macro_multiplier(self, score: float, macro_mood: float) -> float:
        return score * macro_mood
