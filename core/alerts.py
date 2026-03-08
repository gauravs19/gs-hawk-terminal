import json
from plyer import notification

class AlertDispatcher:
    def __init__(self, config: dict):
        self.config = config
        
    def dispatch(self, symbol: str, screener: str, metrics: dict, plan: dict):
        # Desktop
        if self.config.get("alerts", {}).get("desktop_notifications", False):
            try:
                msg = f"Triggered: {screener}\nPrice: {metrics.get('price', 0):.2f}"
                if plan:
                    msg += f"\nPlan: {plan.get('strategy', 'N/A')}\nEntry: {plan.get('entry', 0):.2f} SL: {plan.get('stop_loss', 0):.2f}"
                
                notification.notify(
                    title=f"🔥 New Signal — {symbol}",
                    message=msg,
                    app_name="GS Hawk Terminal",
                    timeout=5
                )
            except Exception as e:
                pass
                
        # Terminal beep
        if self.config.get("alerts", {}).get("sound", False):
            print("\a", end="") # standard bell
            
        # Telegram... (mocked)
        if self.config.get("telegram", {}).get("enabled", False):
            # mock sending via requests
            pass
