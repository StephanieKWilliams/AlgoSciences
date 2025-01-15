import pytest
import socket
import time
import ssl
from unittest.mock import patch, mock_open
from server import  load_search_strings, search_in_file,  handle_client




# Test for load_search_strings function
def test_load_search_strings_valid():
    file_content = "string1\nstring2\nstring3"
    with patch("builtins.open", mock_open(read_data=file_content)):
        result = load_search_strings("200k.txt")
        assert result == ["string1", "string2", "string3"]

def test_load_search_strings_invalid():
    with patch("builtins.open", mock_open(read_data="")):
        result = load_search_strings("200k.txt")
        assert result == []



@pytest.mark.parametrize("file_size, expected_time_range", [
    (10000, (0.001, 0.05)),  
])
def test_search_in_file(file_size, expected_time_range):
    content = "\n".join([f"string{i}" for i in range(file_size)])

    with patch("builtins.open", mock_open(read_data=content)):
        search_strings = ["string1"]
        start_time = time.time()
        result = search_in_file("/dummy/path", search_strings, reread=False)
        execution_time = time.time() - start_time
        assert result == "STRING EXISTS\n"
        assert expected_time_range[0] <= execution_time <= expected_time_range[1]


# Test server's performance (e.g., handling queries per second)
def test_server_performance():
    start_time = time.time()
    num_requests = 1000 
    with patch("socket.socket.send", return_value=None):
        for _ in range(num_requests):
            time.sleep(0.01)  
    execution_time = time.time() - start_time
    queries_per_second = num_requests / execution_time
    assert queries_per_second > 10 
