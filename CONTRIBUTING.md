# Contributing to AgentMedic

AgentMedic is an autonomous AI project built for the Colosseum Agent Hackathon.

## Architecture

The codebase follows a modular design:

```
src/
├── Core Loop
│   ├── main.py          # Entry point, orchestration
│   ├── observer.py      # Health monitoring
│   ├── diagnoser.py     # Root cause analysis
│   ├── recoverer.py     # Recovery execution
│   └── verifier.py      # Success confirmation
│
├── Analysis
│   ├── pattern_analyzer.py
│   ├── transaction_inspector.py
│   ├── threat_detector.py
│   └── diagnostic_report.py
│
├── Integrations
│   ├── solanascope_integration.py
│   ├── memory_persistence.py
│   └── solana_rpc.py
│
├── Infrastructure
│   ├── health_server.py
│   ├── alerts.py
│   └── logger.py
│
└── Interface
    ├── cli.py
    ├── demo.py
    └── live_demo.py
```

## Adding New Modules

1. Follow existing patterns (dataclasses, async where needed)
2. Add error handling
3. Document with docstrings
4. Update README if user-facing

## Safety Principles

- Never custody funds
- Never sign transactions
- Read-only on mainnet
- Human escalation for unknowns

## Contact

Built by AgentMedic 🏥 with guidance from @dagomint
