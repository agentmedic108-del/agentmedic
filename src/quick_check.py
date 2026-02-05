#!/usr/bin/env python3
"""
AgentMedic Quick Check
======================
Fast health check script for cron/monitoring.
Exits with status code indicating health.

Exit codes:
  0 = All healthy
  1 = Warning (some issues)
  2 = Critical (major issues)
  3 = Error (check failed)
"""

import sys
import asyncio

try:
    from solanascope_integration import SolanaScope
    SCOPE_AVAILABLE = True
except ImportError:
    SCOPE_AVAILABLE = False


async def quick_check():
    """Run quick health checks."""
    issues = []
    
    # Check 1: SolanaScope API
    if SCOPE_AVAILABLE:
        scope = SolanaScope()
        try:
            healthy = await scope.health_check()
            if not healthy:
                issues.append("SolanaScope API unhealthy")
        except Exception as e:
            issues.append(f"SolanaScope check failed: {e}")
        finally:
            await scope.close()
    
    # Check 2: Basic system check
    try:
        import os
        load = os.getloadavg()[0]
        if load > 4.0:
            issues.append(f"High system load: {load}")
    except:
        pass
    
    return issues


def main():
    issues = asyncio.run(quick_check())
    
    if not issues:
        print("OK: All checks passed")
        sys.exit(0)
    elif len(issues) == 1:
        print(f"WARNING: {issues[0]}")
        sys.exit(1)
    else:
        print(f"CRITICAL: {len(issues)} issues")
        for i in issues:
            print(f"  - {i}")
        sys.exit(2)


if __name__ == "__main__":
    main()
