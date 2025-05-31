from conftest import http_server_process, send_http_request
import pytest


def test_get_user_agent_basic():
    """Test GET /user-agent with a standard User-Agent header."""
    with http_server_process():
        user_agent_value = "test-client/1.0"
        headers = {"User-Agent": user_agent_value}
        response = send_http_request("GET", "/user-agent", headers=headers)

        expected_body = user_agent_value
        expected_response_start = (
            "HTTP/1.1 200 OK\r\n"
            "Content-Type: text/plain\r\n"
            f"Content-Length: {len(expected_body)}\r\n"
            "\r\n"
        )
        assert response == expected_response_start + expected_body, \
            f"Expected body '{expected_body}', got response:\n{response}"

@pytest.mark.parametrize("header_name", ["user-agent", "USER-AGENT", "uSeR-aGeNt"])
def test_get_user_agent_case_insensitive_header_name(header_name):
    """Test User-Agent header name is matched case-insensitively."""
    with http_server_process():
        user_agent_value = "case-test-client/1.1"
        headers = {header_name: user_agent_value}
        response = send_http_request("GET", "/user-agent", headers=headers)

        expected_body = user_agent_value
        expected_response_start = (
            "HTTP/1.1 200 OK\r\n"
            "Content-Type: text/plain\r\n"
            f"Content-Length: {len(expected_body)}\r\n"
            "\r\n"
        )
        assert response == expected_response_start + expected_body, \
            f"Failed for header '{header_name}'. Expected body '{expected_body}', got response:\n{response}"

def test_get_user_agent_with_leading_trailing_whitespace_in_value():
    """Test User-Agent value is trimmed."""
    with http_server_process():
        # The server should trim the value part after "User-Agent: "
        user_agent_value_sent = "  whitespace-client/2.0  "
        user_agent_value_expected = "whitespace-client/2.0" # Assuming server trims it
        headers = {"User-Agent": user_agent_value_sent}
        response = send_http_request("GET", "/user-agent", headers=headers)

        expected_body = user_agent_value_expected
        expected_response_start = (
            "HTTP/1.1 200 OK\r\n"
            "Content-Type: text/plain\r\n"
            f"Content-Length: {len(expected_body)}\r\n"
            "\r\n"
        )
        assert response == expected_response_start + expected_body, \
            f"Expected body '{expected_body}' after trimming, got response:\n{response}"

def test_get_user_agent_missing():
    """Test GET /user-agent when User-Agent header is not present."""
    with http_server_process():
        # No User-Agent header sent
        response = send_http_request("GET", "/user-agent", headers={}) # Send Host only or allow helper to do it

        expected_body = "" # If header is missing, value should be empty
        expected_response_start = (
            "HTTP/1.1 200 OK\r\n"
            "Content-Type: text/plain\r\n"
            f"Content-Length: {len(expected_body)}\r\n"
            "\r\n"
        )
        assert response == expected_response_start + expected_body, \
            f"Expected empty body when User-Agent is missing, got response:\n{response}"

def test_get_user_agent_empty_value():
    """Test GET /user-agent when User-Agent header has an empty value."""
    with http_server_process():
        headers = {"User-Agent": ""} # Empty value
        response = send_http_request("GET", "/user-agent", headers=headers)

        expected_body = ""
        expected_response_start = (
            "HTTP/1.1 200 OK\r\n"
            "Content-Type: text/plain\r\n"
            f"Content-Length: {len(expected_body)}\r\n"
            "\r\n"
        )
        assert response == expected_response_start + expected_body, \
            f"Expected empty body for empty User-Agent value, got response:\n{response}"


@pytest.mark.parametrize("ua_string", [
    "curl/7.64.1",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "MyCustomApplication/1.0 (TestMode; NoRetry)",
    "foobar/1.2.3",
    "Apache-HttpClient/4.5.13 (Java/11.0.12)"
])
def test_get_user_agent_various_formats(ua_string):
    """Test GET /user-agent with various common User-Agent string formats."""
    with http_server_process():
        headers = {"User-Agent": ua_string}
        response = send_http_request("GET", "/user-agent", headers=headers)

        expected_body = ua_string
        expected_response_start = (
            "HTTP/1.1 200 OK\r\n"
            "Content-Type: text/plain\r\n"
            f"Content-Length: {len(expected_body)}\r\n"
            "\r\n"
        )
        assert response == expected_response_start + expected_body, \
            f"Failed for UA '{ua_string}'. Expected body '{expected_body}', got response:\n{response}"

def test_get_user_agent_with_other_headers_present():
    """Test GET /user-agent correctly extracts User-Agent among other headers."""
    with http_server_process():
        user_agent_value = "specific-client/4.0"
        headers = {
            "User-Agent": user_agent_value,
            "Accept": "application/json",
            "X-Custom-Header": "SomeValue",
            "Connection": "keep-alive"
        }
        response = send_http_request("GET", "/user-agent", headers=headers)

        expected_body = user_agent_value
        expected_response_start = (
            "HTTP/1.1 200 OK\r\n"
            "Content-Type: text/plain\r\n"
            f"Content-Length: {len(expected_body)}\r\n"
            "\r\n"
        )
        assert response == expected_response_start + expected_body, \
            f"Failed to extract User-Agent among other headers. Got response:\n{response}"

def test_user_agent_path_is_not_root():
    """Ensure /user-agent is distinct from /."""
    with http_server_process():
        response_root = send_http_request("GET", "/")
        assert "HTTP/1.1 200 OK\r\n\r\n" == response_root # Assuming / still returns simple 200 OK

        user_agent_value = "client-check/0.1"
        headers = {"User-Agent": user_agent_value}
        response_ua = send_http_request("GET", "/user-agent", headers=headers)
        assert user_agent_value in response_ua
        assert response_root != response_ua

def test_other_paths_still_404_after_user_agent():
    """Ensure that adding /user-agent doesn't make other random paths 200 OK."""
    with http_server_process():
        response = send_http_request("GET", "/this-path-does-not-exist")
        expected_response = "HTTP/1.1 404 Not Found\r\n\r\n"
        assert response == expected_response, \
            f"Expected 404 for random path, got:\n{response}"

def test_echo_path_still_works_after_user_agent():
    """Ensure /echo path still works."""
    with http_server_process():
        echo_msg = "hello_world_echo_test"
        response = send_http_request("GET", f"/echo/{echo_msg}")
        
        expected_body = echo_msg
        expected_response_start = (
            "HTTP/1.1 200 OK\r\n"
            "Content-Type: text/plain\r\n"
            f"Content-Length: {len(expected_body)}\r\n"
            "\r\n"
        )
        assert response == expected_response_start + expected_body, \
            f"Echo path failed. Got response:\n{response}"

def test_post_to_user_agent_path_is_404():
    """Test that POST to /user-agent (which is defined for GET) returns 404."""
    with http_server_process():
        # Based on "Your Updated Routing": GET /user-agent is defined.
        # Other methods to this path should fall under "GET /anything-else -> 404 Not Found"
        # or more specifically, method not allowed for this path. 404 is a safe bet given the current routing.
        response = send_http_request("POST", "/user-agent", body="some_data=value")
        expected_response = "HTTP/1.1 404 Not Found\r\n\r\n"
        assert response == expected_response, \
            f"Expected 404 for POST to /user-agent, got:\n{response}"
