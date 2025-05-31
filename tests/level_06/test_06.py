import threading
import time
import socket
import pytest
from conftest import http_server_process, send_http_request

def test_single_connection_basic():
    """Basic test that single connection still works with concurrent server."""
    with http_server_process():
        response = send_http_request("GET", "/")
        assert response == "HTTP/1.1 200 OK\r\n\r\n", \
            f"Basic single connection failed. Got response:\n{response}"

def test_multiple_sequential_connections():
    """Test that multiple sequential connections work."""
    with http_server_process():
        responses = []
        for _ in range(3):
            response = send_http_request("GET", "/")
            responses.append(response)
        
        for response in responses:
            assert response == "HTTP/1.1 200 OK\r\n\r\n", \
                f"Expected 200 OK for sequential connections. Got:\n{response}"

def test_concurrent_connections_basic():
    """Test basic concurrent connection handling."""
    with http_server_process():
        results = []
        threads = []
        
        def make_request():
            try:
                response = send_http_request("GET", "/")
                results.append(response)
            except Exception as e:
                results.append(str(e))
        
        # Create and start multiple threads
        for _ in range(3):
            t = threading.Thread(target=make_request)
            threads.append(t)
            t.start()
        
        # Wait for all threads to complete
        for t in threads:
            t.join()
        
        # Verify all responses
        assert len(results) == 3, "Not all requests completed"
        for response in results:
            assert response == "HTTP/1.1 200 OK\r\n\r\n", \
                f"Expected 200 OK for concurrent connection. Got:\n{response}"

def test_concurrent_connections_with_delays():
    """Test that slow connections don't block others."""
    with http_server_process():
        results = []
        threads = []
        
        def make_request(delay):
            try:
                time.sleep(delay)
                response = send_http_request("GET", "/")
                results.append((delay, response))
            except Exception as e:
                results.append((delay, str(e)))
        
        # Create requests with different delays
        delays = [0.1, 0.5, 1.0]
        for delay in delays:
            t = threading.Thread(target=make_request, args=(delay,))
            threads.append(t)
            t.start()
        
        # Wait for all threads to complete
        for t in threads:
            t.join()
        
        # Verify all responses
        assert len(results) == 3, "Not all requests completed"
        for delay, response in results:
            assert response == "HTTP/1.1 200 OK\r\n\r\n", \
                f"Expected 200 OK for delayed connection (delay={delay}). Got:\n{response}"

def test_concurrent_connections_with_different_paths():
    """Test concurrent connections to different paths."""
    with http_server_process():
        results = []
        threads = []
        
        def make_request(path):
            try:
                response = send_http_request("GET", path)
                results.append((path, response))
            except Exception as e:
                results.append((path, str(e)))
        
        # Create requests for different paths
        paths = ["/", "/echo/test", "/user-agent"]
        for path in paths:
            headers = {"User-Agent": "concurrent-test"} if path == "/user-agent" else {}
            t = threading.Thread(target=make_request, args=(path,))
            threads.append(t)
            t.start()
        
        # Wait for all threads to complete
        for t in threads:
            t.join()
        
        # Verify responses
        assert len(results) == 3, "Not all requests completed"
        for path, response in results:
            if path == "/":
                assert response == "HTTP/1.1 200 OK\r\n\r\n", \
                    f"Root path failed. Got:\n{response}"
            elif path == "/echo/test":
                expected = "HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\nContent-Length: 4\r\n\r\ntest"
                assert response == expected, \
                    f"Echo path failed. Got:\n{response}"
            elif path == "/user-agent":
                expected = "HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\nContent-Length: 15\r\n\r\nconcurrent-test"
                assert response == expected, \
                    f"User-Agent path failed. Got:\n{response}"

def test_many_concurrent_connections():
    """Stress test with many concurrent connections."""
    with http_server_process():
        results = []
        threads = []
        num_connections = 10  # Adjust based on your system capabilities
        
        def make_request():
            try:
                response = send_http_request("GET", "/")
                results.append(response)
            except Exception as e:
                results.append(str(e))
        
        # Create and start many threads
        for _ in range(num_connections):
            t = threading.Thread(target=make_request)
            threads.append(t)
            t.start()
        
        # Wait for all threads to complete
        for t in threads:
            t.join()
        
        # Verify all responses
        assert len(results) == num_connections, "Not all requests completed"
        for response in results:
            assert response == "HTTP/1.1 200 OK\r\n\r\n", \
                f"Expected 200 OK for concurrent connection. Got:\n{response}"

def test_concurrent_connections_with_error():
    """Test that one bad connection doesn't affect others."""
    with http_server_process():
        results = []
        threads = []
        
        def make_request(good_request):
            try:
                if good_request:
                    response = send_http_request("GET", "/")
                else:
                    # Send malformed request
                    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                        s.connect(('localhost', 4221))
                        s.sendall(b"GARBAGE\r\n\r\n")
                        response = s.recv(4096).decode()
                results.append((good_request, response))
            except Exception as e:
                results.append((good_request, str(e)))
        
        # Create both good and bad requests
        threads.append(threading.Thread(target=make_request, args=(False,)))  # Bad request
        for _ in range(2):
            threads.append(threading.Thread(target=make_request, args=(True,)))  # Good requests
        
        for t in threads:
            t.start()
        
        for t in threads:
            t.join()
        
        # Verify good requests succeeded
        good_responses = [r for good, r in results if good]
        assert len(good_responses) == 2, "Good requests didn't all complete"
        for response in good_responses:
            assert response == "HTTP/1.1 200 OK\r\n\r\n", \
                f"Good request failed. Got:\n{response}"

def test_connection_persistence():
    """Test that connections can be reused (if keep-alive is supported)."""
    with http_server_process():
        # This test assumes the server supports keep-alive (not required but good if it does)
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect(('localhost', 4221))
                
                # Send first request
                s.sendall(b"GET / HTTP/1.1\r\nHost: localhost:4221\r\n\r\n")
                response1 = s.recv(4096).decode()
                assert "HTTP/1.1 200 OK" in response1, "First request failed"
                
                # Send second request on same connection
                s.sendall(b"GET /echo/test HTTP/1.1\r\nHost: localhost:4221\r\n\r\n")
                response2 = s.recv(4096).decode()
                assert "HTTP/1.1 200 OK" in response2 and "test" in response2, "Second request failed"
        except socket.error as e:
            pytest.fail(f"Connection persistence test failed: {e}")