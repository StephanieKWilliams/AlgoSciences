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
    # Create a ConfigParser object
    config = configparser.ConfigParser()
    config.read(config_file)
    
    # Access the 'settings' section and retrieve values
    try:
        linuxpath = config.get('settings', 'linuxpath')
        reread_on_query = config.get('settings', 'REREAD_ON_QUERY').lower() 
        ssl_enabled = config.get('settings', 'SSL_ENABLED').lower() 
        ssl_certfile = config.get('settings', 'SSL_CERTFILE')
        ssl_keyfile = config.get('settings', 'SSL_KEYFILE')
    except KeyError as e:
        raise KeyError(f"{e.args[0]} is missing from configuration")

    return linuxpath, reread_on_query, ssl_enabled, ssl_certfile, ssl_keyfile
 
# Load search strings from the linux path file
def load_search_strings(linuxpath: str) -> List[str]:
    try:
        with open(linuxpath, 'r') as file:
            return [line.strip() for line in file.readlines()]
    except Exception as e:
        logging.error(f"Error loading search strings from {linuxpath}: {e}")
        return []

def binary_search(filepath: str, search_strings: List[str], reread: bool) -> str:
    start_time = time.time()
    if not reread:
        if not hasattr(binary_search, 'cached_lines'):
            with open(filepath, 'r') as file:
                binary_search.cached_lines = [line.strip() for line in file.readlines()]
        lines = binary_search.cached_lines
    else:
        with open(filepath, 'r') as file:
            lines = [line.strip() for line in file.readlines()]
    
    lines.sort()
    for search_string in search_strings:
        index = bisect.bisect_left(lines, search_string)
        if index < len(lines) and lines[index] == search_string:
            execution_time = time.time() - start_time
            logging.debug(f"DEBUG: Found string in file. Time: {execution_time:.4f} seconds")
            return "STRING EXISTS\n"
    
    execution_time = time.time() - start_time
    logging.debug(f"DEBUG: No strings found in file. Time: {execution_time:.4f} seconds")
    return "STRING NOT FOUND\n"

# # Handle client connection
def handle_client(client_socket: socket.socket, config: dict) -> None:
    try:
        request = client_socket.recv(1024).decode('utf-8').strip('\x00')
        if not request:
            logging.warning(f"Invalid request from {client_socket.getpeername()}")
            client_socket.send("STRING NOT FOUND\n".encode('utf-8'))
            return
        logging.debug(f"DEBUG: Client {client_socket.getpeername()} requested '{request}'")
        search_strings = load_search_strings(config['linuxpath'])
        response =binary_search(config['linuxpath'], search_strings  , config['REREAD_ON_QUERY'])
        client_socket.send(response.encode('utf-8'))
    except Exception as e:
        logging.error(f"Error handling client {client_socket.getpeername()}: {e}")
        client_socket.send("ERROR\n".encode('utf-8'))
    client_socket.close()

# Main server function
def start_server(host: str, port: int, config_file: str):
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
    start_server('0.0.0.0', 56749, 'config.ini')
