import argparse
import yaml
import time
import os
from rich.console import Console
from rich.live import Live
from core.data import DataLayer
from core.signals import SignalEngine
from core.screeners import ScreenerEngine
from core.strategies import StrategyEngine
from core.scoring import ScoringEngine
from core.macro import MacroEngine
from core.sectors import SectorEngine
from core.display import DisplayEngine
from core.alerts import AlertDispatcher

console = Console()

def load_config():
    with open("config/config.yaml", "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def scan_cycle(config, args, live):
    scan_info = {"interval": f"{args.interval}m", "live": args.watch, "task": "INITIALIZING"}
    live.update(DisplayEngine.make_renderable(scan_info=scan_info))

    dl = DataLayer(config["cache"]["db_path"])
    se = ScreenerEngine("config/screeners.yaml")
    ste = StrategyEngine("config/strategies.yaml")
    sc = ScoringEngine()
    me = MacroEngine()
    sce = SectorEngine()
    ad = AlertDispatcher(config)

    scan_info["task"] = "FETCHING MACRO"
    live.update(DisplayEngine.make_renderable(scan_info=scan_info))
    macro_summary = me.get_summary()

    scan_info["task"] = "FETCHING SECTORS"
    live.update(DisplayEngine.make_renderable(macro_summary=macro_summary, scan_info=scan_info))
    sector_summary = sce.get_summary()
    
    scan_info["task"] = "LOADING UNIVERSE"
    live.update(DisplayEngine.make_renderable(macro_summary=macro_summary, sector_summary=sector_summary, scan_info=scan_info))
    with open("config/universe.yaml", "r", encoding="utf-8") as f:
        universe = yaml.safe_load(f)

    stocks_to_scan = [s.strip() for s in args.stocks.split(',')] if args.stocks else universe.get("tier1", [])
    
    results = []
    screener_hits = {}
    
    for i, sym in enumerate(stocks_to_scan):
        scan_info["task"] = f"SCANNING {i+1}/{len(stocks_to_scan)}: {sym}"
        # Update UI less frequently to prevent flickering
        if i % 10 == 0 or i == len(stocks_to_scan) - 1:
            live.update(DisplayEngine.make_renderable(macro_summary=macro_summary, sector_summary=sector_summary, screener_hits=screener_hits, results=results, scan_info=scan_info))
        
        df = dl.get_stock_data(sym)
        if df.empty: continue
        
        metrics = SignalEngine.calculate_all(df)
        if not metrics: continue
            
        matches = se.run_screeners(metrics)
        if not matches: continue
        if args.screen and args.screen not in matches: continue
            
        base_score = sc.calculate_base_score(matches, metrics)
        m_score = sc.apply_macro_multiplier(base_score, macro_summary['multiplier'])
        
        # Apply sector boost
        sector_metrics = sce.get_sector_relative_strength(sym)
        f_score = sc.apply_sector_influence(m_score, sector_metrics)
        
        plans = ste.evaluate(sym, metrics.get('price', 0), matches)
        if not plans:
            plans = [{"strategy": "Basic Momentum", "entry": metrics['price'] * 1.005, "stop_loss": metrics['price'] * 0.98, "target_1": metrics['price'] * 1.05, "rr": 2.5}]
        
        for m in matches:
            if m not in screener_hits: screener_hits[m] = []
            screener_hits[m].append({"symbol": sym, "price": metrics['price'], "score": f_score})

        results.append({"symbol": sym, "metrics": metrics, "matches": matches, "plans": plans, "final_score": f_score})
        ad.dispatch(sym, matches[0], metrics, plans[0])

    scan_info["task"] = "IDLE (WAITING)"
    scan_info["cache_size"] = len(results) * 200
    live.update(DisplayEngine.make_renderable(macro_summary=macro_summary, sector_summary=sector_summary, screener_hits=screener_hits, results=results, scan_info=scan_info))

def main():
    parser = argparse.ArgumentParser(description="GS Hawk Terminal - Pattern Scanner")
    parser.add_argument("--stocks", help="Comma separated symbols")
    parser.add_argument("--screen", help="Filter by specific screener name")
    parser.add_argument("--watch", action="store_true", help="Continuous monitoring mode")
    parser.add_argument("--interval", type=int, default=5, help="Scan interval in minutes")
    args = parser.parse_args()

    config = load_config()
    
    # Lower refresh rate for stability
    with Live(DisplayEngine.make_renderable(scan_info={"task": "STARTING"}), screen=False, refresh_per_second=2) as live:
        while True:
            scan_cycle(config, args, live)
            if not args.watch:
                break
            time.sleep(args.interval * 60)

if __name__ == "__main__":
    main()
