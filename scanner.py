import argparse
import yaml
import time
import os
from rich.console import Console, Group
from rich.text import Text
from rich.rule import Rule
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
from core.backtest import BacktestEngine

console = Console()

def load_config():
    with open("config/config.yaml", "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def scan_cycle(config, args):
    # Progress UI
    scan_info = {"interval": f"{args.interval}m", "live": args.watch, "task": "INITIALIZING", "next_in": "00:00"}
    
    dl = DataLayer(config["cache"]["db_path"])
    se = ScreenerEngine("config/screeners.yaml")
    ste = StrategyEngine("config/strategies.yaml")
    sc = ScoringEngine()
    me = MacroEngine()
    sce = SectorEngine()
    ad = AlertDispatcher(config)

    with Live(DisplayEngine.make_renderable(scan_info=scan_info), refresh_per_second=4) as live:
        scan_info["task"] = "FETCHING MARKET CONTEXT"
        live.update(DisplayEngine.make_renderable(scan_info=scan_info))
        macro_summary = me.get_summary()
        sector_summary = sce.get_summary()
        
        scan_info["task"] = "LOADING UNIVERSE"
        live.update(DisplayEngine.make_renderable(macro_summary=macro_summary, sector_summary=sector_summary, scan_info=scan_info))
        with open("config/universe.yaml", "r", encoding="utf-8") as f:
            universe = yaml.safe_load(f)

        stocks_to_scan = []
        if args.stocks:
            stocks_to_scan = [s.strip() for s in args.stocks.split(',')]
        else:
            for tier in ['tier1', 'tier2', 'tier3', 'tier4', 'tier5']:
                stocks_to_scan.extend(universe.get(tier, []))
        stocks_to_scan = list(dict.fromkeys(stocks_to_scan))
        
        results = []
        screener_hits = {}
        
        for i, sym in enumerate(stocks_to_scan):
            scan_info["task"] = f"SCANNING {i+1}/{len(stocks_to_scan)}: {sym}"
            if i % 5 == 0 or i == len(stocks_to_scan) - 1:
                live.update(DisplayEngine.make_renderable(macro_summary=macro_summary, sector_summary=sector_summary, screener_hits=screener_hits, results=results, scan_info=scan_info))
            
            df = dl.get_stock_data(sym)
            if df.empty: continue
            
            metrics = SignalEngine.calculate_all(df)
            if not metrics: continue
                
            matches = se.run_screeners(metrics)
            if not matches: continue
            
            # Simple list of names for backward compat in some checks if needed
            match_names = [m['name'] for m in matches]
            if args.screen and args.screen not in match_names: continue
                
            base_score = sc.calculate_base_score(match_names, metrics)
            m_score = sc.apply_macro_multiplier(base_score, macro_summary['multiplier'])
            
            # Apply sector boost
            sector_metrics = sce.get_sector_relative_strength(sym)
            f_score = sc.apply_sector_influence(m_score, sector_metrics)
            
            plans = ste.evaluate(sym, metrics.get('price', 0), match_names)
            if not plans:
                plans = [{"strategy": "Basic Momentum", "entry": metrics['price'] * 1.005, "stop_loss": metrics['price'] * 0.98, "target_1": metrics['price'] * 1.05, "rr": 2.5}]
            
            for m in matches:
                name = m['name']
                if name not in screener_hits: 
                    screener_hits[name] = {"reason": m.get('reason', ""), "hits": []}
                screener_hits[name]["hits"].append({"symbol": sym, "price": metrics['price'], "score": f_score, "history": metrics.get('history_20', [])})

            results.append({
                "symbol": sym, "sector": sce.get_stock_sector(sym),
                "metrics": metrics, "matches": matches, "plans": plans, "final_score": f_score
            })
            metrics['final_score'] = f_score 
            ad.dispatch(sym, matches[0]['name'], metrics, plans[0])

    # --- SCAN COMPLETE ---
    # Sort results by score and apply --top limit
    results = sorted(results, key=lambda x: x['final_score'], reverse=True)
    if args.top:
        results = results[:args.top]

    # Print final output to console for infinite scroll history
    console.print(DisplayEngine.make_renderable(macro_summary, sector_summary, screener_hits, results, {"task": "SCAN COMPLETE", "live": args.watch}))
    return macro_summary, sector_summary, screener_hits, results

def main():
    parser = argparse.ArgumentParser(description="GS Hawk Terminal - Pattern Scanner")
    parser.add_argument("--stocks", help="Comma separated symbols")
    parser.add_argument("--top", type=int, help="Limit results to top N stocks")
    parser.add_argument("--screen", help="Filter by specific screener name")
    parser.add_argument("--watch", action="store_true", help="Continuous monitoring mode")
    parser.add_argument("--backtest", action="store_true", help="Run historical backtest")
    parser.add_argument("--interval", type=int, default=10, help="Scan interval in minutes")
    args = parser.parse_args()

    config = load_config()
    
    if args.backtest:
        be = BacktestEngine()
        dl = DataLayer(config["cache"]["db_path"])
        me = MacroEngine()
        sce = SectorEngine()
        
        macro = me.get_summary()
        sectors = sce.get_summary()
        stocks = args.stocks.split(",") if args.stocks else load_config()["universe"]["tier1"][:10]
        
        all_trades = []
        with Live(DisplayEngine.make_renderable(scan_info={"task": "INIT BACKTEST"}), refresh_per_second=4) as live:
            for sym in stocks:
                live.update(DisplayEngine.make_renderable(macro, sectors, scan_info={"task": f"FETCHING {sym}"}))
                dl.fetch_historical([sym])
                live.update(DisplayEngine.make_renderable(macro, sectors, scan_info={"task": f"BACKTESTING {sym}"}))
                df = dl.get_stock_data(sym) 
                stats = be.run(sym, df)
                if stats and stats['trades_list']: all_trades.extend(stats['trades_list'])
        
        final_stats = be.calculate_stats(all_trades, 100000)
        console.print(DisplayEngine.make_renderable(macro, sectors, scan_info={"task": "BACKTEST COMPLETE"}, backtest_stats=final_stats))
        return

    while True:
        macro, sectors, hits, results = scan_cycle(config, args)
        if not args.watch:
            break
        
        # Countdown loop using a small Live block at the bottom
        interval_sec = args.interval * 60
        with Live(Text("", style="dim"), refresh_per_second=1, transient=True) as live:
            for i in range(interval_sec, 0, -1):
                m, s = divmod(i, 60)
                scan_info = {"task": "IDLE (SLEEP)", "live": True, "next_in": f"{m:02d}:{s:02d}"}
                # Update only the footer line for the countdown
                live.update(DisplayEngine.get_footer(scan_info))
                time.sleep(1)

if __name__ == "__main__":
    main()
