import argparse
import time
import yaml
from rich.console import Console

from core.data import DataLayer
from core.signals import SignalEngine
from core.screeners import ScreenerEngine
from core.alerts import AlertDispatcher
from core.scoring import ScoringEngine
from core.macro import MacroEngine
from core.strategies import StrategyEngine
from core.display import DisplayEngine

console = Console()

def load_config():
    with open("config/config.yaml", "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def run_setup(config):
    console.print("[bold green]Setting up GS Hawk Terminal...[/bold green]")
    dl = DataLayer(config["cache"]["db_path"])
    
    with open("config/universe.yaml", "r", encoding="utf-8") as f:
        universe = yaml.safe_load(f)
        
    tier1 = universe.get("tier1", [])
    if tier1:
        dl.fetch_historical(tier1)
    console.print("[bold green]Setup complete.[/bold green]")

def scan_once(config, args):
    DisplayEngine.show_header()
    
    dl = DataLayer(config["cache"]["db_path"])
    se = ScreenerEngine("config/screeners.yaml")
    ste = StrategyEngine("config/strategies.yaml")
    sc = ScoringEngine()
    me = MacroEngine()
    ad = AlertDispatcher(config)
    
    macro_mood = me.get_macro_mood()
    DisplayEngine.show_macro_pulse(macro_mood)
    
    with open("config/universe.yaml", "r", encoding="utf-8") as f:
        universe = yaml.safe_load(f)
    
    stocks = []
    if args.stocks:
        stocks = [s.strip() for s in args.stocks.split(',')]
    else:
        stocks = universe.get("tier1", [])
        
    if not stocks:
        console.print("[red]No stocks to scan.[/red]")
        return
        
    console.print(f"Scanning {len(stocks)} symbols...")
    results = []
    
    for sym in stocks:
        df = dl.get_stock_data(sym)
        
        metrics = SignalEngine.calculate_all(df)
        if not metrics:
            continue
            
        matches = se.run_screeners(metrics)
        if not matches:
            continue
            
        # apply specific filter
        if args.screen and args.screen not in matches:
            continue
            
        base_score = sc.calculate_base_score(matches, metrics)
        f_score = sc.apply_macro_multiplier(base_score, macro_mood)
        
        plans = ste.evaluate(sym, metrics.get('price', 0), matches)
        
        # simple thresholding just to have something output
        final_plans = [p for p in plans if p.get('rr', 0) >= config.get('alerts', {}).get('rr_minimum', 1.0)]
        if not final_plans and matches:
            # fallback plan
            final_plans = [{"strategy": "Basic Momentum", "entry": metrics.get('price', 0), "final_score": f_score}]
        
        # update plan final score if any
        for p in final_plans:
            p['final_score'] = f_score
            
        results.append({
            "symbol": sym,
            "metrics": metrics,
            "matches": matches,
            "plans": final_plans,
            "final_score": f_score
        })
        
        # Alert check (dispatching on first run might trigger massively)
        # We will dispatch the strongest match for demo purposes
        if matches:
            ad.dispatch(sym, matches[0], metrics, final_plans[0] if final_plans else None)
            
    DisplayEngine.show_strategy_grid(results)


def main():
    parser = argparse.ArgumentParser(description="GS Hawk Terminal")
    parser.add_argument("--setup", action="store_true", help="First time setup fetch")
    parser.add_argument("--watch", action="store_true", help="Watch loop over interval")
    parser.add_argument("--interval", type=int, default=5, help="Interval in minutes for watch loop")
    parser.add_argument("--screen", type=str, help="Specific screener name to run")
    parser.add_argument("--stocks", type=str, help="Comma separated list of symbols")
    
    args = parser.parse_args()
    config = load_config()
    
    if args.setup:
        run_setup(config)
        return
        
    if args.watch:
        console.print(f"[bold red]Initializing Watch Loop ({args.interval}m interval)...[/bold red]")
        while True:
            scan_once(config, args)
            time.sleep(args.interval * 60)
            
    # Default is scan once
    scan_once(config, args)

if __name__ == "__main__":
    main()
