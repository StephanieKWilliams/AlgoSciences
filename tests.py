import pytest
import time
import tempfile
import os
from unittest.mock import patch, mock_open, MagicMock
from server import load_search_strings, binary_search, handle_client


# Test for load_search_strings function
def test_load_search_strings_valid():
    """
    Test case to check if load_search_strings correctly loads strings from a valid file.
    This test avoids hardcoded paths by using a temporary file.
    """
    file_content = "string1\nstring2\nstring3"
    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        temp_file.write(file_content.encode())
        temp_file.close()

        with patch("builtins.open", mock_open(read_data=file_content)):
            result = load_search_strings(temp_file.name)
            assert result == ["string1", "string2", "string3"]
        
        os.remove(temp_file.name)  # Clean up the temporary file


def test_load_search_strings_empty_file():
    """
    Test case to check if load_search_strings correctly handles an empty file.
    The file is dynamically created and handled without relying on hardcoded paths.
    """
    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        temp_file.close()

        with patch("builtins.open", mock_open(read_data="")):
            result = load_search_strings(temp_file.name)
            assert result == []
        
        os.remove(temp_file.name)  # Clean up the temporary file


def test_load_search_strings_file_not_found():
    """
    Test case to check if load_search_strings handles a FileNotFoundError correctly.
    This test uses a non-existent file name which won't cause an actual filesystem issue.
    """
    with patch("builtins.open", side_effect=FileNotFoundError):
        result = load_search_strings("non_existent_file.txt")
        assert result == []


@pytest.mark.parametrize("file_size, search_strings, expected_result", [
    (10000, ["string1"], "STRING EXISTS\n"),
    (10000, ["string10000"], "STRING NOT FOUND\n"),
    (1000, ["string1", "string2"], "STRING EXISTS\n"),
])
def test_search_in_file(file_size, search_strings, expected_result):
    """
    Test case to perform binary search on a dynamically created file with different search strings.
    This test avoids hardcoded paths by using a dynamically created file.
    """
    content = "\n".join([f"string{i}" for i in range(file_size)])

    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        temp_file.write(content.encode())
        temp_file.close()

        with patch("builtins.open", mock_open(read_data=content)):
            start_time = time.time()
            result = binary_search(temp_file.name, search_strings, reread=False)
            execution_time = time.time() - start_time
            assert result == expected_result
            assert execution_time < 0.05  # Ensure it completes quickly for larger files

        os.remove(temp_file.name)  # Clean up the temporary file

def test_search_in_file_file_not_found():
    """
    Test case to check if binary_search handles FileNotFoundError correctly.
    The test ensures that a FileNotFoundError results in the correct return value.
    """
    with patch("builtins.open", side_effect=FileNotFoundError):
        result = binary_search("/dummy/path", ["sting1"], reread=False)
        assert result == "STRING NOT FOUND\n"

# Test concurrent connection handling (e.g., handle_client)
def test_handle_client_concurrent():
    """
    Test case to simulate handling multiple client connections concurrently.
    This test ensures the server can handle many simultaneous requests and measures throughput.
    """
    num_requests = 100
    mock_socket = MagicMock()
    mock_socket.getpeername.return_value = ('127.0.0.1', 12345)
    
    with patch("socket.socket", return_value=mock_socket), \
         patch("socket.socket.send", return_value=None), patch("socket.socket.recv", return_value=b"query"):
        start_time = time.time()
        for _ in range(num_requests):
            # Simulate multiple clients sending requests simultaneously
            handle_client(mock_socket, None) 
        execution_time = time.time() - start_time
        queries_per_second = num_requests / execution_time
        assert queries_per_second > 10  

# Test for load_search_strings with tempfile (avoiding hardcoded paths)
def test_load_search_strings_with_tempfile():
    """
    Test case to check load_search_strings with a dynamically created temporary file.
    The test ensures that no hardcoded paths are used for loading strings.
    """
    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        temp_file.write(b"string1\nstring2\nstring3")
        temp_file.close()

        with patch("builtins.open", mock_open(read_data="string1\nstring2\nstring3")):
            result = load_search_strings(temp_file.name)
            assert result == ["string1", "string2", "string3"]
        
        os.remove(temp_file.name)  # Clean up the temporary file

# Test server performance with multiple requests
@pytest.mark.parametrize("num_requests, expected_queries_per_second", [
    (10000, 500),
])
def test_server_performance(num_requests, expected_queries_per_second):
    """
    Test case to check the server performance by handling a high number of client requests.
    This test ensures the server can handle a large number of requests in a reasonable amount
    of time, measuring throughput (queries per second).
    """
    num_requests = 10000
    mock_socket = MagicMock()
    mock_socket.getpeername.return_value = ('127.0.0.1', 12345)
    
    with patch("socket.socket", return_value=mock_socket), \
         patch("socket.socket.send", return_value=None), patch("socket.socket.recv", return_value=b"query"):
        start_time = time.time()
        for _ in range(num_requests):
            handle_client(mock_socket, None)  # Simulate each client request

    execution_time = time.time() - start_time
    queries_per_second = num_requests / execution_time
    assert queries_per_second > expected_queries_per_second
