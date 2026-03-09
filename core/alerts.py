import json
import requests
import time
from plyer import notification
from datetime import datetime, timedelta

class AlertDispatcher:
    def __init__(self, config: dict):
        self.config = config
        self.last_alerts = {} # (symbol, screener) -> timestamp
        
    def dispatch(self, symbol: str, screener: str, metrics: dict, plan: dict):
        now = datetime.now()
        cooldown_key = (symbol, screener)
        
        # Check cooldown (default 4 hours)
        cooldown_hrs = self.config.get("alerts", {}).get("cooldown_hours", 4)
        if cooldown_key in self.last_alerts:
            if now < self.last_alerts[cooldown_key] + timedelta(hours=cooldown_hrs):
                return # Skip if still in cooldown

        # 1. Desktop Notification
        if self.config.get("alerts", {}).get("desktop_notifications", False):
            try:
                msg = f"Triggered: {screener}\nPrice: {metrics.get('price', 0):.2f}"
                if plan:
                    msg += f"\nPlan: {plan.get('strategy', 'N/A')}\nEntry: {plan.get('entry', 0):.2f} SL: {plan.get('stop_loss', 0):.2f}"
                notification.notify(
                    title=f"🔥 GS Hawk: {symbol}",
                    message=msg, app_name="GS Hawk", timeout=5
                )
            except: pass
                
        # 2. Terminal beep
        if self.config.get("alerts", {}).get("sound", False):
            print("\a", end="")
            
        # 3. Telegram Alerter (Only high conviction > 5.0)
        tel_cfg = self.config.get("telegram", {})
        if tel_cfg.get("enabled", False):
            score = metrics.get('final_score', 0)
            if score >= 5.0:
                self._send_telegram(symbol, screener, metrics, plan)

        # Update cooldown
        self.last_alerts[cooldown_key] = now

    def _send_telegram(self, symbol: str, screener: str, metrics: dict, plan: dict):
        token = self.config["telegram"]["bot_token"]
        chat_id = self.config["telegram"]["chat_id"]
        
        if token == "YOUR_BOT_TOKEN": return

        # Format Professional Alert Message
        msg = f"🦅 *GS HAWK SIGNAL* — {symbol}\n\n"
        msg += f"🎯 *Screener:* `{screener}`\n"
        msg += f"💰 *CMP:* `₹{metrics.get('price', 0):,.2f}`\n"
        
        if plan:
            msg += f"\n🛠 *Strategy:* {plan.get('strategy', 'Pattern Match')}\n"
            msg += f"━━━━━━━━━━━━━━━\n"
            msg += f"✅ *ENTRY:* `{plan.get('entry', 0):.2f}`\n"
            msg += f"🛑 *SL:* `{plan.get('stop_loss', 0):.2f}`\n"
            msg += f"🚀 *TARGET:* `{plan.get('target_1', 0):.2f}`\n"
            msg += f"📈 *R:R:* `{plan.get('rr', 0):.1f}`\n"
            msg += f"━━━━━━━━━━━━━━━\n"
        
        msg += f"\n_Generated at {datetime.now().strftime('%H:%M:%S')}_"

        url = f"https://api.telegram.org/bot{token}/sendMessage"
        try:
            requests.post(url, data={
                "chat_id": chat_id,
                "text": msg,
                "parse_mode": "Markdown"
            }, timeout=10)
        except Exception as e:
            print(f"Telegram Alert Error: {e}")
