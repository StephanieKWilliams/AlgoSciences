import socket
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(message)s')

def start_client(host: str, port: int, request: str):
    try:
       
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((host, port))
        logging.debug(f"Sending request: {request}")
        client_socket.send(request.encode('utf-8'))
        response = client_socket.recv(1024).decode('utf-8')
        logging.debug(f"Received response: {response}")
        client_socket.close()
        return response
    except Exception as e:
        logging.error(f"Error connecting to the server: {e}")
        return "ERROR"
        
if __name__ == "__main__":
    host = "localhost"
    port = 56747
    request = "SEARCH QUERY "  
    response = start_client(host, port, request)
    print(f"Response from server: {response}")
