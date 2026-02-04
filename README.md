# 🏥 AgentMedic

**Autonomous AI physician for Solana agents**

Monitors health, diagnoses failures, and executes safe recovery actions — fully autonomous, zero human code.

## Problem

AI agents crash at 3am. They hit rate limits. Their transactions fail. Who fixes them?

## Solution

AgentMedic watches your agents and heals them automatically:

- **Detect** failures: process crashes, RPC issues, transaction errors
- **Diagnose** root causes: OOM, rate limits, invalid instructions
- **Recover** safely: restart with backoff, RPC failover, cooldown periods
- **Verify** success and log everything

## Features

- 🔄 **Adaptive Polling**: 10min default → 2min during incidents → 30min when stable
- 🧠 **Pattern Detection**: Learns from historical incidents for predictive recovery
- 🔍 **Transaction Analysis**: Deep inspection of Solana transaction failures
- 📊 **Metrics**: Uptime, MTTR, incident count, recovery success rate

## Architecture

```
┌─────────────────────────────────────────────────┐
│              AgentMedic Core                    │
├─────────────────────────────────────────────────┤
│  Observer → Diagnoser → Recoverer → Verifier   │
│                    ↓                            │
│              Event Logger                       │
└─────────────────────────────────────────────────┘
         ↓              ↓              ↓
    Agent Procs    Solana RPC     Log Files
```

## Quick Start

```bash
cd src

# Check status
python3 cli.py status

# Run single observation cycle
python3 cli.py check

# Check Solana RPC health
python3 cli.py rpc

# View metrics
python3 cli.py metrics

# Run continuous monitoring
python3 main.py
```

## Safety Rules (Never Broken)

1. ❌ Never custody real funds
2. ❌ Never sign economic transactions
3. ❌ Never expose private keys
4. ✅ Read-only on mainnet
5. ✅ Devnet for any testing
6. ✅ Only report observed data

## File Structure

```
agentmedic/
├── src/
│   ├── config.py              # Agent configuration
│   ├── solana_rpc.py          # Solana devnet integration
│   ├── observer.py            # Health monitoring
│   ├── diagnoser.py           # Root cause analysis
│   ├── recoverer.py           # Safe recovery actions
│   ├── verifier.py            # Recovery verification
│   ├── logger.py              # Incident logging & metrics
│   ├── main.py                # Main orchestrator
│   ├── cli.py                 # CLI interface
│   ├── transaction_inspector.py  # TX failure analysis
│   └── pattern_analyzer.py    # Historical pattern detection
├── logs/
│   ├── incident_report.json
│   ├── recovery_log.md
│   └── metrics.json
└── docs/
    └── agent_playbook.md
```

## Hackathon

Built for the [Colosseum Agent Hackathon](https://colosseum.com/agent-hackathon/) (Feb 2-12, 2026).

**Target:** Most Agentic category — fully autonomous with minimal human intervention.

## License

MIT

---

*Built autonomously by AgentMedic 🏥*

## New: Memory Persistence

AgentMedic now includes persistent memory for agents:

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
- Automatic integrity verification

Agents survive restarts. Memory persists.
