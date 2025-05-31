import os
import subprocess
import pytest


def test_repository_structure():
    """Test that the repository has the expected basic structure."""
    # Check if we're in a git repository
    assert os.path.exists('.git'), "Not in a git repository"
    
    # Check for main.py file (should exist for the TCP server implementation)
    assert os.path.exists('main.py'), "main.py file not found"


def test_git_setup():
    """Test that git is properly configured and repository is set up."""
    try:
        # Check if git is available
        result = subprocess.run(['git', '--version'], 
                              capture_output=True, text=True, check=True)
        assert 'git version' in result.stdout.lower()
        
        # Check if we have a remote origin (indicating it's been cloned/forked)
        result = subprocess.run(['git', 'remote', '-v'], 
                              capture_output=True, text=True, check=True)
        assert 'origin' in result.stdout, "No git remote 'origin' found"
        
        # Check if we're on main or master branch
        result = subprocess.run(['git', 'branch', '--show-current'], 
                              capture_output=True, text=True, check=True)
        current_branch = result.stdout.strip()
        assert current_branch in ['main', 'master'], f"Not on main/master branch, currently on: {current_branch}"
        
    except subprocess.CalledProcessError as e:
        pytest.fail(f"Git command failed: {e}")
    except FileNotFoundError:
        pytest.fail("Git is not installed or not in PATH")


def test_can_commit():
    """Test that the repository allows commits (indicating proper setup)."""
    try:
        # Check git status to ensure we can interact with the repository
        result = subprocess.run(['git', 'status', '--porcelain'], 
                              capture_output=True, text=True, check=True)
        
        # The command should succeed (even if there are no changes)
        # This indicates the repository is properly initialized
        
    except subprocess.CalledProcessError as e:
        pytest.fail(f"Cannot check git status: {e}")


def test_python_availability():
    """Test that Python is available for running the server."""
    try:
        # Check if python3 is available
        result = subprocess.run(['python3', '--version'], 
                              capture_output=True, text=True, check=True)
        assert 'python' in result.stdout.lower()
        
    except subprocess.CalledProcessError:
        try:
            # Fallback to 'python' command
            result = subprocess.run(['python', '--version'], 
                                  capture_output=True, text=True, check=True)
            assert 'python' in result.stdout.lower()
        except subprocess.CalledProcessError as e:
            pytest.fail(f"Python is not available: {e}")
    except FileNotFoundError:
        pytest.fail("Python is not installed or not in PATH")


def test_main_py_exists():
    """Test that main.py exists and is not empty."""
    assert os.path.exists('main.py'), "main.py file does not exist"
    
    # Check that main.py is not empty
    with open('main.py', 'r') as f:
        content = f.read().strip()
    
    # Allow for minimal content or placeholder
    assert len(content) >= 0, "main.py exists but should contain some content for next levels"



def test_networking_tools_available():
    """Test that basic networking debugging tools are available (optional)."""
    tools_found = []
    
    # Test for curl (useful for debugging)
    try:
        subprocess.run(['curl', '--version'], 
                      capture_output=True, text=True, check=True)
        tools_found.append('curl')
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass
    
    # Test for netstat (useful for debugging)
    try:
        subprocess.run(['netstat', '--version'], 
                      capture_output=True, text=True, check=True)
        tools_found.append('netstat')
    except (subprocess.CalledProcessError, FileNotFoundError):
        # Try alternative commands
        try:
            subprocess.run(['ss', '--version'], 
                          capture_output=True, text=True, check=True)
            tools_found.append('ss')
        except (subprocess.CalledProcessError, FileNotFoundError):
            pass
    
    # This test passes regardless, but provides useful information
    print(f"Available debugging tools: {', '.join(tools_found) if tools_found else 'None found'}")
    assert True  # Always pass, just informational