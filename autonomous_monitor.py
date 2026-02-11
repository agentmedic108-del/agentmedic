#!/usr/bin/env python3
import json
import time
import requests
from datetime import datetime

# Configuración corregida
SOLANA_RPC = "https://api.mainnet-beta.solana.com"
STATE_FILE = "/tmp/agentmedic_state.json"

# Token y chat ID corregidos (copia-pega los tuyos reales)
TELEGRAM_BOT_TOKEN = "8285409366:AAHdlWH6W1HyT-zTdfYmeXg8D2M-euyeak4"  # el nuevo que me diste
TELEGRAM_CHAT_ID = "5290460909"  # tu chat ID real (confirmado por sesiones/logs)

# Umbrales de alerta (puedes ajustar)
TPS_CRITICAL = 1000
TPS_WARNING = 2000
SLOT_DELAY_CRITICAL = 10  # segundos

def get_solana_health():
    """Obtiene métricas de salud de Solana sin usar LLM"""
    try:
        # Get slot
        slot_response = requests.post(SOLANA_RPC, json={
            "jsonrpc": "2.0",
            "id": 1,
            "method": "getSlot"
        }, timeout=10)
        slot = slot_response.json().get("result")

        # Get block height
        height_response = requests.post(SOLANA_RPC, json={
            "jsonrpc": "2.0",
            "id": 1,
            "method": "getBlockHeight"
        }, timeout=10)
        block_height = height_response.json().get("result")

        # Get performance samples for TPS
        perf_response = requests.post(SOLANA_RPC, json={
            "jsonrpc": "2.0",
            "id": 1,
            "method": "getRecentPerformanceSamples",
            "params": [1]
        }, timeout=10)

        perf_data = perf_response.json().get("result", [])
        tps = None
        if perf_data:
            sample = perf_data[0]
            num_tx = sample.get("numTransactions", 0)
            sample_period = sample.get("samplePeriodSecs", 60)
            tps = num_tx / sample_period if sample_period > 0 else 0

        return {
            "slot": slot,
            "block_height": block_height,
            "tps": tps,
            "timestamp": datetime.now().isoformat(),
            "healthy": True
        }
    except Exception as e:
        print(f"Error chequeando Solana: {e}")
        return {
            "error": str(e),
            "timestamp": datetime.now().isoformat(),
            "healthy": False
        }

def load_state():
    """Carga el estado anterior"""
    try:
        with open(STATE_FILE, 'r') as f:
            return json.load(f)
    except:
        return None

def save_state(state):
    """Guarda el estado actual"""
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f)

def detect_issues(current, previous):
    """Detecta problemas sin usar LLM - solo lógica"""
    issues = []

    if not current.get("healthy"):
        issues.append({
            "severity": "CRITICAL",
            "type": "RPC_DOWN",
            "message": f"Solana RPC no responde: {current.get('error')}"
        })
        return issues

    tps = current.get("tps")
    if tps is not None:
        if tps < TPS_CRITICAL:
            issues.append({
                "severity": "CRITICAL",
                "type": "TPS_CRITICAL",
                "message": f"TPS crítico: {tps:.0f} (umbral: {TPS_CRITICAL})"
            })
        elif tps < TPS_WARNING and previous:
            prev_tps = previous.get("tps")
            if prev_tps and prev_tps >= TPS_WARNING:
                issues.append({
                    "severity": "WARNING",
                    "type": "TPS_DEGRADED",
                    "message": f"TPS bajó: {prev_tps:.0f} → {tps:.0f}"
                })

    # Detectar si la red se recuperó
    if previous and not previous.get("healthy") and current.get("healthy"):
        issues.append({
            "severity": "INFO",
            "type": "RECOVERED",
            "message": "Red Solana recuperada"
        })

    return issues

def send_telegram_alert(message):
    """Envía alerta a Telegram directamente (sin Claude)"""
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        response = requests.post(url, json={
            "chat_id": TELEGRAM_CHAT_ID,
            "text": f"🚨 AgentMedic Alert\n\n{message}",
            "parse_mode": "Markdown"
        }, timeout=10)
        if response.status_code != 200:
            print(f"Error Telegram API: {response.text}")
    except Exception as e:
        print(f"Error sending Telegram: {e}")

def main():
    print(f"[{datetime.now()}] AgentMedic autonomous check...")

    current = get_solana_health()
    previous = load_state()

    issues = detect_issues(current, previous)

    if issues:
        # Genera mensaje simple (sin Claude por ahora)
        severity_emoji = {"CRITICAL": "🔴", "WARNING": "🟡", "INFO": "🟢"}
        lines = []
        for issue in issues:
            emoji = severity_emoji.get(issue["severity"], "⚪")
            lines.append(f"{emoji} *{issue['type']}*\n{issue['message']}")

        tps = current.get("tps")
        if tps:
            lines.append(f"\n📊 TPS actual: {tps:.0f}")

        message = "\n\n".join(lines)
        send_telegram_alert(message)
        print(f" → {len(issues)} issues detected, alert sent")
    else:
        print(" → All OK, no alerts needed")

    save_state(current)

if __name__ == "__main__":
    main()
