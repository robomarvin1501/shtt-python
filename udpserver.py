import socket
import time

server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server.bind(("localhost", 5000))

while True:
    message, addr = server.recvfrom(1024)
    print(f"Received: {message} from {addr} at {time.time()}")

    server.sendto(message, addr)
