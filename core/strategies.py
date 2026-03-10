import yaml

class StrategyEngine:
    def __init__(self, config_path="config/strategies.yaml"):
        with open(config_path, "r", encoding="utf-8") as f:
            self.strategies = yaml.safe_load(f) or []

    def evaluate(self, symbol: str, price: float, matches: list) -> list:
        results = []
        for s in self.strategies:
            logic = s.get("logic", "ANY")
            triggers = s.get("triggers", [])
            
            if logic == "ALL":
                # Must match ALL listed triggers
                applies = all(t in matches for t in triggers)
            else:
                # Default ANY logic
                applies = any(t in matches for t in triggers)
            
            if applies:
                # Calculate SL/Target based on ATR or defaults
                sl = price * 0.97 # Standard 3% SL for now
                t1 = price * 1.06 # Higher 6% Target for combos
                rr = (t1 - price) / (price - sl) if price > sl else 0
                
                results.append({
                    "strategy": s["name"],
                    "entry": price,
                    "target_1": t1,
                    "stop_loss": sl,
                    "rr": rr
                })
        return results
