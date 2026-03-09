from rich.console import Console, Group
from rich.table import Table
from rich.panel import Panel
from rich.columns import Columns
from rich.text import Text
from rich.rule import Rule
from rich.box import DOUBLE, ROUNDED, MINIMAL, SIMPLE, SQUARE
from datetime import datetime

console = Console()

class DisplayEngine:
    # Subtle Bloomberg-Inspired Palette (Dark Grey Theme)
    BG_HEADER = "on grey19"
    TEXT_HL = "grey78"       
    TEXT_DIM = "grey42"      
    PRICE_UP = "spring_green4"
    PRICE_RED = "deep_pink4"
    CYAN = "sky_blue3"       

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
            Text(f"{pulse} LIVE NSE | {now} ", style=f"bold {DisplayEngine.TEXT_HL} {DisplayEngine.BG_HEADER}")
        )
        return Panel(header, box=SQUARE, border_style="grey19", style=DisplayEngine.BG_HEADER, padding=(0,0))

    @staticmethod
    def get_market_intelligence(macro: dict, sectors: dict):
        # Ultra-compact 1-panel Market Intel
        mood_color = DisplayEngine.PRICE_UP if macro.get('score', 0) > 5 else DisplayEngine.PRICE_RED if macro.get('score', 0) < 3 else "grey70"
        mood = f"MOOD: [bold {mood_color}]{macro.get('mood', 'N/A')}[/] ({macro.get('score', 0)}/8)"
        
        factors = []
        for name, data in list(macro.get('factors', {}).items()):
            c = DisplayEngine.PRICE_UP if data.get('change', 0) > 0 else DisplayEngine.PRICE_RED
            short = name.split()[0][:3].upper().replace("NIK", "NKY")
            factors.append(f"{short}[{c}]{data.get('change', 0):+.1f}%[/]")
        
        intel_line = Text.assemble((mood, "default"), (" | ", "dim"), (" ".join(factors), "default"))
        
        leaders = " ".join([f"{n}[{DisplayEngine.PRICE_UP}]+{d['change_1d']:.1f}%[/]" for n, d in sectors.get('leaders', [])])
        sector_line = Text.assemble(("PULSE: ", "dim"), (leaders, "default"))

        grid = Table.grid(expand=True)
        grid.add_row(intel_line)
        grid.add_row(sector_line)
        return Panel(grid, border_style=DisplayEngine.TEXT_DIM, box=SQUARE, padding=(0,1))

    @staticmethod
    def get_screener_grid(screener_hits: dict):
        if not screener_hits: return Text("SCANNING UNIVERSE...", style=DisplayEngine.TEXT_DIM)
        
        grid = Table.grid(expand=True, padding=(0, 2))
        for _ in range(3): grid.add_column(ratio=1)
        
        sorted_hits = sorted(screener_hits.items(), key=lambda x: len(x[1]), reverse=True)
        for i in range(0, len(sorted_hits), 3):
            chunk = sorted_hits[i:i+3]
            row_items = []
            for name, stocks in chunk:
                stock_summary = ", ".join([s['symbol'].replace(".NS","") for s in stocks[:3]])
                if len(stocks) > 3: stock_summary += f" +{len(stocks)-3}"
                row_items.append(Text.assemble((f"{name.upper()}: ", f"bold {DisplayEngine.TEXT_HL}"), (stock_summary, "white")))
            grid.add_row(*row_items)
            
        return Panel(grid, title=" SCREENER ALERTS ", border_style=DisplayEngine.TEXT_DIM, box=SQUARE)

    @staticmethod
    def get_strategy_table(results: list):
        if not results: return Table.grid()
        
        sectors = {}
        for r in results:
            sec = r.get('sector', 'OTHER')
            if sec not in sectors: sectors[sec] = []
            sectors[sec].append(r)

        table = Table(show_header=True, header_style=f"bold {DisplayEngine.TEXT_HL}", box=None, expand=True, padding=(0, 1))
        table.add_column("SYMBOL", style=f"bold {DisplayEngine.CYAN}", width=12)
        table.add_column("TREND", justify="center", width=12)
        table.add_column("SCORE", justify="right", width=6)
        table.add_column("CONVICTION", justify="left")
        table.add_column("TRADE SETUP", justify="left", min_width=30)
        table.add_column("R:R", justify="right", width=5)

        for sector, hits in sorted(sectors.items()):
            table.add_row(f"[bold grey62]{sector}[/]", "", "", "", "", "", style="dim")
            for r in sorted(hits, key=lambda x: x['final_score'], reverse=True):
                score = r['final_score']
                color = DisplayEngine.PRICE_UP if score >= 5 else "grey85" if score >= 2 else DisplayEngine.PRICE_RED
                spark = DisplayEngine.get_sparkline(r['metrics'].get('history_20', []), width=10)
                
                bar_val = min(int(max(0, score)), 10)
                badge = f" [bold {DisplayEngine.PRICE_UP}]STRONG[/]" if score >= 8 else f" [{DisplayEngine.PRICE_UP}]BUY[/]" if score >= 5 else ""
                conviction = f"[{color}]{'■' * bar_val}[/][{DisplayEngine.TEXT_DIM}]{'□' * (10-bar_val)}[/]{badge}"
                
                plan = r['plans'][0] if r['plans'] else {}
                setup = f"E:{plan.get('entry', 0):.0f} / SL:{plan.get('stop_loss', 0):.0f} / T:{plan.get('target_1', 0):.0f}"
                
                table.add_row(r['symbol'], spark, f"[{color}]{score:+.1f}[/]", conviction, setup, f"{plan.get('rr', 0):.1f}")
        return table

    @staticmethod
    def get_backtest_report(stats: dict):
        if not stats or stats.get('total_trades', 0) == 0:
            return Panel(Text("NO TRADES EXECUTED", style="bold red"), border_style="red")

        kpi = Table.grid(expand=True)
        kpi.add_column(); kpi.add_column(); kpi.add_column(); kpi.add_column()
        roi_c = DisplayEngine.PRICE_UP if stats['roi'] > 0 else DisplayEngine.PRICE_RED
        
        kpi.add_row(
            Panel(Text.assemble(("TRADES\n", "dim"), (f"{stats['total_trades']}", "bold")), expand=True, box=SQUARE),
            Panel(Text.assemble(("WIN%\n", "dim"), (f"{stats['win_rate']:.1f}%", "bold")), expand=True, box=SQUARE),
            Panel(Text.assemble(("P&L\n", "dim"), (f"₹{stats['pnl']:,.0f}", f"bold {roi_c}")), expand=True, box=SQUARE),
            Panel(Text.assemble(("ROI\n", "dim"), (f"{stats['roi']:+.2f}%", f"bold {roi_c}")), expand=True, box=SQUARE)
        )

        trades = Table(show_header=True, header_style="dim", box=None, expand=True)
        for col in ["DATE", "SYMBOL", "ENTRY", "EXIT", "P&L%", "RES"]: trades.add_column(col)

        for t in stats.get('trades_list', []):
            color = DisplayEngine.PRICE_UP if t['pnl'] > 0 else DisplayEngine.PRICE_RED
            trades.add_row(t['entry_date'].strftime("%y-%m-%d"), t['symbol'], f"{t['entry_price']:.1f}", f"{t['exit_price']:.1f}", f"[{color}]{t['return_pct']:+.1f}%[/]", t['result'])

        return Group(Rule(title=" BACKTEST ENGINE ", style=DisplayEngine.TEXT_DIM), kpi, trades)

    @staticmethod
    def get_footer(info: dict):
        status = f"STATUS: [bold {DisplayEngine.TEXT_HL}]{info.get('task', 'IDLE')}[/]"
        count = f" | NEXT: {info.get('next_in', '00:00')}" if info.get('live') else ""
        return Group(Rule(style=DisplayEngine.TEXT_DIM), Text(f"Q-Quit R-Reset | {status}{count} | V1.1", justify="right", style=DisplayEngine.TEXT_DIM))

    @classmethod
    def make_renderable(cls, macro_summary=None, sector_summary=None, screener_hits=None, results=None, scan_info=None, backtest_stats=None):
        comps = [cls.get_header(), cls.get_market_intelligence(macro_summary or {}, sector_summary or {})]
        if backtest_stats:
            comps.append(cls.get_backtest_report(backtest_stats))
        else:
            comps.append(cls.get_screener_grid(screener_hits or {}))
            comps.append(cls.get_strategy_table(results or []))
        comps.append(cls.get_footer(scan_info or {}))
        return Group(*comps)
