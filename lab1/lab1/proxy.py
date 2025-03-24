import argparse
import logging
import queue
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
logger = logging.getLogger("Proxy")


def read_secret_bits(filename: str) -> list[int]:
    try:
        with open(filename, "rb") as f:
            data = f.read()

        bits = []
        for byte in data:
            for i in range(7, -1, -1):
                bits.append((byte >> i) & 1)

        logger.info("Read %d secret bits from %s: %r", len(bits), filename, bits)
        return bits
    except Exception as e:
        logger.error("Error reading secret file: %r", e)
        return [0, 1]


def setup_server() -> socket.socket:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((config.PROXY_HOST, config.PROXY_PORT))
    sock.listen(5)
    logger.info("Start proxy server on %s:%s", config.PROXY_HOST, config.PROXY_PORT)
    return sock


def get_next_secret_bit(secret_bits: list[int], current_index: int) -> tuple[int, int]:
    if current_index >= len(secret_bits):
        current_index = 0

    bit = secret_bits[current_index]
    return bit, current_index + 1


def generate_dummy_packet() -> bytes:
    length = random.randint(config.MIN_PACKET_LENGTH, config.MAX_PACKET_LENGTH)
    packet = "".join(random.choices(config.PACKET_CHARS, k=length))
    return packet.encode()


def receive_packets(producer: socket.socket, packet_queue: queue.Queue):
    try:
        while True:
            data = producer.recv(1024)
            if not data:
                break

            logger.info("Received data from producer: %r", data)

            try:
                packet_queue.put(data, timeout=1.0)
            except queue.Full:
                logger.warning("Packet buffer full, dropping packet")
    except KeyboardInterrupt:
        logger.info("Packet receiver stopped by user")
    except Exception as e:
        logger.error("Error receiving data: %r", e)


def get_packet_from_queue_or_dummy(packet_queue: queue.Queue) -> bytes:
    try:
        return packet_queue.get_nowait()
    except queue.Empty:
        dummy = generate_dummy_packet()
        logger.info("Generated dummy packet: %r", dummy)
        return dummy


def get_next_bit(secret_bits: list[int], current_bit_index: int) -> tuple[int, int]:
    if current_bit_index >= len(secret_bits):
        current_bit_index = 0

    bit = secret_bits[current_bit_index]
    logger.info("Next bit to send: %d", bit)
    return bit, current_bit_index + 1


def buffer_packet(packet_queue: queue.Queue, buffer: list) -> None:
    try:
        data = packet_queue.get_nowait()
        buffer.append(data)
        logger.info("Buffered packet for delayed sending (bit 1)")
    except queue.Empty:
        pass


def send_packet_for_bit(
    consumer: socket.socket, packet_queue: queue.Queue, buffer: list, bit: int, elapsed_time: float
) -> float:
    if bit == 1 and buffer:
        data = buffer.pop(0)
    else:
        data = get_packet_from_queue_or_dummy(packet_queue)

    consumer.sendall(data)
    send_time = time.time()
    logger.info(
        "Sent packet for bit '%d' (delay: %.3fs)",
        bit,
        elapsed_time,
    )
    return send_time


def is_ready_to_send(bit: int, elapsed_time: float) -> bool:
    if bit == 0:
        return elapsed_time >= config.BIT_0_DELAY
    else:
        return elapsed_time >= config.BIT_1_DELAY


def send_packets_with_timing(consumer: socket.socket, packet_queue: queue.Queue, secret_bits: list[int]):
    current_bit = None
    current_bit_index = 0
    buffer = []

    try:
        data = get_packet_from_queue_or_dummy(packet_queue)
        consumer.sendall(data)
        last_send_time = time.time()

        while True:
            current_time = time.time()
            elapsed_time = current_time - last_send_time

            if current_bit is None:
                current_bit, current_bit_index = get_next_bit(secret_bits, current_bit_index)

            if is_ready_to_send(current_bit, elapsed_time):
                last_send_time = send_packet_for_bit(consumer, packet_queue, buffer, current_bit, elapsed_time)
                current_bit = None
            elif current_bit == 1:
                buffer_packet(packet_queue, buffer)

            time.sleep(0.01)

    except KeyboardInterrupt:
        logger.info("Packet sender stopped by user")
    except Exception as e:
        logger.error("Error sending data: %r", e)


def handle_connection(producer: socket.socket, secret_bits: list[int]):
    consumer = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        consumer.connect((config.CONSUMER_HOST, config.CONSUMER_PORT))
        packet_queue = queue.Queue(maxsize=100)

        receiver = threading.Thread(
            target=receive_packets,
            args=(producer, packet_queue),
            daemon=True,
        )

        sender = threading.Thread(
            target=send_packets_with_timing,
            args=(consumer, packet_queue, secret_bits),
            daemon=True,
        )

        receiver.start()
        sender.start()

        receiver.join()
        sender.join()

    except KeyboardInterrupt:
        logger.info("Connection handler stopped by user")
    except Exception as e:
        logger.error("Error handling connection: %r", e)
    finally:
        producer.close()
        consumer.close()


def start_proxy(secret_file: str):
    secret_bits = read_secret_bits(secret_file)
    sock = setup_server()

    try:
        while True:
            producer, addr = sock.accept()
            logger.info("Connection from %r", addr)
            threading.Thread(target=handle_connection, args=(producer, secret_bits), daemon=True).start()

    except KeyboardInterrupt:
        logger.info("Proxy stopped by user")
    except Exception as e:
        logger.error("Server error: %r", e)
    finally:
        if sock:
            sock.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--secret-file", help="File containing secret bits to transmit")

    args = parser.parse_args()

    start_proxy(args.secret_file)


if __name__ == "__main__":
    main()
