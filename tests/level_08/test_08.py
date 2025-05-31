import tempfile
import threading
from conftest import http_server_process
from conftest import send_http_request
import os
from conftest import http_server_process, send_http_request

def test_create_new_file():
    """Test basic file creation via POST."""
    with tempfile.TemporaryDirectory() as temp_dir:
        with http_server_process(directory=temp_dir):
            # Send POST request with file content
            filename = "testfile.txt"
            content = "Hello, World!"
            headers = {
                "Content-Type": "application/octet-stream",
                "Content-Length": str(len(content))
            }
            response = send_http_request(
                "POST", 
                f"/files/{filename}",
                headers=headers,
                body=content
            )
            
            # Check response
            assert response == "HTTP/1.1 201 Created\r\n\r\n", \
                f"Expected 201 Created, got:\n{response}"
            
            # Verify file was created
            created_file = os.path.join(temp_dir, filename)
            assert os.path.exists(created_file), "File was not created"
            
            # Verify content
            with open(created_file, "r") as f:
                assert f.read() == content, "File content mismatch"

def test_overwrite_existing_file():
    """Test that POST overwrites existing files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create initial file
        filename = "existing.txt"
        initial_content = "Old content"
        with open(os.path.join(temp_dir, filename), "w") as f:
            f.write(initial_content)
        
        with http_server_process(directory=temp_dir):
            # Send POST with new content
            new_content = "New content"
            headers = {
                "Content-Type": "application/octet-stream",
                "Content-Length": str(len(new_content))
            }
            response = send_http_request(
                "POST",
                f"/files/{filename}",
                headers=headers,
                body=new_content
            )
            
            # Check response
            assert response == "HTTP/1.1 201 Created\r\n\r\n"
            
            # Verify content was overwritten
            with open(os.path.join(temp_dir, filename), "r") as f:
                assert f.read() == new_content

def test_create_file_with_binary_content():
    """Test file creation with binary data."""
    with tempfile.TemporaryDirectory() as temp_dir:
        with http_server_process(directory=temp_dir):
            filename = "binary.bin"
            content = b'\x00\x01\x02\x03\xFF'
            headers = {
                "Content-Type": "application/octet-stream",
                "Content-Length": str(len(content))
            }
            response = send_http_request(
                "POST",
                f"/files/{filename}",
                headers=headers,
                body=content,
                binary=True
            )
            
            assert response == "HTTP/1.1 201 Created\r\n\r\n"
            
            # Verify binary content
            created_file = os.path.join(temp_dir, filename)
            with open(created_file, "rb") as f:
                assert f.read() == content

def test_missing_content_length():
    """Test that missing Content-Length header returns 400."""
    with tempfile.TemporaryDirectory() as temp_dir:
        with http_server_process(directory=temp_dir):
            response = send_http_request(
                "POST",
                "/files/test.txt",
                headers={"Content-Type": "application/octet-stream"},
                body="some content"
            )
            assert response == "HTTP/1.1 400 Bad Request\r\n\r\n", \
                "Should require Content-Length header"

def test_empty_file_creation():
    """Test creating an empty file."""
    with tempfile.TemporaryDirectory() as temp_dir:
        with http_server_process(directory=temp_dir):
            filename = "empty.txt"
            headers = {
                "Content-Type": "application/octet-stream",
                "Content-Length": "0"
            }
            response = send_http_request(
                "POST",
                f"/files/{filename}",
                headers=headers,
                body=""
            )
            
            assert response == "HTTP/1.1 201 Created\r\n\r\n"
            
            # Verify empty file
            created_file = os.path.join(temp_dir, filename)
            assert os.path.exists(created_file)
            assert os.path.getsize(created_file) == 0

def test_directory_traversal_protection():
    """Test that path traversal attempts are blocked."""
    with tempfile.TemporaryDirectory() as temp_dir:
        with http_server_process(directory=temp_dir):
            # Try to create file outside the directory
            response = send_http_request(
                "POST",
                "/files/../outside.txt",
                headers={
                    "Content-Type": "application/octet-stream",
                    "Content-Length": "5"
                },
                body="hello"
            )
            assert response == "HTTP/1.1 403 Forbidden\r\n\r\n", \
                "Should block path traversal attempts"

def test_filename_with_spaces():
    """Test filenames with spaces."""
    with tempfile.TemporaryDirectory() as temp_dir:
        with http_server_process(directory=temp_dir):
            filename = "file with spaces.txt"
            content = "content"
            headers = {
                "Content-Type": "application/octet-stream",
                "Content-Length": str(len(content))
            }
            response = send_http_request(
                "POST",
                f"/files/{filename}",
                headers=headers,
                body=content
            )
            
            assert response == "HTTP/1.1 201 Created\r\n\r\n"
            
            # Verify file was created with spaces
            created_file = os.path.join(temp_dir, filename)
            assert os.path.exists(created_file)

def test_concurrent_file_creation():
    """Test multiple concurrent file uploads."""
    with tempfile.TemporaryDirectory() as temp_dir:
        with http_server_process(directory=temp_dir):
            results = []
            threads = []
            
            def make_request(filename, content):
                headers = {
                    "Content-Type": "application/octet-stream",
                    "Content-Length": str(len(content))
                }
                response = send_http_request(
                    "POST",
                    f"/files/{filename}",
                    headers=headers,
                    body=content
                )
                results.append((filename, response))
            
            # Create and start threads
            for i in range(3):
                filename = f"file_{i}.txt"
                content = f"content {i}"
                t = threading.Thread(target=make_request, args=(filename, content))
                threads.append(t)
                t.start()
            
            # Wait for all threads
            for t in threads:
                t.join()
            
            # Verify responses
            assert len(results) == 3, "Not all requests completed"
            for filename, response in results:
                assert response == "HTTP/1.1 201 Created\r\n\r\n", \
                    f"File {filename} creation failed"
                
                # Verify file was created
                assert os.path.exists(os.path.join(temp_dir, filename))

def test_post_without_directory_flag():
    """Test that POST /files returns 404 when no directory specified."""
    with http_server_process():  # No directory flag
        response = send_http_request(
            "POST",
            "/files/test.txt",
            headers={
                "Content-Type": "application/octet-stream",
                "Content-Length": "5"
            },
            body="hello"
        )
        assert response == "HTTP/1.1 404 Not Found\r\n\r\n", \
            "Files endpoint should be disabled when no directory specified"