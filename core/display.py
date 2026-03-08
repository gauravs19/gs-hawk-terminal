from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()

class DisplayEngine:
    @staticmethod
    def show_header(metrics: dict = None):
        console.print(Panel.fit("[bold blue]GS HAWK TERMINAL v1.0[/bold blue]\nNSE Pattern Scanner", border_style="blue"))
        
    @staticmethod
    def show_macro_pulse(mood: float):
        console.print(f"[bold cyan]Macro Pulse Score: {mood}[/bold cyan]")
        
    @staticmethod
    def show_strategy_grid(scan_results: list):
        if not scan_results:
            console.print("[yellow]No signals found.[/yellow]")
            return
            
        table = Table(title="STRATEGY OUTPUT", show_header=True, header_style="bold magenta")
        table.add_column("Stock")
        table.add_column("Score")
        table.add_column("Signal")
        table.add_column("Entry")
        table.add_column("SL")
        table.add_column("Target")
        
        for sr in scan_results:
            sym = sr['symbol']
            sc = sr['final_score']
            sig = "██ SBUY" if sc >= 8 else "▓ BUY WATCH" if sc >= 5 else "░ WEAK SIGNAL" if sc > 3 else "— NEUTRAL"
            
            # Use the first strategy plan
            plan = sr['plans'][0] if sr['plans'] else {}
            entry = f"₹{plan.get('entry', 0):.1f}" if plan else "—"
            sl = f"₹{plan.get('stop_loss', 0):.1f}" if plan else "—"
            target = f"₹{plan.get('target_1', 0):.1f}" if plan else "—"
            
            table.add_row(sym, f"{sc:.1f}", sig, entry, sl, target)
            
        console.print(table)
        
    @staticmethod
    def show_alert(symbol: str, screener: str, metrics: dict, plan: dict):
        score = plan.get('final_score', 0) if plan else 0
        panel = Panel(
            f"[bold red]🔥 NEW SIGNAL — {symbol}[/bold red]\n"
            f"{screener}\n"
            f"Price ₹{metrics.get('price', 0):.2f} • RSI {metrics.get('rsi_14', 0):.1f} • Vol {metrics.get('volume_ratio', 0):.1f}x\n"
            f"Score: {score:.1f}",
            border_style="red"
        )
        console.print(panel)
