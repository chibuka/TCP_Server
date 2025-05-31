import threading
from conftest import http_server_process
from conftest import send_http_request
import os
import tempfile
import pytest
from conftest import http_server_process, send_http_request

def test_serve_existing_file():
    """Test serving an existing file returns correct content."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create test file
        test_file = os.path.join(temp_dir, "test.txt")
        with open(test_file, "w") as f:
            f.write("Hello, World!")
        
        # Start server with directory flag
        with http_server_process(directory=temp_dir):
            response = send_http_request("GET", "/files/test.txt")
            
            expected_response = (
                "HTTP/1.1 200 OK\r\n"
                "Content-Type: application/octet-stream\r\n"
                "Content-Length: 13\r\n"
                "\r\n"
                "Hello, World!"
            )
            assert response == expected_response, f"Expected file contents, got:\n{response}"

def test_serve_nonexistent_file():
    """Test requesting non-existent file returns 404."""
    with tempfile.TemporaryDirectory() as temp_dir:
        with http_server_process(directory=temp_dir):
            response = send_http_request("GET", "/files/nonexistent.txt")
            assert response == "HTTP/1.1 404 Not Found\r\n\r\n", \
                f"Expected 404 for non-existent file, got:\n{response}"

def test_file_with_binary_content():
    """Test serving a file with binary content."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create binary test file
        test_file = os.path.join(temp_dir, "binary.bin")
        with open(test_file, "wb") as f:
            f.write(b'\x00\x01\x02\x03\xFF')
        
        with http_server_process(directory=temp_dir):
            response = send_http_request("GET", "/files/binary.bin", binary=True)
            
            expected_response = (
                b"HTTP/1.1 200 OK\r\n"
                b"Content-Type: application/octet-stream\r\n"
                b"Content-Length: 5\r\n"
                b"\r\n"
                b'\x00\x01\x02\x03\xFF'
            )
            assert response == expected_response, "Binary file content mismatch"

def test_empty_file():
    """Test serving an empty file."""
    with tempfile.TemporaryDirectory() as temp_dir:
        test_file = os.path.join(temp_dir, "empty.txt")
        open(test_file, "w").close()  # Create empty file
        
        with http_server_process(directory=temp_dir):
            response = send_http_request("GET", "/files/empty.txt")
            
            expected_response = (
                "HTTP/1.1 200 OK\r\n"
                "Content-Type: application/octet-stream\r\n"
                "Content-Length: 0\r\n"
                "\r\n"
            )
            assert response == expected_response, "Empty file response incorrect"

def test_directory_traversal_protection():
    """Test that path traversal attempts are blocked."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a test file we shouldn't be able to access
        sensitive_file = os.path.join(temp_dir, "secret.txt")
        with open(sensitive_file, "w") as f:
            f.write("secret data")
        
        with http_server_process(directory=temp_dir):
            # Try to access file outside the directory
            response = send_http_request("GET", "/files/../secret.txt")
            assert response == "HTTP/1.1 404 Not Found\r\n\r\n", \
                "Path traversal vulnerability detected!"
            
            # Try more complex traversal
            response = send_http_request("GET", "/files/../../../../etc/passwd")
            assert response == "HTTP/1.1 404 Not Found\r\n\r\n", \
                "Complex path traversal vulnerability detected!"

def test_file_with_spaces_in_name():
    """Test files with spaces in their names."""
    with tempfile.TemporaryDirectory() as temp_dir:
        test_file = os.path.join(temp_dir, "file with spaces.txt")
        with open(test_file, "w") as f:
            f.write("content")
        
        with http_server_process(directory=temp_dir):
            response = send_http_request("GET", "/files/file%20with%20spaces.txt")
            
            expected_response = (
                "HTTP/1.1 200 OK\r\n"
                "Content-Type: application/octet-stream\r\n"
                "Content-Length: 7\r\n"
                "\r\n"
                "content"
            )
            assert response == expected_response, "Failed to handle filename with spaces"

def test_concurrent_file_access():
    """Test multiple concurrent requests for files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create multiple test files
        files = {}
        for i in range(3):
            filename = f"file_{i}.txt"
            content = f"content {i}"
            with open(os.path.join(temp_dir, filename), "w") as f:
                f.write(content)
            files[filename] = content
        
        with http_server_process(directory=temp_dir):
            results = []
            threads = []
            
            def make_request(filename):
                response = send_http_request("GET", f"/files/{filename}")
                results.append((filename, response))
            
            # Create and start threads
            for filename in files:
                t = threading.Thread(target=make_request, args=(filename,))
                threads.append(t)
                t.start()
            
            # Wait for all threads
            for t in threads:
                t.join()
            
            # Verify responses
            assert len(results) == 3, "Not all file requests completed"
            for filename, response in results:
                expected_content = files[filename]
                expected_response = (
                    f"HTTP/1.1 200 OK\r\n"
                    f"Content-Type: application/octet-stream\r\n"
                    f"Content-Length: {len(expected_content)}\r\n"
                    f"\r\n"
                    f"{expected_content}"
                )
                assert response == expected_response, \
                    f"File {filename} response incorrect. Got:\n{response}"

def test_directory_flag_required():
    """Test that /files endpoint returns 404 if no directory specified."""
    with http_server_process():  # No directory flag
        response = send_http_request("GET", "/files/test.txt")
        assert response == "HTTP/1.1 404 Not Found\r\n\r\n", \
            "Files endpoint should be disabled when no directory specified"