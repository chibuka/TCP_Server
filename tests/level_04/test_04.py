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


def test_echo_returns_correct_string():
    with http_server_process():
        request = "GET /echo/hello HTTP/1.1\r\nHost: localhost:4221\r\n\r\n"
        response = send_http_request(request)

        assert response.startswith("HTTP/1.1 200 OK\r\n")
        assert "Content-Type: text/plain" in response
        assert "Content-Length: 5" in response
        assert response.endswith("\r\n\r\nhello")


def test_echo_empty_string():
    with http_server_process():
        request = "GET /echo/ HTTP/1.1\r\nHost: localhost:4221\r\n\r\n"
        response = send_http_request(request)

        assert response.startswith("HTTP/1.1 200 OK\r\n")
        assert "Content-Length: 0" in response
        assert response.endswith("\r\n\r\n")


def test_echo_with_special_characters():
    with http_server_process():
        value = "123_ABC-def%20xyz"
        request = f"GET /echo/{value} HTTP/1.1\r\nHost: localhost:4221\r\n\r\n"
        response = send_http_request(request)

        assert response.startswith("HTTP/1.1 200 OK\r\n")
        assert f"Content-Length: {len(value)}" in response
        assert response.endswith(f"\r\n\r\n{value}")


def test_echo_long_string():
    with http_server_process():
        long_string = "a" * 1000
        request = f"GET /echo/{long_string} HTTP/1.1\r\nHost: localhost:4221\r\n\r\n"
        response = send_http_request(request)

        assert response.startswith("HTTP/1.1 200 OK\r\n")
        assert f"Content-Length: {len(long_string)}" in response
        assert response.endswith(f"\r\n\r\n{long_string}")


def test_echo_invalid_path_returns_404_or_equivalent():
    with http_server_process():
        request = "GET /echox/test HTTP/1.1\r\nHost: localhost:4221\r\n\r\n"
        response = send_http_request(request)

        status_line = response.split("\r\n")[0]
        assert "404" in status_line or "400" in status_line, f"Expected 404 or 400, got: {status_line}"
