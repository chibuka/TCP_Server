import time
from conftest import http_server_process, is_port_in_use
from conftest import send_http_request
import pytest
import socket
import subprocess
from contextlib import contextmanager
import os

def test_server_starts_without_error():
    """Test that the server process starts without immediate errors."""
    with http_server_process() as process:
        # Give the server a moment to potentially crash
        time.sleep(0.5)
        
        # Check if process is still running
        poll_result = process.poll()
        if poll_result is not None:
            # Process has terminated, capture output
            stdout, stderr = process.communicate()
            error_msg = f"Server process terminated with exit code {poll_result}"
            if stderr:
                error_msg += f"\nStderr: {stderr.decode()}"
            if stdout:
                error_msg += f"\nStdout: {stdout.decode()}"
            pytest.fail(error_msg)


def test_server_accepts_single_connection():
    """Test that the server can accept a single TCP connection."""
    with http_server_process():
        try:
            # Create a socket and connect to the server
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
                client_socket.settimeout(5)
                client_socket.connect(('localhost', 4221))
                
                # Connection successful - this is what we're testing
                assert True
                
        except socket.timeout:
            pytest.fail("Connection timed out - server may not be accepting connections")
        except ConnectionRefusedError:
            pytest.fail("Connection refused - server is not listening on port 4221")
        except socket.error as e:
            pytest.fail(f"Socket error during connection: {e}")


def test_server_accepts_multiple_connections():
    """Test that the server can handle multiple sequential connections."""
    with http_server_process():
        for i in range(3):
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
                    client_socket.settimeout(5)
                    client_socket.connect(('localhost', 4221))
                    # Brief pause to ensure connection is established
                    time.sleep(0.1)
                    
            except socket.error as e:
                pytest.fail(f"Failed to establish connection #{i+1}: {e}")


def test_server_binds_to_correct_port():
    """Test that the server is specifically binding to port 4221."""
    with http_server_process():
        # Test that we can connect to 4221
        assert is_port_in_use('localhost', 4221), "Server is not listening on port 4221"
        
        # Test that we cannot connect to nearby ports (server should be specific)
        for port in [4220, 4222]:
            assert not is_port_in_use('localhost', port), f"Server should not be listening on port {port}"


def test_server_uses_tcp_protocol():
    """Test that the server is using TCP (not UDP) protocol."""
    with http_server_process():
        # Try to connect using TCP - this should work
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as tcp_socket:
                tcp_socket.settimeout(2)
                tcp_socket.connect(('localhost', 4221))
        except socket.error as e:
            pytest.fail(f"TCP connection failed: {e}")
        
        # Try to send UDP packet - this should not interfere with TCP server
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as udp_socket:
                udp_socket.settimeout(1)
                # Send a UDP packet to the same port - should not crash TCP server
                udp_socket.sendto(b"test", ('localhost', 4221))
        except socket.error:
            # UDP failure is expected and acceptable
            pass


def test_server_handles_connection_gracefully():
    """Test that server doesn't crash when connection is closed abruptly."""
    with http_server_process() as process:
        # Connect and immediately close
        for _ in range(2):
            try:
                client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                client_socket.settimeout(2)
                client_socket.connect(('localhost', 4221))
                client_socket.close()  # Abrupt close
            except socket.error:
                pass  # Connection issues are acceptable for this test
        
        # Give server time to potentially crash
        time.sleep(0.5)
        
        # Check that server process is still running
        poll_result = process.poll()
        if poll_result is not None:
            pytest.fail(f"Server crashed after connection handling (exit code: {poll_result})")