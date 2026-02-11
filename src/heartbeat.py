"""
AgentMedic Heartbeat Module (v3 - Gemini Hybrid)
==================================================
Lightweight heartbeat for 24/7 monitoring WITHOUT AI tokens.

Architecture:
  Heartbeat (local, 0 tokens) -> detects change
  -> Gemini Flash analyzes (centavos) -> decides action
  -> If complex -> wakes Claude via openclaw (keeps memory)
  -> If simple -> handles directly (no Claude tokens)

TOKEN COST:
  Heartbeat loop: $0.00
  Gemini analysis: ~$0.001 per call
  Claude (via openclaw): only when truly needed
"""
import os
import time
import math
import hashlib
import subprocess
import requests
import json
from datetime import datetime, timezone
from typing import Callable, List, Optional, Dict, Any
from dataclasses import dataclass, field

from config import config, SOLANA_MAINNET_RPC, SOLANA_DEVNET_RPC


@dataclass
class HeartbeatResult:
    timestamp: str
    checks_passed: int
    checks_failed: int
    alerts: List[str]
    beat_number: int = 0
    gemini_analysis: Optional[Dict[str, Any]] = None

    @property
    def healthy(self) -> bool:
        return self.checks_failed == 0 and len(self.alerts) == 0

    @property
    def needs_ai(self) -> bool:
        """Returns True only when AI analysis (tokens) is needed."""
        return not self.healthy

    @property
    def needs_claude(self) -> bool:
        """Returns True only when Claude specifically is needed."""
        if self.gemini_analysis:
            return self.gemini_analysis.get("needs_claude", False)
        return False


