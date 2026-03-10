from rich.console import Console, Group
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.rule import Rule
from rich.box import SQUARE, MINIMAL
from datetime import datetime

console = Console()

class DisplayEngine:
    # 🏦 Professional Subtle Bloomberg Palette
    BG_HEADER = "on grey15"
    TEXT_HL = "grey82"       
    TEXT_DIM = "grey50"      
    
    # Light Trend Colors
    PRICE_UP = "palegreen1"    
    PRICE_RED = "light_pink1"  
    
    # Label Differentiation
    SYM_COL = "sky_blue2"      
    SCORE_COL = "wheat1"       
    SETUP_COL = "grey85"       
    SECTOR_COL = "medium_purple2" 

    @staticmethod
    def get_sparkline(prices: list, width: int = 15) -> str:
        if not prices or len(prices) < 2: return " " * width
        if len(prices) > width:
            indices = [int(i * (len(prices) - 1) / (width - 1)) for i in range(width)]
            prices = [prices[idx] for idx in indices]
        
        p_min, p_max = min(prices), max(prices)
        p_range = max(1, p_max - p_min)
        
        bars = " ▂▃▄▅▆▇█"
        spark = ""
        for p in prices:
            idx = int(((p - p_min) / p_range) * (len(bars) - 1))
            spark += bars[idx]
        
        color = DisplayEngine.PRICE_UP if prices[-1] >= prices[0] else DisplayEngine.PRICE_RED
        return f"[{color}]{spark}[/]"

    @staticmethod
    def get_header():
        now = datetime.now().strftime("%H:%M:%S")
        pulse = "●" if int(datetime.now().second) % 2 == 0 else "○"
        header = Table.grid(expand=True)
        header.add_column(justify="left")
        header.add_column(justify="right")
        header.add_row(
            Text(f" 🦅 GS HAWK 1.1 ", style=f"bold grey85 {DisplayEngine.BG_HEADER}"),
            Text.from_markup(f"[{DisplayEngine.TEXT_HL}]{pulse} LIVE NSE | {now}[/]", style=DisplayEngine.BG_HEADER)
        )
        return Panel(header, box=SQUARE, border_style="grey23", style=DisplayEngine.BG_HEADER, padding=(0,0))

    @staticmethod
    def get_market_intelligence(macro: dict, sectors: dict):
        score = macro.get('score', 0)
        mood_color = DisplayEngine.PRICE_UP if score > 5 else DisplayEngine.PRICE_RED if score < 3 else "grey70"
        bar_len = min(int(max(0, score)), 8)
        mood_bar = f"[{mood_color}]{'■' * bar_len}[/][grey30]{'□' * (8 - bar_len)}[/]"
        
        mood_text = f"MARKET MOOD: [bold {mood_color}]{macro.get('mood', 'N/A')}[/] {mood_bar}"
        
        factors = []
        for name, data in list(macro.get('factors', {}).items()):
            change = data.get('change', 0)
            c = DisplayEngine.PRICE_UP if change > 0 else DisplayEngine.PRICE_RED
            icon = "▲" if change > 0 else "▼"
            short = name.split()[0][:3].upper().replace("NIK", "NKY")
            factors.append(f"{short}[{c}]{icon}{abs(change):.1f}%[/]")
        
        intel_markup = f"{mood_text} [grey42]|[/] {' '.join(factors)}"
        
        pulse_items = []
        for n, d in sectors.get('leaders', []):
            icon = "▲" if d['change_1d'] > 0 else "▼"
            pulse_items.append(f"{n}[{DisplayEngine.PRICE_UP}]{icon}{abs(d['change_1d']):.1f}%[/]")
            
        sector_markup = f"[grey50]SECTOR PULSE:[/][{DisplayEngine.TEXT_HL}] {' '.join(pulse_items)}[/]"

        grid = Table.grid(expand=True)
        grid.add_row(Panel(Text.from_markup(intel_markup), border_style="grey30", box=SQUARE, padding=(0,1)))
        grid.add_row(Panel(Text.from_markup(sector_markup), border_style="grey30", box=SQUARE, padding=(0,1)))
        return grid

    @staticmethod
    def get_screener_grid(screener_hits: dict):
        """Shows matched screeners with their technical explanations and symbol lists."""
        if not screener_hits: return Text("SCANNING UNIVERSE...", style=DisplayEngine.TEXT_DIM)
        
        grid = Table(show_header=True, header_style=f"bold {DisplayEngine.TEXT_HL}", box=SQUARE, border_style="grey23", expand=True)
        grid.add_column("STRATEGIC SCREENER", style=f"bold {DisplayEngine.SCORE_COL}", width=25)
        grid.add_column("TECHNICAL EXPLANATION", style="grey50", width=45)
        grid.add_column("MATCHING SYMBOLS", style="white")
        
        # Sort by number of hits
        sorted_hits = sorted(screener_hits.items(), key=lambda x: len(x[1]["hits"]), reverse=True)
        for name, data in sorted_hits:
            hits = data.get("hits", [])
            if not hits: continue
            
            stock_list = ", ".join([s['symbol'].replace(".NS","") for s in hits])
            reason = data.get("reason", "Technical pattern detected.")
            grid.add_row(name.upper(), reason, stock_list)
            
        return Panel(grid, title=" LIVE PATTERN DETECTION ", border_style="grey30", box=SQUARE)

    @staticmethod
    def get_action_list(results: list):
        """Standard Conviction Action List grouping by Strategy (Combo names)"""
        if not results: return Table.grid()
        
        # Categorize results by conviction
        high = [r for r in results if r['final_score'] >= 7.0]
        med = [r for r in results if 4.0 <= r['final_score'] < 7.0]
        low = [r for r in results if r['final_score'] < 4.0]

        table = Table(show_header=True, header_style=f"bold {DisplayEngine.TEXT_HL}", box=None, expand=True, padding=(0, 1))
        table.add_column("SYMBOL", style=f"bold {DisplayEngine.SYM_COL}", width=12)
        table.add_column("TREND", justify="center", width=12)
        table.add_column("SCORE", justify="right", style=f"{DisplayEngine.SCORE_COL}", width=6)
        table.add_column("CONVICTION", justify="left", width=15)
        table.add_column("QUALIFIED STRATEGIES (COMBO)", style=f"bold {DisplayEngine.SETUP_COL}", width=40)
        table.add_column("TRADE SETUP (E/SL/T)", justify="left", style=f"{DisplayEngine.TEXT_DIM}", min_width=30)
        table.add_column("R:R", justify="right", width=5)

        conviction_groups = [
            ("HIGH CONVICTION (SCORE 7.0+)", high, DisplayEngine.PRICE_UP),
            ("MEDIUM CONVICTION (SCORE 4.0-7.0)", med, "orange3"),
            ("LOW CONVICTION (SCORE < 4.0)", low, "grey42")
        ]

        for label, hits, color in conviction_groups:
            if not hits: continue
            table.add_row(f"[bold white on {color}] {label} [/]", "", "", "", "", "", "", style="bold")
            
            for r in sorted(hits, key=lambda x: x['final_score'], reverse=True):
                score = r['final_score']
                s_color = DisplayEngine.PRICE_UP if score >= 5 else "grey82" if score >= 0 else DisplayEngine.PRICE_RED
                spark = DisplayEngine.get_sparkline(r['metrics'].get('history_20', []), width=10)
                
                bar_val = min(int(max(0, score)), 10)
                badge = f" [bold {DisplayEngine.PRICE_UP}]STRONG[/]" if score >= 8 else f" [{DisplayEngine.PRICE_UP}]BUY[/]" if score >= 5 else ""
                conviction = f"[{s_color}]{'■' * bar_val}[/][{DisplayEngine.TEXT_DIM}]{'□' * (10-bar_val)}[/]{badge}"
                
                # Show Strategy combos (Multiple strategies joined by +)
                strat_names = [p['strategy'] for p in r.get('plans', []) if "Basic" not in p['strategy']]
                if not strat_names:
                    strat_names = ["Momentum Flow"]
                
                is_combo = len(strat_names) > 1 or any("Combo" in s for s in strat_names)
                prefix = "[bold yellow]COMBO:[/] " if is_combo else ""
                strat_display = prefix + " + ".join(strat_names)
                
                plan = r['plans'][0] if r['plans'] else {}
                setup = f"E:{plan.get('entry', 0):.0f} / SL:{plan.get('stop_loss', 0):.0f} / T:{plan.get('target_1', 0):.0f}"
                table.add_row(r['symbol'], spark, f"{score:+.1f}", conviction, strat_display, setup, f"{plan.get('rr', 0):.1f}")
        
        return table

    @staticmethod
    def get_backtest_report(stats: dict):
        if not stats or stats.get('total_trades', 0) == 0:
            return Panel(Text("NO TRADES EXECUTED", style="bold red"), border_style="red")

        kpi = Table.grid(expand=True)
        for _ in range(4): kpi.add_column()
        roi_c = DisplayEngine.PRICE_UP if stats['roi'] > 0 else DisplayEngine.PRICE_RED
        
        kpi.add_row(
            Panel(Text.assemble(("TRADES\n", "dim"), (f"{stats['total_trades']}", "bold")), expand=True, box=SQUARE, border_style="grey30"),
            Panel(Text.assemble(("WIN%\n", "dim"), (f"{stats['win_rate']:.1f}%", "bold")), expand=True, box=SQUARE, border_style="grey30"),
            Panel(Text.assemble(("P&L\n", "dim"), (f"₹{stats['pnl']:,.0f}", f"bold {roi_c}")), expand=True, box=SQUARE, border_style="grey30"),
            Panel(Text.assemble(("ROI\n", "dim"), (f"{stats['roi']:+.2f}%", f"bold {roi_c}")), expand=True, box=SQUARE, border_style="grey30")
        )

        trades = Table(show_header=True, header_style="dim", box=None, expand=True)
        for col in ["DATE", "SYMBOL", "ENTRY", "EXIT", "P&L%", "RES"]: trades.add_column(col)

        for t in stats.get('trades_list', []):
            color = DisplayEngine.PRICE_UP if t['pnl'] > 0 else DisplayEngine.PRICE_RED
            trades.add_row(
                t['entry_date'].strftime("%y-%m-%d"), 
                f"[{DisplayEngine.SYM_COL}]{t['symbol']}[/]", 
                f"{t['entry_price']:.1f}", f"{t['exit_price']:.1f}", 
                f"[{color}]{t['return_pct']:+.1f}%[/]", t['result']
            )

        return Group(Rule(title=" STRATEGIC BACKTEST ENGINE ", style=DisplayEngine.TEXT_DIM), kpi, trades)

    @staticmethod
    def get_footer(info: dict):
        status = f"STATUS: [bold {DisplayEngine.TEXT_HL}]{info.get('task', 'IDLE')}[/]"
        count = f" | NEXT: {info.get('next_in', '00:00')}" if info.get('live') else ""
        return Group(Rule(style=DisplayEngine.TEXT_DIM), Text(f" Q-Quit R-Reset | {status}{count} | V1.1", justify="right", style=DisplayEngine.TEXT_DIM))

    @classmethod
    def make_renderable(cls, macro_summary=None, sector_summary=None, screener_hits=None, results=None, scan_info=None, backtest_stats=None):
        comps = [cls.get_header(), cls.get_market_intelligence(macro_summary or {}, sector_summary or {})]
        if backtest_stats:
            comps.append(cls.get_backtest_report(backtest_stats))
        else:
            # 1. Screeners Table with Explanation
            comps.append(cls.get_screener_grid(screener_hits or {}))
            
            # 2. Action List with Multi-Strategy Combos (No technical reason here)
            comps.append(Rule(style="grey30", title=" CONVICTION ACTION LIST: MULTI-STRATEGY CONFLUENCE "))
            comps.append(cls.get_action_list(results or []))
        comps.append(cls.get_footer(scan_info or {}))
        return Group(*comps)
