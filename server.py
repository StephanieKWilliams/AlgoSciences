import socket
import threading
import time
import logging
import ssl
from typing import List, Tuple
import configparser
import bisect
import os
import sys

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(message)s')

def start_daemon():
    """
    Start the server as a daemon process, detaching from the terminal and running in the background.
    """
    pid = os.fork()
    if pid > 0:  
        sys.exit()
    os.setsid()  
    sys.stdout = open("/var/log/algosciences.log", "a")
    sys.stderr = sys.stdout

# Load configuration
def load_config(config_file: str) -> Tuple[str, bool, bool, str, str]:
    """
    Load the configuration from the provided file.

    Args:
        config_file (str): Path to the configuration file.

    Returns:
        Tuple containing the Linux path, reread flag, SSL enabled flag, SSL cert file, and SSL key file paths.
    
    Raises:
        KeyError: If any required configuration keys are missing.
    """

    config = configparser.ConfigParser()
    config.read(config_file)
    
    try:
        linuxpath = config.get('settings', 'linuxpath')
        reread_on_query = config.get('settings', 'REREAD_ON_QUERY') .lower()
        ssl_enabled = config.get('settings', 'SSL_ENABLED') .lower()
        ssl_certfile = config.get('settings', 'SSL_CERTFILE')
        ssl_keyfile = config.get('settings', 'SSL_KEYFILE')
    except KeyError as e:
        raise KeyError(f"{e.args[0]} is missing from configuration")

    return linuxpath, reread_on_query, ssl_enabled, ssl_certfile, ssl_keyfile
 

def load_search_strings(linuxpath: str) -> List[str]:

    """
    Load the search strings from the specified file.

    Args:
        linuxpath (str): Path to the file containing search strings.

    Returns:
        List[str]: A list of search strings.
    """
    try:
        with open(linuxpath, 'r') as file:
            return [line.strip() for line in file.readlines()]
    except Exception as e:
        logging.error(f"Error loading search strings from {linuxpath}: {e}")
        return []

def binary_search(filepath: str, search_strings: List[str], reread: bool) -> str:
    """
    Perform a binary search on the file to check for the presence of search strings.

    Args:
        filepath (str): Path to the file to search.
        search_strings (List[str]): List of search strings to find.
        reread (bool): Whether to reread the file for each search.

    Returns:
        str: "STRING EXISTS" if any string is found, else "STRING NOT FOUND".
    """
    start_time = time.time()
    lines = []
    try:
        
        # If reread is True, we bypass the cache and read the file again
        if reread == 'true':
            logging.debug(f'rereading the file again {reread}')
            with open(filepath, 'r') as file:
                lines = [line.strip() for line in file.readlines()]
            lines.sort()
        else:
            logging.debug(f'reading from cache {reread}')
            if not hasattr(binary_search, 'cached_lines'):
                with open(filepath, 'r') as file:
                    binary_search.cached_lines = [line.strip() for line in file.readlines()]
            lines = binary_search.cached_lines

        search_strings.sort()
        for search_string in search_strings:
            index = bisect.bisect_left(lines, search_string)
            
            if index < len(lines) and lines[index] == search_string:
                execution_time = time.time() - start_time
                logging.debug(f"Found exact match: {search_string},Execution time: {execution_time:.4f} seconds")
                return "STRING EXISTS\n"

    except FileNotFoundError:
        # If the file is not found, return "STRING NOT FOUND"
        execution_time = time.time() - start_time
        logging.debug(f"STRING NOT FOUND: Execution time: {execution_time:.4f} seconds")
        return "STRING NOT FOUND\n"
    return "STRING NOT FOUND\n"
def handle_client(client_socket: socket.socket, config: dict) -> None:
    """
    Handle the incoming client connection, perform the search, and send a response.

    Args:
        client_socket (socket.socket): The socket object representing the client connection.
        config (dict): Configuration values such as linuxpath and reread flag.
    """
    try:
        request = client_socket.recv(1024).decode('utf-8').strip('\x00')
        if not request:
            logging.warning(f"Invalid request from {client_socket.getpeername()}")
            client_socket.send("STRING NOT FOUND\n".encode('utf-8'))
            return
        logging.debug(f"DEBUG: Client {client_socket.getpeername()} requested '{request}'")
        search_strings = load_search_strings(config['linuxpath'])
        response =binary_search(config['linuxpath'], search_strings  , config['REREAD_ON_QUERY'])
        # Ensure response is not None before sending
        if response:
            client_socket.send(response.encode('utf-8'))
        else:
            logging.warning("Response was None, sending default message")
            client_socket.send("STRING NOT FOUND\n".encode('utf-8'))
    except Exception as e:
        logging.error(f"Error handling client {client_socket.getpeername()}: {e}")
        client_socket.send("ERROR\n".encode('utf-8'))
    client_socket.close()

def start_server(host: str, port: int, config_file: str):
    """
    Start the server and listen for incoming connections.

    Args:
        host (str): Host to bind the server to (e.g., '0.0.0.0').
        port (int): Port to bind the server to.
        config_file (str): Path to the configuration file.
    """
    linuxpath, reread_on_query, ssl_enabled, ssl_certfile, ssl_keyfile = load_config(config_file)
    
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((host, port))
    server_socket.listen(5)
    logging.info(f"Server started on {host}:{port}, SSL enabled: {ssl_enabled}, REREAD_ON_QUERY: {reread_on_query}")
    
    if ssl_enabled == 'true':
        context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        try:
            context.load_cert_chain(certfile=ssl_certfile, keyfile=ssl_keyfile)
            logging.info(f"SSL certificates loaded from {ssl_certfile} and {ssl_keyfile}")
        except Exception as e:
            logging.error(f"Error loading SSL certificates: {e}")
            return
        server_socket = context.wrap_socket(server_socket, server_side=True)
        logging.info("SSL encryption enabled with client authentication: ")
    while True:
        client_socket, addr = server_socket.accept()
        logging.debug(f"DEBUG: Connection from {addr}")
        client_thread = threading.Thread(target=handle_client, args=(client_socket, {
            'linuxpath': linuxpath,
            'REREAD_ON_QUERY': reread_on_query,
            'SSL_ENABLED': ssl_enabled,
        }))
        client_thread.start()

# Run the server
if __name__ == "__main__":
    start_server('0.0.0.0', 56747, 'config.ini')
