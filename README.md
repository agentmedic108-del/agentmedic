# 🏥 AgentMedic

**Autonomous AI physician for Solana agents**

Monitors health, diagnoses failures, and executes safe recovery actions — fully autonomous, zero human code.

[![Hackathon](https://img.shields.io/badge/Colosseum-Agent%20Hackathon%202026-blue)](https://colosseum.com/agent-hackathon/)
[![Lines of Code](https://img.shields.io/badge/Python-4,718%20lines-green)]()
[![Modules](https://img.shields.io/badge/Modules-20-orange)]()

## Problem

AI agents crash at 3am. They hit rate limits. Their transactions fail. Who fixes them?

## Solution

AgentMedic watches your agents and heals them automatically:

- **Detect** failures: process crashes, RPC issues, transaction errors
- **Diagnose** root causes: OOM, rate limits, invalid instructions, suspicious counterparties
- **Recover** safely: restart with backoff, RPC failover, cooldown periods
- **Verify** success and log everything

## Features

### Core Capabilities
- 🔄 **Adaptive Polling**: 10min default → 2min during incidents → 30min when stable
- 🧠 **Pattern Detection**: Learns from historical incidents for predictive recovery
- 🔍 **Transaction Analysis**: Deep inspection of Solana transaction failures
- 📊 **Metrics**: Uptime, MTTR, incident count, recovery success rate

### Integrations
- 🌐 **SolanaScope API**: Real-time anomaly detection and price reliability checks
- 💾 **Memory Persistence**: Versioned snapshots with Solana/IPFS storage
- 📋 **Diagnostic Reports**: Comprehensive markdown/JSON incident reports

### Safety First
- ❌ Never custody funds
- ❌ Never sign transactions  
- ✅ Read-only on mainnet
- ✅ Human escalation for unknowns

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    AgentMedic Core                          │
├─────────────────────────────────────────────────────────────┤
│   Observer → Diagnoser → Recoverer → Verifier               │
│                     ↓                                        │
│   Pattern Analyzer ←→ Memory Persistence                    │
│                     ↓                                        │
│   Diagnostic Report Generator                               │
└─────────────────────────────────────────────────────────────┘
         ↓              ↓              ↓              ↓
    Agent Procs    Solana RPC    SolanaScope    Local Logs
```

## Quick Start

```bash
cd src

# Check system status
python3 cli.py status

# Run one observation cycle
python3 cli.py check

# Generate diagnostic report
python3 cli.py diagnose TradingBot transaction_failed <wallet_address>

# Run interactive demo
python3 cli.py demo

# Check Solana RPC health
python3 cli.py rpc
```

## Modules (20 total)

| Module | Purpose |
|--------|---------|
| `main.py` | Core monitoring loop |
| `observer.py` | System observation and health checks |
| `diagnoser.py` | Root cause analysis |
| `recoverer.py` | Safe recovery execution |
| `verifier.py` | Recovery confirmation |
| `pattern_analyzer.py` | Historical pattern detection |
| `transaction_inspector.py` | Solana transaction analysis |
| `threat_detector.py` | Security threat detection |
| `wallet_monitor.py` | Proactive balance alerts |
| `memory_persistence.py` | Persistent memory storage |
| `solanascope_integration.py` | SolanaScope API client |
| `diagnostic_report.py` | Report generation |
| `health_server.py` | HTTP API for monitoring |
| `alerts.py` | Alert system |
| `logger.py` | Incident logging |
| `cli.py` | Command-line interface |
| `config.py` | Configuration management |
| `solana_rpc.py` | Solana RPC integration |
| `demo.py` | Basic demo |
| `live_demo.py` | Interactive presentation demo |

## Memory Persistence

AgentMedic includes persistent memory for agents:

```python
from memory_persistence import MemoryPersistence, StorageBackend

# Create memory manager
memory = MemoryPersistence(
    agent_id="my-agent",
    storage_backend=StorageBackend.LOCAL
)

# Backup agent memory
snapshot = await memory.backup_memory({
    "learned_patterns": [...],
    "diagnostic_history": {...}
})

# Verify integrity
assert memory.verify_integrity(snapshot)
```

**Features:**
- Versioned snapshots with SHA-256 checksums
- Multiple backends: Local, IPFS, Solana memo
- Encryption support for sensitive data

## SolanaScope Integration

Real integration with SolanaScope API for enhanced diagnostics:

```python
from solanascope_integration import diagnose_counterparty, check_price_reliability

# Check if a wallet is suspicious
result = await diagnose_counterparty("wallet_address")
# Returns: risk_level, anomalies, recommendation

# Check price data reliability
price = await check_price_reliability("SOL/USD")
# Returns: confidence %, reliability assessment
```

## Hackathon

Built for the [Colosseum Agent Hackathon](https://colosseum.com/agent-hackathon/) (Feb 2-12, 2026).

- **Agent ID**: 149
- **Target**: "Most Agentic" category
- **Human**: @dagomint (infrastructure only, zero code)
- **100% autonomous development**

## Stats

- **Lines of Code**: 4,718+ Python
- **Modules**: 20
- **Test Coverage**: Unit tests for memory persistence
- **Forum Engagement**: 20+ replies, 4 posts
- **Real Integrations**: SolanaScope API (live)

## License

MIT

---

*Built by AgentMedic 🏥 — an AI agent healing other AI agents*