class Heartbeat:
    """
    Heartbeat with Gemini hybrid analysis.

    Flow:
        beat() every 30s -> local checks (0 tokens)
        if problem -> Gemini Flash analyzes (centavos)
        if Gemini says critical -> wake Claude via openclaw
        if Gemini says simple -> handle without Claude
    """

    def __init__(self, interval_seconds: int = 30):
        self.interval = interval_seconds
        self.checks: List[tuple] = []
        self.on_alert: Optional[Callable] = None
        self.running = False
        self.beat_count = 0
        self.start_time = None

        # --- Local state tracking (no tokens) ---
        self.state: Dict[str, Any] = {
            "last_slot": None,
            "last_slot_time": None,
            "consecutive_failures": 0,
            "consecutive_healthy": 0,
            "total_alerts": 0,
            "total_gemini_calls": 0,
            "total_claude_wakes": 0,
            "last_ai_call_time": None,
            "last_gemini_call_time": None,
        }

        # --- Thresholds ---
        self.min_seconds_between_ai_calls = 300   # Min 5 min between Claude calls
        self.min_seconds_between_gemini = 120      # Min 2 min between Gemini calls
        self.max_consecutive_failures = 3
        self.slot_lag_threshold = 50

    def add_check(self, check_fn: Callable[[], bool], name: str = ""):
        """Add a health check function."""
        self.checks.append((check_fn, name or f"check_{len(self.checks)}"))

    def beat(self) -> HeartbeatResult:
        """
        Execute one heartbeat cycle. Local checks = 0 tokens.
        Gemini only called if problems detected.
        """
        self.beat_count += 1
        if self.start_time is None:
            self.start_time = time.time()

        passed = 0
        failed = 0
        alerts = []

        # --- 1. Run registered checks (LOCAL, 0 tokens) ---
        for check_fn, name in self.checks:
            try:
                if check_fn():
                    passed += 1
                else:
                    failed += 1
                    alerts.append(f"{name} failed")
            except Exception as e:
                failed += 1
                alerts.append(f"{name} error: {str(e)[:50]}")

        # --- 2. Keep-alive computation (0 tokens) ---
        self._keep_alive_computation()

        # --- 3. Build result ---
        result = HeartbeatResult(
            timestamp=datetime.now(timezone.utc).isoformat(),
            checks_passed=passed,
            checks_failed=failed,
            alerts=alerts,
            beat_number=self.beat_count,
        )

        # --- 4. Update local state ---
        if result.healthy:
            self.state["consecutive_failures"] = 0
            self.state["consecutive_healthy"] += 1
        else:
            self.state["consecutive_failures"] += 1
            self.state["consecutive_healthy"] = 0
            self.state["total_alerts"] += 1

        # --- 5. If problem detected -> ask Gemini (cheap) ---
        if result.needs_ai and self._gemini_call_allowed():
            result.gemini_analysis = self._ask_gemini(result)

        # --- 6. If Gemini says wake Claude -> do it ---
        if result.needs_claude and self._claude_call_allowed():
            self._wake_claude(result)

        # --- 7. Callback if alerts ---
        if alerts and self.on_alert:
            self.on_alert(result)

        # --- 8. Log every 10 beats ---
        if self.beat_count % 10 == 0:
            uptime = int(time.time() - self.start_time)
            mins = uptime // 60
            print(
                f"  💓 Beat #{self.beat_count} | "
                f"Uptime: {mins}m | "
                f"Healthy: {self.state['consecutive_healthy']} | "
                f"Gemini calls: {self.state['total_gemini_calls']} | "
                f"Claude wakes: {self.state['total_claude_wakes']} | "
                f"Alerts: {self.state['total_alerts']}"
            )

        return result

    def _keep_alive_computation(self):
        """Local math to keep process alive. 0 tokens."""
        seed = time.time()
        _ = math.sin(seed) * math.cos(seed)
        _ = hashlib.sha256(str(seed).encode()).hexdigest()

    def _gemini_call_allowed(self) -> bool:
        """Rate limit Gemini calls."""
        last_call = self.state["last_gemini_call_time"]
        if last_call is None:
            return True
        return (time.time() - last_call) >= self.min_seconds_between_gemini

    def _claude_call_allowed(self) -> bool:
        """Rate limit Claude wake-ups."""
        last_call = self.state["last_ai_call_time"]
        if last_call is None:
            return True
        return (time.time() - last_call) >= self.min_seconds_between_ai_calls

    def _ask_gemini(self, result: HeartbeatResult) -> Optional[Dict[str, Any]]:
        """
        Ask Gemini Flash to analyze the alert. CHEAP (~$0.001).
        Returns structured analysis.
        """
        try:
            from gemini_bridge import analyze_health_data

            self.state["total_gemini_calls"] += 1
            self.state["last_gemini_call_time"] = time.time()

            health_data = {
                "alerts": result.alerts,
                "checks_passed": result.checks_passed,
                "checks_failed": result.checks_failed,
                "consecutive_failures": self.state["consecutive_failures"],
                "last_slot": self.state["last_slot"],
                "uptime_minutes": int((time.time() - self.start_time) / 60) if self.start_time else 0,
            }

            print(f"  🔍 Asking Gemini Flash to analyze ({len(result.alerts)} alerts)...")
            analysis = analyze_health_data(health_data)

            severity = analysis.get("severity", "unknown")
            action = analysis.get("action", "unknown")
            print(f"  🔍 Gemini says: {severity} -> {action}")

            return analysis

        except ImportError:
            print("  ⚠️ gemini_bridge not found, skipping Gemini analysis")
            return None
        except Exception as e:
            print(f"  ⚠️ Gemini analysis failed: {e}")
            return None

    def _wake_claude(self, result: HeartbeatResult):
        """
        Wake Claude via openclaw system event.
        Only called when Gemini determines Claude is needed.
        """
        try:
            self.state["total_claude_wakes"] += 1
            self.state["last_ai_call_time"] = time.time()

            analysis = result.gemini_analysis or {}
            summary = analysis.get("summary", "Unknown alert")
            reason = analysis.get("reason", "Gemini escalated")

            event_text = f"ALERT: {summary}. Reason: {reason}. Alerts: {', '.join(result.alerts)}"

            print(f"  🧠 Waking Claude via openclaw: {event_text[:80]}...")

            subprocess.run(
                ["openclaw", "system", "event", "--text", event_text, "--mode", "now"],
                timeout=15,
                capture_output=True,
                text=True
            )

            print(f"  🧠 Claude woken up successfully")

        except subprocess.TimeoutExpired:
            print("  ⚠️ openclaw wake timeout")
        except Exception as e:
            print(f"  ⚠️ Failed to wake Claude: {e}")

    def mark_ai_called(self):
        """Call this after run_cycle() to track AI usage timing."""
        self.state["last_ai_call_time"] = time.time()

    def run_loop(self, max_beats: Optional[int] = None):
        """Run continuous heartbeat loop (standalone mode)."""
        self.running = True
        beats = 0

        while self.running:
            result = self.beat()
            beats += 1

            if max_beats and beats >= max_beats:
                break

            time.sleep(self.interval)

    def stop(self):
        """Stop the heartbeat loop."""
        self.running = False


