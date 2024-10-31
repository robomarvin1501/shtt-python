import SHTT

import argparse

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="SHTT client with optional TLS. Note that if the broker "
                    "uses TLS, so too must the client.")
    parser.add_argument("host", type=str,
                        help="Hostname or IP address to connect to")
    parser.add_argument("channel", type=str,
                        help="channel on which to send the message")
    parser.add_argument("message", type=str,
                        help="message to send")
    parser.add_argument("--username", type=str, default="",
                        help="username")
    parser.add_argument("--password", type=str, default="",
                        help="password")
    parser.add_argument("--port", type=int, default=5477,
                        help="Port number (default: 5477)")
    parser.add_argument("--tls", action="store_true",
                        help="Enable TLS (default: True)")

    args = parser.parse_args()
    print(args)

    shtt_message = SHTT.SHTTMessage()
    shtt_message.channel = args.channel
    shtt_message.data = args.message
    shtt_message.message_type = SHTT.PUBLISH
    shtt_message.username = args.username
    shtt_message.password = args.password

    SHTT.send_message(shtt_message.encode(), args.tls, (args.host, args.port))
