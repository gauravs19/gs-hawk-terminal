from rich.console import Console, Group
from rich.table import Table
from rich.panel import Panel
from rich.columns import Columns
from rich.text import Text
from rich.rule import Rule
from datetime import datetime

console = Console()

class DisplayEngine:
    # Bloomberg Palette
    BG_HEADER = "on orange3"
    TEXT_HL = "orange3"
    TEXT_DIM = "grey50"
    PRICE_UP = "spring_green3"
    PRICE_RED = "red3"

    @staticmethod
    def get_header():
        now = datetime.now().strftime("%d %b %Y | %H:%M:%S")
        header_table = Table.grid(expand=True)
        header_table.add_column(justify="left", ratio=1)
        header_table.add_column(justify="center", ratio=1)
        header_table.add_column(justify="right", ratio=1)
        
        header_table.add_row(
            Text(f" GS HAWK TERM 1.0 ", style=f"bold black {DisplayEngine.BG_HEADER}"),
            Text("EQUITY MONITOR <NSE/BSE>", style=f"bold {DisplayEngine.TEXT_HL}"),
            Text(f" {now} ", style=f"bold white {DisplayEngine.BG_HEADER}")
        )
        return header_table

    @staticmethod
    def get_macro_dashboard(macro_summary: dict):
        if not macro_summary:
            return Panel(Text("FETCHING MACRO...", style="dim"), border_style=DisplayEngine.TEXT_HL)

        factors = []
        for name, data in macro_summary.get('factors', {}).items():
            color = DisplayEngine.PRICE_UP if data.get('change', 0) > 0 else DisplayEngine.PRICE_RED
            short_name = name.replace("Hang Seng", "HSI").replace("Nikkei 225", "NKY").replace("Nasdaq", "NQ").replace("S&P 500", "SPX")
            factors.append(f"{short_name} [{color}]{data.get('change', 0):+.1f}%[/{color}]")

        dashboard = Table.grid(expand=True)
        dashboard.add_row(
            Text.assemble(
                (" MOOD: ", "dim"), (f" {macro_summary.get('mood', 'N/A')} ", "bold white"),
                (" (", "dim"), (f"{macro_summary.get('score', 0)}", "bold"), ("/8) ", "dim")
            ),
            Text("  ".join(factors), style="dim")
        )
        return Panel(dashboard, border_style=DisplayEngine.TEXT_HL, padding=(0, 1))

    @staticmethod
    def get_screener_grid(screener_hits: dict):
        if not screener_hits:
            return Text("SCANNING STOCKS...", style="dim")

        panels = []
        # Compact grid: Top 3 only to save vertical space
        for name, stocks in screener_hits.items():
            if not stocks: continue
            stock_lines = [f"[{DisplayEngine.PRICE_UP if s['score'] >= 5 else 'white'}]{s['symbol']:<10}[/] {s['price']:>6.0f}" for s in stocks[:3]]
            if len(stocks) > 3:
                stock_lines.append(f"[dim]+{len(stocks)-3} more[/]")
            
            panel = Panel(
                "\n".join(stock_lines), 
                title=f" {name.upper()} ", 
                title_align="left", 
                border_style=DisplayEngine.TEXT_DIM,
                padding=(0, 1)
            )
            panels.append(panel)
        
        return Columns(panels, equal=True, expand=True)

    @staticmethod
    def get_strategy_table(results: list):
        if not results:
            return Table.grid()

        # High-density Bloomberg table
        table = Table(
            show_header=True, 
            header_style=f"bold {DisplayEngine.TEXT_HL}", 
            box=None, 
            expand=True,
            collapse_padding=True,
            padding=(0, 1)
        )
        table.add_column("TICKER", ratio=1, style="bold white")
        table.add_column("LAST", justify="right", ratio=1)
        table.add_column("SCORE", justify="right", ratio=0.8)
        table.add_column("CONVICTION", justify="left", ratio=2, overflow="fold")
        table.add_column("TRADE SETUP", justify="left", ratio=3, overflow="fold")
        table.add_column("R:R", justify="right", ratio=0.5)

        for r in results:
            score = r['final_score']
            color = DisplayEngine.PRICE_UP if score >= 5 else "white" if score >= 2 else DisplayEngine.PRICE_RED
            
            bar_len = min(int(max(0, score)), 10)
            bar = "█" * bar_len
            conviction = f"[{color}]{bar:<10} {r['matches'][0] if r['matches'] else 'NEUTRAL'}[/]"
            
            plan = r['plans'][0] if r['plans'] else {}
            setup = f"[white]E:{plan.get('entry', 0):.0f}[/] / SL:{plan.get('stop_loss', 0):.0f} / T1:{plan.get('target_1', 0):.0f}"
            
            table.add_row(
                r['symbol'], 
                f"{r['metrics']['price']:,.2f}", 
                f"[{color}]{score:+.1f}[/]", 
                conviction, 
                setup, 
                f"{plan.get('rr', 0):.1f}"
            )
        return table

    @staticmethod
    def get_footer(scan_info: dict):
        footer = Table.grid(expand=True)
        footer.add_column(ratio=1); footer.add_column(ratio=1); footer.add_column(ratio=1)
        task = scan_info.get('task', 'IDLE')
        status = f"STATUS: [{DisplayEngine.TEXT_HL}]{task}[/] | INTERVAL: {scan_info.get('interval', '5m')}"
        footer.add_row(
            f"[dim]F1 HELP | F2 WATCH | F3 SCREEN | [/][bold white]Q EXIT[/]", 
            Text(" ENGINE V1.0 - NSE LIVE ", justify="center", style="dim"), 
            Text(status, justify="right")
        )
        return Group(Rule(style=DisplayEngine.TEXT_HL), footer, Text(" " + "═" * (console.width - 2), style=DisplayEngine.TEXT_HL))

    @classmethod
    def make_renderable(cls, macro_summary=None, screener_hits=None, results=None, scan_info=None):
        """Assembles components. Designed for vertical scrollability in non-screen mode."""
        return Group(
            cls.get_header(),
            cls.get_macro_dashboard(macro_summary),
            cls.get_screener_grid(screener_hits or {}),
            cls.get_strategy_table(results or []),
            cls.get_footer(scan_info or {})
        )
