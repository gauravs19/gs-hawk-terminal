from rich.console import Console, Group
from rich.table import Table
from rich.panel import Panel
from rich.columns import Columns
from rich.text import Text
from rich.rule import Rule
from rich.box import DOUBLE, ROUNDED
from datetime import datetime

console = Console()

class DisplayEngine:
    # Bloomberg / Ticker Palette
    BG_HEADER = "on orange3"
    TEXT_HL = "orange3"
    TEXT_DIM = "grey50"
    PRICE_UP = "spring_green3"
    PRICE_RED = "red3"
    CYAN = "cyan"

    @staticmethod
    def get_sparkline(prices: list, width: int = 15) -> str:
        """Generates a text-based sparkline using Unicode bar characters."""
        if not prices or len(prices) < 2: return " " * width
        
        # Subsample to target width
        if len(prices) > width:
            indices = [int(i * (len(prices) - 1) / (width - 1)) for i in range(width)]
            prices = [prices[idx] for idx in indices]
        
        p_min = min(prices)
        p_max = max(prices)
        p_range = p_max - p_min
        if p_range == 0: p_range = 1
        
        bars = " ▂▃▄▅▆▇█"
        spark = ""
        for p in prices:
            idx = int(((p - p_min) / p_range) * (len(bars) - 1))
            spark += bars[idx]
        
        color = DisplayEngine.PRICE_UP if prices[-1] >= prices[0] else DisplayEngine.PRICE_RED
        return f"[{color}]{spark}[/]"

    @staticmethod
    def get_header():
        now = datetime.now().strftime("%d %b %Y | %H:%M:%S")
        pulse = "●" if int(datetime.now().second) % 2 == 0 else "○"
        
        header_table = Table.grid(expand=True)
        header_table.add_column(justify="left", ratio=1)
        header_table.add_column(justify="center", ratio=1)
        header_table.add_column(justify="right", ratio=1)
        
        header_table.add_row(
            Text(f" GS HAWK TERM 1.1 ", style=f"bold black {DisplayEngine.BG_HEADER}"),
            Text(f"{pulse} MONITORING NSE REAL-TIME {pulse}", style=f"bold {DisplayEngine.TEXT_HL}"),
            Text(f" {now} ", style=f"bold white {DisplayEngine.BG_HEADER}")
        )
        return header_table

    @staticmethod
    def get_market_intelligence(macro: dict, sectors: dict):
        # Professional Double Border Box for Market Intelligence
        intel = Table.grid(expand=True)
        intel.add_column(ratio=2); intel.add_column(ratio=3)

        # Macro (Left side)
        mood_color = "green" if macro.get('score', 0) > 5 else "red" if macro.get('score', 0) < 3 else "white"
        mood_str = f"MOOD: [bold {mood_color}]{macro.get('mood', 'N/A')}[/] ({macro.get('score', 0)}/8)"
        
        factors = []
        for name, data in list(macro.get('factors', {}).items())[:4]:
            c = DisplayEngine.PRICE_UP if data.get('change', 0) > 0 else DisplayEngine.PRICE_RED
            short = name.split()[0].replace("Nikkei", "NKY").replace("Hang", "HSI")
            factors.append(f"{short}[{c}]{data.get('change', 0):+.1f}%[/]")
        
        macro_line = Text.assemble((mood_str, "default"), ("  ", ""), (" | ".join(factors), "dim"))

        # Sector Performance (Right side)
        leaders = " ".join([f"{n}[{DisplayEngine.PRICE_UP}]+{d['change_1d']:.1f}%[/]" for n, d in sectors.get('leaders', [])])
        sector_line = Text.assemble(("PULSE: ", "dim"), (leaders, "default"), justify="right")

        intel.add_row(macro_line, sector_line)
        return Panel(intel, border_style=DisplayEngine.TEXT_HL, padding=(0, 1), box=DOUBLE)

    @staticmethod
    def get_screener_grid(screener_hits: dict):
        if not screener_hits:
            return Text("SCANNING STOCKS...", style="dim")

        panels = []
        # Sort by most hits
        sorted_hits = sorted(screener_hits.items(), key=lambda x: len(x[1]), reverse=True)
        
        for name, stocks in sorted_hits[:6]: # Limit to top 6 screeners to save vertical space
            if not stocks: continue
            
            stock_rows = []
            for s in stocks[:4]:
                color = DisplayEngine.PRICE_UP if s['score'] >= 5 else "white"
                spark = DisplayEngine.get_sparkline(s.get('history', []), width=6)
                stock_rows.append(f"[{color}]{s['symbol']:<10}[/] {spark}")
            
            if len(stocks) > 4:
                stock_rows.append(f"[dim] +{len(stocks)-4} hits[/]")
            
            panels.append(Panel(
                "\n".join(stock_rows), 
                title=f" {name.upper()} ", 
                title_align="left", 
                border_style=DisplayEngine.TEXT_DIM,
                padding=(0, 1)
            ))
        
        return Columns(panels, equal=True, expand=True)

    @staticmethod
    def get_strategy_table(results: list):
        if not results:
            return Table.grid()

        # Group by Sector for better visibility (TICKER style)
        sectors = {}
        for r in results:
            sec = r.get('sector', 'OTHER')
            if sec not in sectors: sectors[sec] = []
            sectors[sec].append(r)

        table = Table(
            show_header=True, 
            header_style=f"bold {DisplayEngine.TEXT_HL}", 
            box=None, 
            expand=True,
            collapse_padding=True,
            padding=(0, 1)
        )
        table.add_column("SYMBOL", style=f"bold {DisplayEngine.CYAN}", width=12)
        table.add_column("TREND (20D)", justify="center", width=12)
        table.add_column("SCORE", justify="right", width=6)
        table.add_column("CONVICTION", justify="left", min_width=25)
        table.add_column("TRADE SETUP (ENTRY/SL/T1)", justify="left", min_width=35)
        table.add_column("R:R", justify="right", width=5)

        for sector, hits in sorted(sectors.items()):
            # Sector separator row
            table.add_row(f"[bold white on blue] {sector} [/]", "", "", "", "", "", style="dim")
            
            for r in sorted(hits, key=lambda x: x['final_score'], reverse=True):
                score = r['final_score']
                color = DisplayEngine.PRICE_UP if score >= 5 else "white" if score >= 2 else DisplayEngine.PRICE_RED
                
                spark = DisplayEngine.get_sparkline(r['metrics'].get('history_20', []), width=10)
                
                # Visual Bar + Badge
                bar_val = min(int(max(0, score)), 10)
                dim_val = 10 - bar_val
                badge = " [bold green]STRONG[/]" if score >= 8 else " [green]BUY[/]" if score >= 5 else ""
                conviction = f"[{color}]{'■' * bar_val}[/][dim]{'□' * dim_val}[/]{badge}"
                
                plan = r['plans'][0] if r['plans'] else {}
                setup = f"[white]E:{plan.get('entry', 0):.0f}[/] / [dim]SL:{plan.get('stop_loss', 0):.0f} / T:{plan.get('target_1', 0):.0f}[/]"
                
                table.add_row(
                    r['symbol'], 
                    spark,
                    f"[{color}]{score:+.1f}[/]", 
                    conviction, 
                    setup, 
                    f"{plan.get('rr', 0):.1f}"
                )
        return table

    @staticmethod
    def get_footer(scan_info: dict):
        footer = Table.grid(expand=True)
        footer.add_column(ratio=1); footer.add_column(ratio=1)
        
        task = scan_info.get('task', 'IDLE')
        status = f"STATUS: [bold {DisplayEngine.TEXT_HL}]{task}[/]"
        countdown = f" | NEXT SCAN: {scan_info.get('next_in', '00:00')}" if scan_info.get('live') else ""
        
        footer.add_row(
            Text.assemble((" Q-Quit  R-Reset  F1-Help ", "dim")),
            Text(f"{status}{countdown} | ENGINE V1.1", justify="right", style="dim")
        )
        return Group(Rule(style=DisplayEngine.TEXT_HL), footer)

    @classmethod
    def make_renderable(cls, macro_summary=None, sector_summary=None, screener_hits=None, results=None, scan_info=None):
        """Final Layout assembly for the Bloomberg TUI."""
        return Group(
            cls.get_header(),
            cls.get_market_intelligence(macro_summary or {}, sector_summary or {}),
            cls.get_screener_grid(screener_hits or {}),
            Rule(style="dim", title=" TRADE STRATEGIES & SIGNALS "),
            cls.get_strategy_table(results or []),
            cls.get_footer(scan_info or {})
        )
