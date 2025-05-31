import socket
import subprocess
import time
import pytest
import signal
import os
from contextlib import contextmanager


def wait_for_port(host, port, timeout=10):
    """Wait for a port to become available."""
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(1)
                result = sock.connect_ex((host, port))
                if result == 0:
                    return True
        except socket.error:
            pass
        time.sleep(0.1)
    return False


def is_port_in_use(host, port):
    """Check if a port is already in use."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(1)
            result = sock.connect_ex((host, port))
            return result == 0
    except socket.error:
        return False


# Add this to your existing conftest.py

@contextmanager
def http_server_process(directory=None):
    """Context manager to start and stop the HTTP server process with optional directory."""
    if is_port_in_use('localhost', 4221):
        pytest.fail("Port 4221 is already in use. Please stop any existing servers.")
    
    process = None
    try:
        cmd = ['python3', 'main.py']
        if directory:
            cmd.extend(['--directory', directory])
        
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            preexec_fn=os.setsid if hasattr(os, 'setsid') else None
        )
        
        if not wait_for_port('localhost', 4221, timeout=10):
            stdout, stderr = process.communicate(timeout=2)
            error_msg = f"Server failed to start listening on port 4221 within 10 seconds"
            if stderr:
                error_msg += f"\nServer stderr: {stderr.decode()}"
            if stdout:
                error_msg += f"\nServer stdout: {stdout.decode()}"
            pytest.fail(error_msg)
        
        yield process
        
    except subprocess.TimeoutExpired:
        pytest.fail("Server process timed out during startup")
    except FileNotFoundError:
        pytest.fail("Could not start server: python3 not found or main.py missing")
    finally:
        if process:
            try:
                if hasattr(os, 'killpg'):
                    os.killpg(os.getpgid(process.pid), signal.SIGTERM)
                else:
                    process.terminate()
                
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    if hasattr(os, 'killpg'):
                        os.killpg(os.getpgid(process.pid), signal.SIGKILL)
                    else:
                        process.kill()
                    process.wait()
            except (ProcessLookupError, OSError):
                pass

# Add binary mode support to send_http_request
def send_http_request(method, path=None, headers=None, body=None, timeout=5, binary=False):
    """Send HTTP request and return response (as text or binary)."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(timeout)
            sock.connect(('localhost', 4221))
            
            # Build request
            request_lines = [f"{method} {path} HTTP/1.1"]
            request_lines.append("Host: localhost:4221")
            
            if headers:
                for header, value in headers.items():
                    request_lines.append(f"{header}: {value}")
            
            request_lines.append("")  # Empty line before body
            
            if body:
                request_lines.append(body)
            
            request = "\r\n".join(request_lines)
            if not body:
                request += "\r\n"
            
            sock.sendall(request.encode())
            
            # Receive response
            response = b""
            while True:
                try:
                    chunk = sock.recv(4096)
                    if not chunk:
                        break
                    response += chunk
                    # Stop if we have a complete HTTP response
                    if b'\r\n\r\n' in response:
                        if b"Content-Length:" in response:
                            # For responses with content, read until we have all content
                            headers_part, body_part = response.split(b'\r\n\r\n', 1)
                            content_length = 0
                            for line in headers_part.split(b'\r\n'):
                                if line.lower().startswith(b'content-length:'):
                                    content_length = int(line.split(b':')[1].strip())
                                    break
                            if len(body_part) >= content_length:
                                break
                except socket.timeout:
                    break
            
            return response if binary else response.decode('utf-8', errors='ignore')
    except socket.error as e:
        pytest.fail(f"Failed to send HTTP request: {e}")