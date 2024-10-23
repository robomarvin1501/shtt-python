import SHTT

import argparse
import socket
import threading
import queue
import time


def keep_alive(shutdown: queue.Queue, use_tls, addr, reminder=10):
    while True:
        message = SHTT.SHTTMessage()
        message.message_type = SHTT.KEEP_ALIVE

        SHTT.send_message(message.encode(), use_tls, addr)
        if shutdown.qsize() > 0:
            break
        time.sleep(reminder)


def subscriber(use_tls, channel, broker_addr=("localhost", SHTT.PORT), subscriber_addr=("localhost", SHTT.PORT)):
    subscription_message = SHTT.SHTTMessage()
    subscription_message.channel = channel
    subscription_message.message_type = SHTT.SUBSCRIBE
    SHTT.send_message(subscription_message.encode(), use_tls, broker_addr)

    shutdown = queue.Queue()

    thread_keep_alive = threading.Thread(
        target=keep_alive, args=(shutdown, use_tls, broker_addr))
    thread_keep_alive.start()

    local_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    local_server.bind(subscriber_addr)
    local_server.listen(5)

    context = SHTT.create_tls_context() if use_tls else None
    shtt_message = SHTT.SHTTMessage()

    # TODO logging
    # print(f"Server listening on {addr} (TLS={'ON' if use_tls else 'OFF'})")

    try:
        sock = None
        while True:
            server_sock, server_addr = local_server.accept()
            # TODO logging
            # print(f"Connection from {client_addr}")

            if use_tls:
                sock = context.wrap_socket(server_sock, local_server_side=True)
            else:
                sock = server_sock

            try:
                data = sock.recv(4096)
                shtt_message.decode(data)
                print(shtt_message)
            finally:
                sock.close()
    except KeyboardInterrupt:
        shutdown.put("Shutdown")
        if sock:
            sock.close()
        disconnect = SHTT.SHTTMessage()
        disconnect.message_type = SHTT.DISCONNECT
        SHTT.send_message(disconnect.encode(), use_tls, broker_addr)
        return


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="SHTT client with optional TLS. Note that if the broker "
        "uses TLS, so too must the client.")
    parser.add_argument("broker", type=str,
                        help="Hostname or IP address of the broker")
    parser.add_argument("channel", type=str,
                        help="channel to which to subscribe")
    parser.add_argument("subscriber", type=str,
                        help="subscriber hostname")
    parser.add_argument("--subscriber_port", type=int,
                        help="subscriber port", default=5478)
    parser.add_argument("--port", type=int, default=5477,
                        help="Port number (default: 5477)")
    parser.add_argument("--tls", action="store_true",
                        help="Enable TLS (default: False)")

    args = parser.parse_args()
    print(args)

    subscriber(args.tls, args.channel, (args.broker, args.port),
               (args.subscriber, args.subscriber_port))
