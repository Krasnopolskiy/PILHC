import logging
import random
import socket
import time

import config

logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format=config.LOG_FORMAT,
    datefmt=config.LOG_DATE_FORMAT,
)
logger = logging.getLogger("Producer")


def setup_connection() -> socket.socket:
    proxy = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    proxy.connect((config.PROXY_HOST, config.PROXY_PORT))
    logger.info("Connected to proxy server")
    return proxy


def generate_packet() -> bytes:
    length = random.randint(config.MIN_PACKET_LENGTH, config.MAX_PACKET_LENGTH)
    packet = "".join(random.choices(config.PACKET_CHARS, k=length))
    return packet.encode()


def send_packet(proxy: socket.socket, packet: bytes):
    try:
        proxy.send(packet)
        logger.info("Sent packet: %r", packet)
    except Exception as e:
        logger.error("Error sending packet: %r", e)


def calculate_delay() -> float:
    if random.random() < 0.5:
        return random.uniform(config.MIN_DELAY, config.MIN_DELAY + 0.5)
    else:
        return random.uniform(config.MAX_DELAY - 0.5, config.MAX_DELAY)


def send_packet_with_delay(proxy: socket.socket):
    packet = generate_packet()
    send_packet(proxy, packet)

    delay = calculate_delay()
    logger.info(f"Waiting for {delay:.3f}s before next packet")
    time.sleep(delay)


def start_producer():
    proxy = None
    try:
        proxy = setup_connection()
        while True:
            send_packet_with_delay(proxy)
    except KeyboardInterrupt:
        logger.info("Producer stopped by user")
    finally:
        if proxy:
            proxy.close()


def main():
    start_producer()


if __name__ == "__main__":
    main()
