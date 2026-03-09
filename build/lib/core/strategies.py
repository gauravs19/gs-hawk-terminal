import yaml

class StrategyEngine:
    def __init__(self, config_path="config/strategies.yaml"):
        with open(config_path, "r", encoding="utf-8") as f:
            self.strategies = yaml.safe_load(f) or []

    def evaluate(self, symbol: str, price: float, matches: list) -> list:
        results = []
        for s in self.strategies:
            applies = False
            for t in s.get("triggers", []):
                if t in matches:
                    applies = True
                    break
            
            if applies:
                # Basic mock logic for SL/Targets
                sl = price * 0.95
                t1 = price * 1.05
                rr = (t1 - price) / (price - sl) if price > sl else 0
                
                results.append({
                    "strategy": s["name"],
                    "entry": price,
                    "target_1": t1,
                    "stop_loss": sl,
                    "rr": rr
                })
        return results
