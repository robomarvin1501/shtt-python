import socket
import ssl

PUBLISH = 0
SUBSCRIBE = 1
UNSUBSCRIBE = 2
KEEP_ALIVE = 3
DISCONNECT = 4


SIZE_VERSION = 1
SIZE_MESSAGE_TYPE = 1
MAX_CHANNEL_BYTES = 2
MAX_MESSAGE_BYTES = 2

ENDIAN = "big"

PORT = 5477


class SHTTMessage:
    def __init__(self, channel="", data="", message_type=PUBLISH):
        self.version = 1
        self.channel = channel
        self.data = data
        self.message_type = message_type

    def encode(self) -> bytes:
        content: bytes = b""
        if self.message_type == PUBLISH:
            content = self._encode_publish()
        elif self.message_type == SUBSCRIBE:
            content = self._encode_subscribe()
        elif self.message_type == UNSUBSCRIBE:
            content = self._encode_unsubscribe()
        elif self.message_type == KEEP_ALIVE:
            content = self._encode_keep_alive()
        elif self.message_type == DISCONNECT:
            content = self._encode_disconnect()
        return content

    def decode(self, data: bytes):
        version = int.from_bytes(data[0:1], ENDIAN)
        if version != self.version:
            # TODO log invalid version
            return

        self.message_type = int.from_bytes(data[1:2], ENDIAN)
        self.channel = ""
        self.data = ""

        if self.message_type == PUBLISH:
            channel_length = int.from_bytes(data[2:4], ENDIAN)
            channel_start = 4
            self.channel = data[channel_start:channel_start +
                                channel_length].decode()
            message_length_start = channel_start + channel_length
            message_length = int.from_bytes(
                data[message_length_start:message_length_start + 2], ENDIAN)
            self.data = data[message_length_start +
                             2: message_length_start
                             + 2 + message_length].decode()

        elif self.message_type == SUBSCRIBE:
            channel_length = int.from_bytes(data[2:4], ENDIAN)
            channel_start = 4
            self.channel = data[channel_start:channel_start +
                                channel_length].decode()
        elif self.message_type == UNSUBSCRIBE:
            channel_length = int.from_bytes(data[2:4], ENDIAN)
            channel_start = 4
            self.channel = data[channel_start:channel_start +
                                channel_length].decode()
        elif self.message_type == KEEP_ALIVE:
            self.message_type = KEEP_ALIVE
        elif self.message_type == DISCONNECT:
            self.message_type = DISCONNECT

    def __repr__(self):
        return f"version: {self.version}, message_type: {self.message_type}, channel: {self.channel}, data: {self.data}"

    def _encode_publish(self) -> bytes:
        return (
            self.version.to_bytes(SIZE_VERSION, ENDIAN)
            + PUBLISH.to_bytes(SIZE_MESSAGE_TYPE, ENDIAN)
            + len(self.channel).to_bytes(MAX_CHANNEL_BYTES, ENDIAN)
            + self.channel.encode()
            + len(self.data).to_bytes(MAX_MESSAGE_BYTES, ENDIAN)
            + self.data.encode()
        )

    def _encode_subscribe(self):
        return (
            self.version.to_bytes(SIZE_VERSION, ENDIAN)
            + SUBSCRIBE.to_bytes(SIZE_MESSAGE_TYPE, ENDIAN)
            + len(self.channel).to_bytes(MAX_CHANNEL_BYTES, ENDIAN)
            + self.channel.encode()
        )

    def _encode_unsubscribe(self):
        return (
            self.version.to_bytes(SIZE_VERSION, ENDIAN)
            + UNSUBSCRIBE.to_bytes(SIZE_MESSAGE_TYPE, ENDIAN)
            + len(self.channel).to_bytes(MAX_CHANNEL_BYTES, ENDIAN)
            + self.channel.encode()
        )

    def _encode_keep_alive(self):
        return (
            self.version.to_bytes(SIZE_VERSION, ENDIAN)
            + KEEP_ALIVE.to_bytes(SIZE_MESSAGE_TYPE, ENDIAN)
        )

    def _encode_disconnect(self):
        return (
            self.version.to_bytes(SIZE_VERSION, ENDIAN)
            + DISCONNECT.to_bytes(SIZE_MESSAGE_TYPE, ENDIAN)
        )


def create_tls_context():
    """Create a TLS context for secure connection."""
    context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
    # Disable hostname and certificate verification for testing.
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE
    return context


def send_message(message: bytes, use_tls, addr=("localhost", 5477)):
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.settimeout(1)

    if use_tls:
        context = create_tls_context()
        sock = context.wrap_socket(client, server_hostname=addr[0])
    else:
        sock = client

    try:
        sock.connect(addr)
        sock.sendall(message)
        # TODO logging
        # print(f"Sent message to {addr} at {time.time()}")

        # response = sock.recv(4096)
        # TODO logging
        # print(f"Received response: {response.decode()}")

    finally:
        sock.close()
