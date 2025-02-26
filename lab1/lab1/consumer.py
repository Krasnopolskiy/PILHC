import argparse
import logging
import socket
import threading
import time

import config

logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format=config.LOG_FORMAT,
    datefmt=config.LOG_DATE_FORMAT,
)
logger = logging.getLogger("Consumer")


def setup_server() -> socket.socket:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((config.CONSUMER_HOST, config.CONSUMER_PORT))
    sock.listen(5)
    logger.info("Consumer listening on %s:%s", config.CONSUMER_HOST, config.CONSUMER_PORT)
    return sock


def decode_timing(current_time: float, last_packet_time: float | None) -> tuple[int | None, float]:
    if last_packet_time is None:
        return None, current_time

    delay = current_time - last_packet_time
    bit = 1 if delay >= config.BIT_THRESHOLD else 0
    logger.info("Decoded bit: %d (delay: %.3fs)", bit, delay)
    return bit, current_time


def process_byte(received_bits: list[int], bit_count: int, output_file: str):
    start_index = bit_count - 8
    byte_bits = received_bits[start_index:bit_count]
    byte_value = 0

    for bit in byte_bits:
        byte_value = (byte_value << 1) | bit

    logger.info(
        "Decoded byte: %02X (ASCII: %s)",
        byte_value,
        chr(byte_value) if 32 <= byte_value <= 126 else "?",
    )

    with open(output_file, "ab") as f:
        f.write(bytes([byte_value]))


def process_bit(bit: int | None, received_bits: list[int], output_file: str) -> list[int]:
    if bit is None:
        return received_bits

    received_bits.append(bit)
    bit_count = len(received_bits)

    if bit_count % 8 == 0:
        process_byte(received_bits, bit_count, output_file)

    return received_bits


def display_binary_sequence(received_bits: list[int]):
    if not received_bits:
        return

    bits_str = "".join(map(str, received_bits))
    logger.info("Received bit sequence: %s", bits_str)


def process_received_data(
    data: bytes, last_packet_time: float | None, received_bits: list[int], output_file: str
) -> tuple[float, list[int]]:
    current_time = time.time()
    bit, new_last_packet_time = decode_timing(current_time, last_packet_time)
    new_received_bits = process_bit(bit, received_bits, output_file)
    logger.info("Received data: %r", data)
    return new_last_packet_time, new_received_bits


def handle_connection(conn: socket.socket, output_file: str):
    received_bits = []
    last_packet_time = None

    try:
        while True:
            data = conn.recv(1024)
            if not data:
                break
            last_packet_time, received_bits = process_received_data(data, last_packet_time, received_bits, output_file)
    except KeyboardInterrupt:
        logger.info("Connection handler stopped by user")
    finally:
        conn.close()
        display_binary_sequence(received_bits)


def start_consumer(output_file: str):
    sock = setup_server()

    try:
        while True:
            conn, addr = sock.accept()
            threading.Thread(target=handle_connection, args=(conn, output_file), daemon=True).start()

    except KeyboardInterrupt:
        logger.info("Consumer stopped by user")
    finally:
        if sock:
            sock.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-file", help="File to save decoded secret message")

    args = parser.parse_args()

    start_consumer(args.output_file)


if __name__ == "__main__":
    main()
