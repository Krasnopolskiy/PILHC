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
logger = logging.getLogger("Filter 2")


def setup_server() -> socket.socket:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((config.FILTER_HOST, config.FILTER_PORT))
    sock.listen(5)
    logger.info("Start proxy server on %s:%s", config.FILTER_HOST, config.FILTER_PORT)
    return sock


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


def send_packet(consumer: socket.socket, packet_queue: queue.Queue, elapsed_time: float) -> float:
    data = get_packet_from_queue_or_dummy(packet_queue)

    consumer.sendall(data)
    send_time = time.time()
    logger.info("Sent packet (delay: %.3fs)", elapsed_time)
    return send_time


def is_ready_to_send(elapsed_time: float) -> bool:
    return elapsed_time >= config.NORMAL_DELAY


def send_packets_with_timing(consumer: socket.socket, packet_queue: queue.Queue):
    try:
        data = get_packet_from_queue_or_dummy(packet_queue)
        consumer.sendall(data)
        last_send_time = time.time()

        while True:
            current_time = time.time()
            elapsed_time = current_time - last_send_time

            if is_ready_to_send(elapsed_time):
                last_send_time = send_packet(consumer, packet_queue, elapsed_time)

            time.sleep(0.01)

    except KeyboardInterrupt:
        logger.info("Packet sender stopped by user")
    except Exception as e:
        logger.error("Error sending data: %r", e)


def handle_connection(producer: socket.socket):
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
            args=(consumer, packet_queue),
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
