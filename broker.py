import SHTT

import socket
import time
import argparse
import os

# TODO needs two different servers, one TLS enabled, one not, on different
# ports

SUBSCRIBER_LIFETIME = 30


class Subscription:
    def __init__(self, port=SHTT.PORT):
        self.channels = set()
        self.port: int = port
        self.last_alive = 0

    def add_channel(self, channel: str):
        self.channels.add(channel)
        self.keep_alive()

    def keep_alive(self):
        self.last_alive = time.time()


def server(tls_data: str, addr=("localhost", SHTT.PORT)):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(addr)
    server.listen(5)

    use_tls = len(tls_data) > 0
    context = SHTT.create_tls_context() if use_tls > 0 else None
    shtt_message = SHTT.SHTTMessage()

    subscriptions: dict[str, Subscription] = dict()
    # t = threading.Timer(10, send_life_check, args=(subscriptions,))
    # t.start()

    # TODO logging
    # print(f"Server listening on {addr} (TLS={'ON' if use_tls else 'OFF'})")

    while True:
        client_sock, client_addr = server.accept()
        print(client_addr)
        # TODO logging
        # print(f"Connection from {client_addr}")

        if use_tls:
            sock = context.wrap_socket(client_sock, server_side=True)
        else:
            sock = client_sock

        try:
            data = sock.recv(4096)
            shtt_message.decode(data)
            if config.username and config.password:
                if shtt_message.username != config.username or shtt_message.password != config.password:
                    continue
            print(f"Received: {shtt_message}")
            if shtt_message.message_type == SHTT.PUBLISH:
                start = time.time()
                for address in list(subscriptions.keys()):
                    if start - subscriptions[address].last_alive > SUBSCRIBER_LIFETIME:
                        del subscriptions[address]
                        continue
                    if shtt_message.channel in subscriptions[address].channels:
                        print(f"Sending {data} to {address} on {
                        shtt_message.channel}")
                        SHTT.send_message(
                            data, use_tls, (address, subscriptions[address].port))
            elif shtt_message.message_type == SHTT.SUBSCRIBE:
                if client_addr not in subscriptions:
                    subscriptions[client_addr[0]] = Subscription(
                        int(shtt_message.data))
                subscriptions[client_addr[0]].add_channel(shtt_message.channel)
            elif shtt_message.message_type == SHTT.UNSUBSCRIBE:
                if client_addr in subscriptions:
                    subscriptions[client_addr[0]].channels.remove(
                        shtt_message.channel)
            elif shtt_message.message_type == SHTT.KEEP_ALIVE:
                if client_addr in subscriptions:
                    subscriptions[client_addr[0]].keep_alive()
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
    parser.add_argument("--config", type=str, help="Path to the config file.")
    args = parser.parse_args()

    if os.path.exists(args.config):
        try:
            import config

            if not os.path.exists(config.tls_path):
                tls = False
                tls_data = ""
            else:
                with open(config.tls_path, "r") as f:
                    tls_data = f.read()
                tls = True
                # TODO load TLS file
        except:
            tls = False
            tls_data = ""

    server(tls_data)
