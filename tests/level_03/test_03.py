from conftest import http_server_process
from conftest import send_http_request


def test_root_path_returns_200():
    """Test that root path '/' returns 200 OK."""
    with http_server_process():
        response = send_http_request("GET", "/")
        
        expected_response = "HTTP/1.1 200 OK\r\n\r\n"
        assert response == expected_response, f"Expected '{expected_response}' for path '/', got '{response}'"


def test_random_path_returns_404():
    """Test that random path returns 404 Not Found (as per mission example)."""
    with http_server_process():
        response = send_http_request("GET", "/abcdefg")
        
        expected_response = "HTTP/1.1 404 Not Found\r\n\r\n"
        assert response == expected_response, f"Expected '{expected_response}' for path '/abcdefg', got '{response}'"


def test_various_paths_return_404():
    """Test that various non-root paths return 404 Not Found."""
    with http_server_process():
        test_paths = [
            "/index.html",
            "/test",
            "/foo/bar",
            "/api/users",
            "/static/style.css",
            "/favicon.ico",
            "/path/with/many/segments"
        ]
        
        for path in test_paths:
            response = send_http_request("GET", path)
            expected_response = "HTTP/1.1 404 Not Found\r\n\r\n"
            assert response == expected_response, f"Expected '{expected_response}' for path '{path}', got '{response}'"


def test_path_parsing_with_query_parameters():
    """Test that paths with query parameters are treated as 404."""
    with http_server_process():
        test_paths = [
            "/?param=value",
            "/search?q=test",
            "/api?key=123&value=abc"
        ]
        
        for path in test_paths:
            response = send_http_request("GET", path)
            expected_response = "HTTP/1.1 404 Not Found\r\n\r\n"
            assert response == expected_response, f"Expected '{expected_response}' for path '{path}', got '{response}'"


def test_different_http_methods_with_root_path():
    """Test that different HTTP methods to root path return 200."""
    with http_server_process():
        methods = ["GET", "POST", "PUT", "DELETE", "HEAD", "OPTIONS"]
        
        for method in methods:
            response = send_http_request(method, "/")
            expected_response = "HTTP/1.1 200 OK\r\n\r\n"
            assert response == expected_response, f"Expected '{expected_response}' for {method} /, got '{response}'"


def test_different_http_methods_with_non_root_path():
    """Test that different HTTP methods to non-root paths return 404."""
    with http_server_process():
        methods = ["GET", "POST", "PUT", "DELETE", "HEAD", "OPTIONS"]
        
        for method in methods:
            response = send_http_request(method, "/test")
            expected_response = "HTTP/1.1 404 Not Found\r\n\r\n"
            assert response == expected_response, f"Expected '{expected_response}' for {method} /test, got '{response}'"


def test_case_sensitive_path_parsing():
    """Test that path parsing is case-sensitive."""
    with http_server_process():
        # These should all be 404 since they're not exactly "/"
        case_variations = ["/", "/INDEX", "/Index", "/HOME", "/home"]
        
        # Only "/" should return 200
        response = send_http_request("GET", "/")
        expected_response = "HTTP/1.1 200 OK\r\n\r\n"
        assert response == expected_response, f"Expected '{expected_response}' for '/', got '{response}'"
        
        # All others should return 404
        for path in ["/INDEX", "/Index", "/HOME", "/home"]:
            response = send_http_request("GET", path)
            expected_response = "HTTP/1.1 404 Not Found\r\n\r\n"
            assert response == expected_response, f"Expected '{expected_response}' for '{path}', got '{response}'"


def test_path_with_trailing_characters():
    """Test that paths similar to root but with extra characters return 404."""
    with http_server_process():
        similar_paths = [
            "//",
            "/.",
            "/ ",
            "/\t",
            "/index",
            "/root"
        ]
        
        for path in similar_paths:
            response = send_http_request("GET", path)
            expected_response = "HTTP/1.1 404 Not Found\r\n\r\n"
            assert response == expected_response, f"Expected '{expected_response}' for '{path}', got '{response}'"


def test_handles_complex_request_headers():
    """Test that server correctly parses path even with complex headers."""
    with http_server_process():
        headers = {
            "User-Agent": "curl/7.64.1",
            "Accept": "*/*",
            "Authorization": "Bearer token123",
            "Content-Type": "application/json"
        }
        
        # Test root path with headers
        response = send_http_request("GET", "/", headers=headers)
        expected_response = "HTTP/1.1 200 OK\r\n\r\n"
        assert response == expected_response, f"Expected '{expected_response}' for '/' with headers, got '{response}'"
        
        # Test non-root path with headers
        response = send_http_request("GET", "/api", headers=headers)
        expected_response = "HTTP/1.1 404 Not Found\r\n\r\n"
        assert response == expected_response, f"Expected '{expected_response}' for '/api' with headers, got '{response}'"


def test_handles_post_request_with_body():
    """Test that server correctly parses path from POST requests with body."""
    with http_server_process():
        body = '{"key": "value", "test": "data"}'
        headers = {"Content-Type": "application/json", "Content-Length": str(len(body))}
        
        # Test root path with POST body
        response = send_http_request("POST", "/", headers=headers, body=body)
        expected_response = "HTTP/1.1 200 OK\r\n\r\n"
        assert response == expected_response, f"Expected '{expected_response}' for POST /, got '{response}'"
        
        # Test non-root path with POST body
        response = send_http_request("POST", "/submit", headers=headers, body=body)
        expected_response = "HTTP/1.1 404 Not Found\r\n\r\n"
        assert response == expected_response, f"Expected '{expected_response}' for POST /submit, got '{response}'"


def test_sequential_requests_maintain_logic():
    """Test that server maintains correct path logic across multiple requests."""
    with http_server_process():
        # Alternate between root and non-root paths
        test_sequence = [
            ("/", "HTTP/1.1 200 OK\r\n\r\n"),
            ("/test", "HTTP/1.1 404 Not Found\r\n\r\n"),
            ("/", "HTTP/1.1 200 OK\r\n\r\n"),
            ("/another", "HTTP/1.1 404 Not Found\r\n\r\n"),
            ("/", "HTTP/1.1 200 OK\r\n\r\n")
        ]
        
        for i, (path, expected_response) in enumerate(test_sequence):
            response = send_http_request("GET", path)
            assert response == expected_response, f"Request #{i+1} failed: path '{path}' expected '{expected_response}', got '{response}'"