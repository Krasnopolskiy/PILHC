import logging
import random
import socket
import threading
import time

import config

logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format=config.LOG_FORMAT,
    datefmt=config.LOG_DATE_FORMAT,
)
logger = logging.getLogger("Filter 1")


def setup_server() -> socket.socket:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((config.FILTER_HOST, config.FILTER_PORT))
    sock.listen(5)
    logger.info("Start filter server on %s:%s", config.FILTER_HOST, config.FILTER_PORT)
    return sock


def generate_dummy_packet() -> bytes:
    length = random.randint(config.MIN_PACKET_LENGTH, config.MAX_PACKET_LENGTH)
    packet = "".join(random.choices(config.PACKET_CHARS, k=length))
    return packet.encode()


def forward_packets(producer: socket.socket, consumer: socket.socket):
    while True:
        data = producer.recv(1024)
        if not data:
            break

        logger.info("Forwarding data from proxy: %r", data)

        consumer.sendall(data)


def inject_packets(consumer: socket.socket):
    while True:
        packet = generate_dummy_packet()
        logger.info("Injecting %s packet", packet)

        consumer.sendall(packet)

        time.sleep(config.MAX_DELAY)


def handle_connection(producer: socket.socket):
    consumer = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        consumer.connect((config.CONSUMER_HOST, config.CONSUMER_PORT))

        receiver = threading.Thread(target=forward_packets, args=(producer, consumer), daemon=True)
        injector = threading.Thread(target=inject_packets, args=(consumer,), daemon=True)

        receiver.start()
        injector.start()

        receiver.join()
        injector.join()

    except KeyboardInterrupt:
        logger.info("Connection handler stopped by user")
    except Exception as e:
        logger.error("Error handling connection: %r", e)
    finally:
        producer.close()
        consumer.close()


def start_proxy():
    sock = setup_server()

    try:
        while True:
            producer, addr = sock.accept()
            logger.info("Connection from %r", addr)
            threading.Thread(target=handle_connection, args=(producer,), daemon=True).start()

    except KeyboardInterrupt:
        logger.info("Proxy stopped by user")
    except Exception as e:
        logger.error("Server error: %r", e)
    finally:
        if sock:
            sock.close()


def main():
    start_proxy()


if __name__ == "__main__":
    main()
