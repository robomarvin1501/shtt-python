import SHTT

import socket
import time
import argparse

# TODO needs two different servers, one TLS enabled, one not, on different
# ports

SUBSCRIBER_LIFETIME = 30


class Subscription:
    def __init__(self):
        self.channels = set()
        self.last_alive = 0

    def add_channel(self, channel: str):
        self.channels.add(channel)
        self.keep_alive()

    def keep_alive(self):
        self.last_alive = time.time()


def server(use_tls, addr=("localhost", SHTT.PORT)):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(addr)
    server.listen(5)

    context = SHTT.create_tls_context() if use_tls else None
    shtt_message = SHTT.SHTTMessage()

    subscriptions: dict[str, Subscription] = dict()
    # t = threading.Timer(10, send_life_check, args=(subscriptions,))
    # t.start()

    # TODO logging
    # print(f"Server listening on {addr} (TLS={'ON' if use_tls else 'OFF'})")

    while True:
        client_sock, client_addr = server.accept()
        # TODO logging
        # print(f"Connection from {client_addr}")

        if use_tls:
            sock = context.wrap_socket(client_sock, server_side=True)
        else:
            sock = client_sock

        try:
            data = sock.recv(4096)
            shtt_message.decode(data)
            print(f"Received: {shtt_message}")
            if shtt_message.message_type == SHTT.PUBLISH:
                start = time.time()
                for addr in list(subscriptions.keys()):
                    if start - subscriptions[addr].last_alive > SUBSCRIBER_LIFETIME:
                        del subscriptions[addr]
                        continue
                    if shtt_message.channel in subscriptions[addr].channels:
                        SHTT.send_message(data, use_tls, (addr[0], SHTT.PORT))
            elif shtt_message.message_type == SHTT.SUBSCRIBE:
                if client_addr not in subscriptions:
                    subscriptions[client_addr] = Subscription()
                subscriptions[client_addr].add_channel(shtt_message.channel)
            elif shtt_message.message_type == SHTT.UNSUBSCRIBE:
                if client_addr in subscriptions:
                    subscriptions[client_addr].channels.remove(
                        shtt_message.channel)
            elif shtt_message.message_type == SHTT.KEEP_ALIVE:
                if client_addr in subscriptions:
                    subscriptions[client_addr].keep_alive()
            elif shtt_message.message_type == SHTT.DISCONNECT:
                if client_addr in subscriptions:
                    del subscriptions[client_addr]

            # print(f"Received: {data.decode()} at {time.time()}")
            # sock.sendall(message_received.__repr__())

        finally:
            sock.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="SHTT broker with optional TLS.")
    parser.add_argument("--tls", action="store_true",
                        help="Enable TLS encryption.")
    args = parser.parse_args()

    server(use_tls=args.tls)
