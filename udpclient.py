import socket
import time


class MSTTMessage:
    def __init__(self, version: int, channel: bytes, data: bytes):
        self.version = version
        self.channel = channel
        self.data = data

    def __repr__(self):
        return self.version.to_bytes(1) + len(self.channel).to_bytes(2) + self.channel + len(self.data).to_bytes(2) + self.data


client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
client.settimeout(1)

# data = b"this is a test"
# message = (1).to_bytes(1) + len(data).to_bytes(2) + data

mstt = MSTTMessage(1, b"sensors/kitchen", b"hello world")

addr = ("localhost", 5000)

client.sendto(mstt.__repr__(), addr)
print(f"Sent message to {addr} at {time.time()}")

# print(f"Received: {data}")
