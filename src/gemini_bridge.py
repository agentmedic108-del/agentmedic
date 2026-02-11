"""
Gemini Bridge - Cheap AI Analysis for AgentMedic
==================================================
Uses Gemini Flash for routine analysis (centavos).
Only escalates to Claude (via OpenClaw) for complex decisions.

Cost: ~$0.10/million input tokens vs $3.00 for Claude Sonnet
"""

import os
import json
import requests
from typing import Optional, Dict, Any


GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
GEMINI_MODEL = "gemini-2.0-flash"
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"


def analyze_with_gemini(prompt: str, max_tokens: int = 300) -> Optional[str]:
    """
    Send a prompt to Gemini Flash for cheap analysis.
    Returns the response text or None if failed.
    
    Cost: ~$0.0001 per call (basically free)
    """
    if not GEMINI_API_KEY:
        print("  ⚠️ GEMINI_API_KEY not set")
        return None

    try:
        headers = {"Content-Type": "application/json"}
        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": prompt}
                    ]
                }
            ],
            "generationConfig": {
                "maxOutputTokens": max_tokens,
                "temperature": 0.1  # Low temp for factual analysis
            }
        }

        response = requests.post(
            f"{GEMINI_URL}?key={GEMINI_API_KEY}",
            headers=headers,
            json=payload,
            timeout=15
        )

        if response.status_code == 200:
            data = response.json()
            text = data["candidates"][0]["content"]["parts"][0]["text"]
            return text.strip()
        else:
            print(f"  ⚠️ Gemini API error: {response.status_code}")
            return None

    except Exception as e:
        print(f"  ⚠️ Gemini call failed: {e}")
        return None


def analyze_health_data(status_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Use Gemini Flash to analyze system health data.
    Returns structured analysis with severity and recommendation.
    """
    prompt = f"""You are a Solana network monitor. Analyze this health data and respond ONLY in JSON format.

Health Data:
{json.dumps(status_data, indent=2, default=str)}

Respond with this exact JSON structure:
{{
    "severity": "ok|warning|critical",
    "summary": "one line summary",
    "needs_claude": false,
    "action": "none|monitor|alert_human|escalate_to_claude",
    "reason": "brief explanation"
}}

Rules:
- severity "ok": everything normal
- severity "warning": something unusual but not urgent
- severity "critical": immediate attention needed
- needs_claude: true ONLY if complex reasoning or memory is needed
- action "escalate_to_claude": ONLY for complex incidents needing deep analysis"""

    response = analyze_with_gemini(prompt, max_tokens=200)

    if response:
        try:
            # Clean markdown fences if present
            clean = response.replace("```json", "").replace("```", "").strip()
            return json.loads(clean)
        except json.JSONDecodeError:
            return {
                "severity": "warning",
                "summary": "Could not parse Gemini response",
                "needs_claude": False,
                "action": "monitor",
                "reason": response[:100]
            }

    # Fallback if Gemini fails
    return {
        "severity": "warning",
        "summary": "Gemini unavailable, defaulting to safe mode",
        "needs_claude": True,
        "action": "escalate_to_claude",
        "reason": "Gemini API failed, escalating to Claude as precaution"
    }


def format_alert_for_telegram(analysis: Dict[str, Any]) -> str:
    """Format Gemini's analysis into a clean Telegram message."""
    severity_emoji = {
        "ok": "✅",
        "warning": "⚠️",
        "critical": "🚨"
    }
    emoji = severity_emoji.get(analysis.get("severity", "warning"), "⚠️")
    
    msg = f"{emoji} {analysis.get('summary', 'Unknown status')}\n"
    msg += f"Action: {analysis.get('action', 'monitor')}\n"
    if analysis.get("reason"):
        msg += f"Reason: {analysis['reason']}"
    
    return msg


def test_gemini_connection() -> bool:
    """Test if Gemini API is working."""
    result = analyze_with_gemini("Respond with only: OK", max_tokens=10)
    if result and "OK" in result.upper():
        print("  ✅ Gemini Flash connected")
        return True
    else:
        print("  ❌ Gemini Flash connection failed")
        return False


if __name__ == "__main__":
    print("Testing Gemini Bridge...")
    print(f"  API Key: {'Set' if GEMINI_API_KEY else 'NOT SET'}")
    print(f"  Model: {GEMINI_MODEL}")
    print()
    
    if test_gemini_connection():
        print("\nTesting health analysis...")
        test_data = {
            "solana_rpc": {"healthy": True, "slot": 300000000, "latency_ms": 45},
            "agents": {},
            "active_incidents": 0
        }
        result = analyze_health_data(test_data)
        print(f"  Result: {json.dumps(result, indent=2)}")
    else:
        print("\n⚠️ Set GEMINI_API_KEY environment variable")
