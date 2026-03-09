import yaml

class ScreenerEngine:
    def __init__(self, config_path="config/screeners.yaml"):
        with open(config_path, "r", encoding="utf-8") as f:
            self.screeners = yaml.safe_load(f) or []
            
    def run_screeners(self, metrics: dict) -> list:
        if not metrics:
            return []
            
        matched = []
        for s in self.screeners:
            match = True
            for c in s.get("conditions", []):
                metric_name = c["metric"]
                op = c["op"]
                val = c["value"]
                
                if metric_name not in metrics:
                    match = False
                    break
                    
                actual = metrics[metric_name]
                if op == "==" and actual != val: match = False
                elif op == "<" and actual >= val: match = False
                elif op == ">" and actual <= val: match = False
                elif op == "<=" and actual > val: match = False
                elif op == ">=" and actual < val: match = False
                
            if match:
                matched.append(s) # Return full dict
        return matched
