#!/usr/bin/env python3
"""
Health Server
=============
Simple HTTP server exposing AgentMedic status and metrics.
Useful for external monitoring and integration.

Usage:
    python3 health_server.py [port]
    
Endpoints:
    GET /health     - Basic health check
    GET /status     - Full system status
    GET /metrics    - Metrics summary
    GET /incidents  - Recent incidents
"""

import json
import http.server
import socketserver
from urllib.parse import urlparse
from datetime import datetime

from config import list_agents
from observer import get_system_status
from diagnoser import analyze
import logger
import solana_rpc


class HealthHandler(http.server.SimpleHTTPRequestHandler):
    """HTTP request handler for health endpoints."""
    
    def _send_json(self, data: dict, status: int = 200):
        """Send JSON response."""
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=2, default=str).encode())
    
    def do_GET(self):
        """Handle GET requests."""
        path = urlparse(self.path).path
        
        if path == '/health':
            self._handle_health()
        elif path == '/status':
            self._handle_status()
        elif path == '/metrics':
            self._handle_metrics()
        elif path == '/incidents':
            self._handle_incidents()
        elif path == '/rpc':
            self._handle_rpc()
        else:
            self._send_json({
                'error': 'Not found',
                'endpoints': ['/health', '/status', '/metrics', '/incidents', '/rpc']
            }, 404)
    
    def _handle_health(self):
        """Basic health check."""
        rpc = solana_rpc.devnet_health()
        self._send_json({
            'status': 'ok',
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'service': 'AgentMedic',
            'solana_rpc': 'healthy' if rpc.healthy else 'unhealthy'
        })
    
    def _handle_status(self):
        """Full system status."""
        status = get_system_status()
        incidents = analyze(status)
        
        self._send_json({
            'timestamp': status.timestamp,
            'solana_rpc': {
                'healthy': status.solana_rpc.healthy,
                'slot': status.solana_rpc.slot,
                'latency_ms': status.solana_rpc.latency_ms
            },
            'agents': {
                name: {
                    'status': r.status.value,
                    'errors': r.errors,
                    'metrics': r.metrics
                }
                for name, r in status.agents.items()
            },
            'active_incidents': len(incidents),
            'incidents': [
                {
                    'id': i.id,
                    'type': i.incident_type.value,
                    'severity': i.severity.value,
                    'agent': i.agent_name,
                    'description': i.description
                }
                for i in incidents
            ]
        })
    
    def _handle_metrics(self):
        """Metrics summary."""
        metrics = logger.get_metrics()
        self._send_json({
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            **metrics
        })
    
    def _handle_incidents(self):
        """Recent incidents from log."""
        try:
            with open('../logs/incident_report.json') as f:
                data = json.load(f)
            self._send_json({
                'count': len(data.get('incidents', [])),
                'incidents': data.get('incidents', [])[-20:]  # Last 20
            })
        except Exception as e:
            self._send_json({'error': str(e)}, 500)
    
    def _handle_rpc(self):
        """Solana RPC health details."""
        devnet = solana_rpc.devnet_health()
        mainnet = solana_rpc.mainnet_health()
        
        self._send_json({
            'devnet': {
                'healthy': devnet.healthy,
                'slot': devnet.slot,
                'latency_ms': devnet.latency_ms,
                'error': devnet.error
            },
            'mainnet': {
                'healthy': mainnet.healthy,
                'slot': mainnet.slot,
                'latency_ms': mainnet.latency_ms,
                'error': mainnet.error
            }
        })
    
    def log_message(self, format, *args):
        """Suppress default logging."""
        pass


def run_server(port: int = 8080):
    """Run the health server."""
    with socketserver.TCPServer(("", port), HealthHandler) as httpd:
        print(f"AgentMedic Health Server running on port {port}")
        print(f"Endpoints: /health /status /metrics /incidents /rpc")
        httpd.serve_forever()


if __name__ == "__main__":
    import sys
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
    run_server(port)
