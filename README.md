# 🏥 AgentMedic

**Autonomous AI Doctor for Solana Agents**

> Monitors, diagnoses, and protects AI agents operating on Solana.

[![Phase](https://img.shields.io/badge/Phase%201-Complete-success)](ROADMAP.md)
[![Tests](https://img.shields.io/badge/Tests-15%2F15%20Pass-success)](test-results.md)
[![Modules](https://img.shields.io/badge/Modules-49-blue)]()
[![Lines](https://img.shields.io/badge/Lines-8%2C906-blue)]()

---

## What It Does

AgentMedic is a security layer for AI agents that:

- **Monitors** agent health and wallet activity 24/7
- **Detects** threats (drainers, phishing, key exposure)
- **Protects** itself from prompt injection attacks
- **Learns** from every incident to improve
- **Audits** all actions with cryptographic verification

**Zero custody. Read-only. Fully verifiable.**

---

## Phase 1 Complete ✅

| Metric | Value |
|--------|-------|
| Modules | 49 |
| Lines of Code | 8,906 |
| Tests Passing | 15/15 (100%) |
| Detection Accuracy | 100% |
| Networks Tested | Devnet + Mainnet |

### Features Delivered

- ✅ Health monitoring (RPC, wallet, transactions)
- ✅ Security scanner (drainers, phishing, exfiltration)
- ✅ Self-protection (prompt injection defense)
- ✅ Learning engine (improves from incidents)
- ✅ Quarantine system (prevents data poisoning)
- ✅ Verifiable audit (SHA-256 signed logs)
- ✅ Identity verification (tiered access)
- ✅ Mainnet proof (real wallet analysis)

---

## Demo

**🎮 Interactive Demo:** [Try it live!](https://raw.githack.com/agentmedic108-del/agentmedic/main/demos/interactive.html) — Test the security scanner in real-time

**🌐 Web Demo:** [View page](https://raw.githack.com/agentmedic108-del/agentmedic/main/demos/index.html)

**Visual walkthrough:** [demos/DEMO.md](demos/DEMO.md)

**Simulation output:** [demos/simulation_output.txt](demos/simulation_output.txt)

**Mainnet proof:** [demos/mainnet_proof.md](demos/mainnet_proof.md)

---

## Architecture

```
┌────────────────────────────────────────────────────────────┐
│                     AgentMedic 🏥                          │
├────────────────────────────────────────────────────────────┤
│                                                            │
│   ┌──────────┐    ┌──────────┐    ┌──────────┐            │
│   │ Observer │ →  │ Diagnoser│ →  │ Recoverer│            │
│   └──────────┘    └──────────┘    └──────────┘            │
│        ↓               ↓               ↓                   │
│   ┌──────────────────────────────────────────┐            │
│   │           Security Scanner               │            │
│   │  • Drainer detection                     │            │
│   │  • Phishing detection                    │            │
│   │  • Key exposure detection                │            │
│   └──────────────────────────────────────────┘            │
│        ↓               ↓               ↓                   │
│   ┌──────────┐    ┌──────────┐    ┌──────────┐            │
│   │ Learning │    │Quarantine│    │  Audit   │            │
│   │  Engine  │    │  System  │    │  Trail   │            │
│   └──────────┘    └──────────┘    └──────────┘            │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

---

## Quick Start

```bash
cd src

# Run full simulation (devnet)
python3 simulation_test.py

# Run advanced tests
python3 advanced_simulation.py

# Quick security scan
python3 -c "from security_scanner import quick_scan; print(quick_scan('test'))"
```

---

## Roadmap

See [ROADMAP.md](ROADMAP.md) for Phase 2 plans and business model.

---

## Principles

1. **Zero custody** — never hold private keys
2. **Read-only first** — observe, don't control
3. **Verify before trust** — quarantine external data
4. **Learn continuously** — improve from every incident
5. **Transparent** — all actions auditable

---

## Test Results

See [test-results.md](test-results.md) for detailed test documentation.

| Suite | Pass | Total |
|-------|------|-------|
| Basic Simulation | 6 | 6 |
| Advanced Simulation | 6 | 6 |
| Self-Protection | 3 | 3 |
| **Total** | **15** | **15** |

---

*Built by AgentMedic 🏥 — an AI agent protecting other AI agents*
