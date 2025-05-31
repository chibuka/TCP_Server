import time
from conftest import http_server_process
from conftest import send_http_request
from conftest import is_port_in_use
from conftest import wait_for_port
import pytest
import socket
import subprocess
from contextlib import contextmanager
import os


def test_server_responds_to_http_request():
    """Test that server responds to basic HTTP GET request."""
    with http_server_process():
        request = "GET / HTTP/1.1\r\nHost: localhost:4221\r\n\r\n"
        response = send_http_request(request)
        
        # Server should respond with something
        assert response, "Server did not send any response to HTTP request"


def test_http_status_line_format():
    """Test that server responds with proper HTTP/1.1 200 OK status line."""
    with http_server_process():
        request = "GET / HTTP/1.1\r\nHost: localhost:4221\r\n\r\n"
        response = send_http_request(request)
        
        # Check if response starts with correct status line
        lines = response.split('\r\n')
        assert len(lines) > 0, "Response is empty or malformed"
        
        status_line = lines[0]
        assert status_line == "HTTP/1.1 200 OK", f"Expected 'HTTP/1.1 200 OK', got '{status_line}'"


def test_exact_http_response_format():
    """Test that server responds with exactly 'HTTP/1.1 200 OK\\r\\n\\r\\n'."""
    with http_server_process():
        request = "GET / HTTP/1.1\r\nHost: localhost:4221\r\n\r\n"
        response = send_http_request(request)
        
        # Check for exact response as specified in mission
        expected_response = "HTTP/1.1 200 OK\r\n\r\n"
        assert response == expected_response, f"Expected exactly '{expected_response}', got '{response}'"


def test_http_line_endings():
    """Test that server uses proper HTTP line endings (\\r\\n)."""
    with http_server_process():
        request = "GET / HTTP/1.1\r\nHost: localhost:4221\r\n\r\n"
        response = send_http_request(request)
        
        # Check that response uses \r\n not just \n
        assert '\r\n' in response, "Response must use HTTP line endings (\\r\\n)"
        assert response.count('\r\n') >= 2, "Response must have status line + empty headers (at least 2 \\r\\n)"


def test_response_to_different_paths():
    """Test that server responds the same way to different request paths."""
    with http_server_process():
        paths = ["/", "/test", "/anything", "/foo/bar"]
        
        for path in paths:
            request = f"GET {path} HTTP/1.1\r\nHost: localhost:4221\r\n\r\n"
            response = send_http_request(request)
            
            # Should get same response regardless of path (as per mission instructions)
            expected_response = "HTTP/1.1 200 OK\r\n\r\n"
            assert response == expected_response, f"Response for path '{path}' should be same: '{expected_response}', got '{response}'"


def test_response_to_different_methods():
    """Test that server responds the same way to different HTTP methods."""
    with http_server_process():
        methods = ["GET", "POST", "PUT", "DELETE"]
        
        for method in methods:
            request = f"{method} / HTTP/1.1\r\nHost: localhost:4221\r\n\r\n"
            response = send_http_request(request)
            
            # Should get same response regardless of method (as per mission instructions)
            expected_response = "HTTP/1.1 200 OK\r\n\r\n"
            assert response == expected_response, f"Response for method '{method}' should be same: '{expected_response}', got '{response}'"


def test_handles_request_with_headers():
    """Test that server handles requests with additional headers."""
    with http_server_process():
        request = (
            "GET / HTTP/1.1\r\n"
            "Host: localhost:4221\r\n"
            "User-Agent: test-client\r\n"
            "Accept: text/html\r\n"
            "\r\n"
        )
        response = send_http_request(request)
        
        expected_response = "HTTP/1.1 200 OK\r\n\r\n"
        assert response == expected_response, f"Server should ignore request headers and send: '{expected_response}', got '{response}'"


def test_handles_request_with_body():
    """Test that server handles POST requests with body data."""
    with http_server_process():
        request_body = "test data"
        request = (
            "POST / HTTP/1.1\r\n"
            "Host: localhost:4221\r\n"
            f"Content-Length: {len(request_body)}\r\n"
            "\r\n"
            f"{request_body}"
        )
        response = send_http_request(request)
        
        expected_response = "HTTP/1.1 200 OK\r\n\r\n"
        assert response == expected_response, f"Server should ignore request body and send: '{expected_response}', got '{response}'"


def test_multiple_sequential_requests():
    """Test that server can handle multiple sequential HTTP requests."""
    with http_server_process():
        for i in range(3):
            request = f"GET /test{i} HTTP/1.1\r\nHost: localhost:4221\r\n\r\n"
            response = send_http_request(request)
            
            expected_response = "HTTP/1.1 200 OK\r\n\r\n"
            assert response == expected_response, f"Request #{i+1} failed: expected '{expected_response}', got '{response}'"


def test_response_completeness():
    """Test that the response is complete and properly terminated."""
    with http_server_process():
        request = "GET / HTTP/1.1\r\nHost: localhost:4221\r\n\r\n"
        response = send_http_request(request)
        
        # Response should end with \r\n\r\n (status line + empty headers section)
        assert response.endswith('\r\n\r\n'), "HTTP response must end with \\r\\n\\r\\n"
        
        # Response should not have extra content
        expected_response = "HTTP/1.1 200 OK\r\n\r\n"
        assert len(response) == len(expected_response), f"Response should be exactly {len(expected_response)} characters"