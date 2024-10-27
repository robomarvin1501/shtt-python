import socket
import ssl

PUBLISH = 0
SUBSCRIBE = 1
UNSUBSCRIBE = 2
KEEP_ALIVE = 3
DISCONNECT = 4

SIZE_VERSION = 1
SIZE_AUTHENTICATED = 1
SIZE_MESSAGE_TYPE = 1
MAX_CHANNEL_BYTES = 2
MAX_MESSAGE_BYTES = 2
MAX_USERNAME_BYTES = 2
MAX_PASSWORD_BYTES = 2

ENDIAN = "big"

PORT = 5477


class SHTTMessage:
    def __init__(self, authenticated=False, username="", password="", channel="", data="", message_type=PUBLISH):
        self.version = 1
        self.channel = channel
        self.data = data
        self.message_type = message_type
        self.authenticated = authenticated
        self.username = username
        self.password = password

    def encode(self) -> bytes:
        content: bytes = b""
        content += self.encode_base()
        if self.message_type == PUBLISH:
            content += self._encode_publish()
        elif self.message_type == SUBSCRIBE:
            content += self._encode_subscribe()
        elif self.message_type == UNSUBSCRIBE:
            content += self._encode_unsubscribe()
        elif self.message_type == KEEP_ALIVE:
            content += self._encode_keep_alive()
        elif self.message_type == DISCONNECT:
            content += self._encode_disconnect()
        return content

    def decode(self, data: bytes):
        channel_length_start = self.decode_base(data)
        if channel_length_start == -1:
            return
        channel_start = channel_length_start + MAX_CHANNEL_BYTES

        self.channel = ""
        self.data = ""

        if self.message_type == PUBLISH:
            channel_length = int.from_bytes(data[channel_length_start:channel_length_start + MAX_CHANNEL_BYTES], ENDIAN)
            self.channel = data[channel_start:channel_start +
                                              channel_length].decode()
            message_length_start = channel_start + channel_length
            message_length = int.from_bytes(
                data[message_length_start:message_length_start + MAX_MESSAGE_BYTES], ENDIAN)
            message_start = message_length_start + MAX_MESSAGE_BYTES
            self.data = data[message_start: message_start + message_length].decode()

        elif self.message_type == SUBSCRIBE:
            channel_length = int.from_bytes(data[channel_length_start:channel_length_start + MAX_CHANNEL_BYTES], ENDIAN)
            self.channel = data[channel_start:channel_start +
                                              channel_length].decode()

            port_length_start = channel_start + channel_length
            port_length = int.from_bytes(
                data[port_length_start:port_length_start + MAX_MESSAGE_BYTES], ENDIAN)
            port_start = port_length_start + MAX_MESSAGE_BYTES
            self.data = data[port_start: port_start + port_length].decode()

        elif self.message_type == UNSUBSCRIBE:
            channel_length = int.from_bytes(data[channel_length_start:channel_length_start + MAX_CHANNEL_BYTES], ENDIAN)
            self.channel = data[channel_start:channel_start +
                                              channel_length].decode()
        elif self.message_type == KEEP_ALIVE:
            self.message_type = KEEP_ALIVE
        elif self.message_type == DISCONNECT:
            self.message_type = DISCONNECT

    def __repr__(self):
        return f"version: {self.version}, message_type: {self.message_type}, channel: {self.channel}, data: {self.data}"

    def encode_base(self):
        return (
                self.version.to_bytes(SIZE_VERSION, ENDIAN)
                + self.authenticated.to_bytes(SIZE_AUTHENTICATED, ENDIAN)
                + len(self.username).to_bytes(MAX_USERNAME_BYTES, ENDIAN)
                + self.username.encode()
                + len(self.password).to_bytes(MAX_PASSWORD_BYTES, ENDIAN)
                + self.password.encode()
        )

    def decode_base(self, data: bytes) -> int:
        version_begin = 0
        version = int.from_bytes(data[version_begin:version_begin + SIZE_VERSION], ENDIAN)
        if version != self.version:
            # TODO log invalid version
            return -1

        authenticated_begin = version_begin + SIZE_VERSION
        self.authenticated = int.from_bytes(data[authenticated_begin:authenticated_begin + SIZE_AUTHENTICATED], ENDIAN)
        # TODO don't encode user + pass lengths if not authenticated?

        username_length_begin = authenticated_begin + SIZE_AUTHENTICATED
        username_length = int.from_bytes(data[username_length_begin:username_length_begin + MAX_USERNAME_BYTES], ENDIAN)
        if username_length > 0:
            username_begin = username_length_begin + MAX_USERNAME_BYTES
            self.username = data[username_begin:username_begin + username_length].decode()
        else:
            username_begin = username_length_begin + MAX_USERNAME_BYTES
            self.username = ""

        password_length_begin = username_begin + username_length
        password_length = int.from_bytes(data[password_length_begin:password_length_begin + MAX_PASSWORD_BYTES])
        if password_length > 0:
            password_begin = password_length_begin + MAX_PASSWORD_BYTES
            self.password = data[password_begin:password_begin + password_length].decode()
        else:
            password_begin = password_length_begin + MAX_PASSWORD_BYTES
            self.password = ""

        message_type_begin = password_begin + password_length
        self.message_type = int.from_bytes(data[message_type_begin:message_type_begin + SIZE_MESSAGE_TYPE], ENDIAN)
        return message_type_begin + SIZE_MESSAGE_TYPE

    def _encode_publish(self) -> bytes:
        return (
                PUBLISH.to_bytes(SIZE_MESSAGE_TYPE, ENDIAN)
                + len(self.channel).to_bytes(MAX_CHANNEL_BYTES, ENDIAN)
                + self.channel.encode()
                + len(self.data).to_bytes(MAX_MESSAGE_BYTES, ENDIAN)
                + self.data.encode()
        )

    def _encode_subscribe(self):
        return (
                SUBSCRIBE.to_bytes(SIZE_MESSAGE_TYPE, ENDIAN)
                + len(self.channel).to_bytes(MAX_CHANNEL_BYTES, ENDIAN)
                + self.channel.encode()
                + (5).to_bytes(MAX_MESSAGE_BYTES, ENDIAN)
                + self.data.encode()
        )

    def _encode_unsubscribe(self):
        return (
                UNSUBSCRIBE.to_bytes(SIZE_MESSAGE_TYPE, ENDIAN)
                + len(self.channel).to_bytes(MAX_CHANNEL_BYTES, ENDIAN)
                + self.channel.encode()
        )

    def _encode_keep_alive(self):
        return (
            KEEP_ALIVE.to_bytes(SIZE_MESSAGE_TYPE, ENDIAN)
        )

    def _encode_disconnect(self):
        return (
            DISCONNECT.to_bytes(SIZE_MESSAGE_TYPE, ENDIAN)
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
