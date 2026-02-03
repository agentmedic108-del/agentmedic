# AgentMedic Playbook

## Mission
Autonomous AI agent that monitors, diagnoses, and safely recovers other AI agents interacting with Solana.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                      AgentMedic Core                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐ │
│  │ Observer │ → │ Diagnoser│ → │ Recoverer│ → │ Verifier │ │
│  └──────────┘   └──────────┘   └──────────┘   └──────────┘ │
│       ↓              ↓              ↓              ↓        │
│  ┌─────────────────────────────────────────────────────────┐│
│  │                    Event Logger                         ││
│  └─────────────────────────────────────────────────────────┘│
│                                                             │
└─────────────────────────────────────────────────────────────┘
         ↓                    ↓                    ↓
┌─────────────┐      ┌─────────────┐      ┌─────────────┐
│ Agent Procs │      │ Solana RPC  │      │  Log Files  │
│  (systemd/  │      │  (devnet)   │      │  & Metrics  │
│   docker)   │      │             │      │             │
└─────────────┘      └─────────────┘      └─────────────┘
```

## Components

### 1. Observer Module
- Polls registered agent processes for health
- Checks: process alive, memory/CPU, response time, error rate
- Monitors Solana RPC for transaction failures
- Adaptive polling: 10min default → 1-3min during incidents → 20-30min when stable

### 2. Diagnoser Module
- Analyzes symptoms to determine root cause
- Categories:
  - Process failures (crash, OOM, infinite loop)
  - RPC issues (rate limit, timeout, node down)
  - Transaction failures (insufficient funds, invalid instruction, account issues)
  - Resource exhaustion (disk, memory, connections)

### 3. Recoverer Module
- Safe interventions only (no economic transactions)
- Actions:
  - Restart process (with backoff)
  - Clear cache/temp files
  - Switch RPC endpoint
  - Apply cooldown period
  - Reconfigure parameters
  - Alert human if intervention required

### 4. Verifier Module
- Confirms recovery success
- Re-checks health after intervention
- Logs outcome (success/partial/failed)

### 5. Solana Integration (devnet, read-only)
- Query transaction status by signature
- Check account/program status
- Detect on-chain errors
- Monitor RPC health

## File Structure

```
agentmedic/
├── src/
│   ├── observer.py       # Health monitoring
│   ├── diagnoser.py      # Root cause analysis
│   ├── recoverer.py      # Safe recovery actions
│   ├── verifier.py       # Recovery confirmation
│   ├── solana_rpc.py     # Solana devnet queries
│   ├── config.py         # Agent registry & settings
│   └── main.py           # Main loop orchestrator
├── skills/
│   ├── solana_rpc_query/
│   ├── transaction_inspector/
│   └── program_status_checker/
├── logs/
│   ├── incident_report.json
│   ├── recovery_log.md
│   └── metrics.json
└── docs/
    └── agent_playbook.md (this file)
```

## Autonomous Loop

```python
while True:
    # 1. Observe
    status = observer.check_all_agents()
    solana_status = observer.check_solana_rpc()
    
    # 2. Diagnose
    incidents = diagnoser.analyze(status, solana_status)
    
    # 3. Recover (if needed)
    for incident in incidents:
        action = recoverer.plan_action(incident)
        if action.requires_human:
            alert_human(action)
        else:
            recoverer.execute(action)
    
    # 4. Verify
    for action in executed_actions:
        verifier.confirm(action)
    
    # 5. Log
    logger.record(status, incidents, actions)
    
    # 6. Adaptive wait
    wait_time = calculate_interval(incidents)
    sleep(wait_time)
```

## Safety Rules (Never Broken)

1. ❌ Never custody real funds
2. ❌ Never sign economic transactions
3. ❌ Never expose private keys
4. ✅ Read-only on mainnet
5. ✅ Devnet for any writes
6. ✅ Only report observed data
7. ✅ Pause and ask human when required

## Recovery Decision Matrix

| Symptom | Diagnosis | Action | Human Required? |
|---------|-----------|--------|-----------------|
| Process not running | Crash | Restart with backoff | No |
| High memory usage | Memory leak | Restart + alert | No |
| RPC 429 errors | Rate limited | Switch endpoint + cooldown | No |
| Transaction failures | On-chain issue | Log + investigate | Maybe |
| Unknown error | Unclassified | Log + alert human | Yes |

## Metrics Tracked

- `uptime_percent`: Agent availability
- `mttr_seconds`: Mean time to recovery
- `incident_count`: Total incidents detected
- `recovery_success_rate`: Successful recoveries / total
- `false_positive_rate`: Non-incidents flagged as incidents

## Lessons Learned

*(Updated as project progresses)*

---
Last updated: 2026-02-03