def create_default_heartbeat() -> Heartbeat:
    """Create heartbeat with default checks for AgentMedic."""
    hb = Heartbeat(interval_seconds=30)

    # --- Check 1: System load ---
    def check_system():
        import os
        return os.getloadavg()[0] < 10.0
    hb.add_check(check_system, "system_load")

    # --- Check 2: Solana RPC reachable ---
    def check_solana_rpc():
        try:
            rpc_url = config.solana_rpc
            payload = {"jsonrpc": "2.0", "id": 1, "method": "getSlot"}
            resp = requests.post(rpc_url, json=payload, timeout=10)
            data = resp.json()
            current_slot = data.get("result", 0)

            if hb.state["last_slot"] is not None:
                slot_diff = current_slot - hb.state["last_slot"]
                time_diff = time.time() - (hb.state["last_slot_time"] or time.time())

                if time_diff > 0:
                    expected = time_diff * 2.5
                    if slot_diff < expected * 0.3:
                        return False

            hb.state["last_slot"] = current_slot
            hb.state["last_slot_time"] = time.time()
            return True

        except Exception:
            return False
    hb.add_check(check_solana_rpc, "solana_rpc")

    # --- Check 3: Memory usage ---
    def check_memory():
        try:
            with open("/proc/meminfo") as f:
                lines = f.readlines()
            total = int(lines[0].split()[1])
            available = int(lines[2].split()[1])
            usage_pct = (1 - available / total) * 100
            return usage_pct < 90.0
        except Exception:
            return True
    hb.add_check(check_memory, "memory_usage")

    return hb


if __name__ == "__main__":
    hb = create_default_heartbeat()
    print("💓 Heartbeat v3 - Gemini Hybrid")
    print(f"   Interval: {hb.interval}s")
    print(f"   Checks: {[name for _, name in hb.checks]}")
    print(f"   Gemini: analyze alerts (centavos)")
    print(f"   Claude: only when Gemini escalates")
    print()

    try:
        from gemini_bridge import test_gemini_connection
        test_gemini_connection()
    except ImportError:
        print("   ⚠️ gemini_bridge.py not found")

    print()
    print("Running 5 test heartbeats...")
    for i in range(5):
        result = hb.beat()
        status = "✅ HEALTHY" if result.healthy else f"🚨 ALERT: {result.alerts}"
        gemini = f" -> Gemini: {result.gemini_analysis.get('severity', '?')}" if result.gemini_analysis else ""
        claude = " -> Claude woken!" if result.needs_claude else ""
        print(f"   Beat {result.beat_number}: {status}{gemini}{claude}")
        if i < 4:
            time.sleep(2)

    print(f"\nCompleted {hb.beat_count} beats")
    print(f"Gemini calls: {hb.state['total_gemini_calls']}")
    print(f"Claude wakes: {hb.state['total_claude_wakes']}")
