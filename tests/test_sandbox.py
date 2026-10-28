"""
Tests kernel boundary, socket interception, and zero-egress enforcement.
"""
import pytest
import socket
from src.sandbox.openshell import OpenShellSupervisor, SecurityBoundaryViolation

def test_socket_egress_interceptor_blocks_external_ip():
    OpenShellSupervisor.install_egress_interceptor()

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    with pytest.raises(SecurityBoundaryViolation) as exc_info:
        s.connect(("93.184.216.34", 80))  # example.com IP

    assert "Kernel Policy Denied Outbound Egress" in str(exc_info.value)

def test_socket_egress_interceptor_allows_loopback():
    OpenShellSupervisor.install_egress_interceptor()
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        # Loopback connection should not raise SecurityBoundaryViolation
        s.connect(("127.0.0.1", 11434))
    except (ConnectionRefusedError, OSError):
        pass  # Port closed is expected; security check passed
