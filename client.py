"""
Client Module to monitor system level statistics like memory usage, CPU
usage, total uptime and return to Server.
"""

import psutil
import json
import socket
import time
import sys
from datetime import timedelta
from Crypto.Cipher import AES

# Client configuration
key = "1234567890123456"
retryAttempts = 10
attempt = 1


def collect_stats():
    """
    Collect stats from client machine
    """
    stats = {}
    stats['cpu_usage'] = str(psutil.cpu_percent())
    stats['memory_usage'] = str(psutil.virtual_memory().percent)
    uptime_seconds = time.time() - psutil.boot_time()
    stats['uptime'] = str(timedelta(seconds=uptime_seconds))
    stats_json = json.dumps(stats)
    return stats_json


def encrypt_data(raw_data):
    """
    AES Encryption  of raw data for security
    """
    BS = 16
    pad = lambda s: s + (BS - len(s) % BS) * chr(BS - len(s) % BS) 

    padded_data = pad(raw_data)
    encryption_suite = AES.new(key, AES.MODE_CBC, 'This is an IV456')
    cipher_text = encryption_suite.encrypt(padded_data)
    return cipher_text


def send_data(host, port, data):
    """
    Send data to Server using socket
    """
    global attempt
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        client_socket.connect((host, port))
        client_socket.send(data)
        client_socket.close()
    except Exception as e:
        if attempt < retryAttempts:
            attempt += 1
            send_data(host, port, data)
        else:
            raise e


if __name__ == '__main__':

    server_ip = str(sys.argv[1])
    server_port = int(sys.argv[2])

    raw_stats = collect_stats()
    print(raw_stats)
    encrypted_data = encrypt_data(raw_stats)
    send_data(server_ip, server_port, encrypted_data)
