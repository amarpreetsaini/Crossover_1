"""
Client Module to monitor system level statistics like memory usage, CPU
usage, total uptime and return to Server.
"""

import psutil
import json
import socket
import time
from datetime import timedelta
from Crypto.Cipher import AES

# TODO create config
host = '10.50.1.185'
port = 9999
retryAttempts = 5
attempt = 1
client_ip = '10.50.1.118'

def collect_stats():
    """
    Collect stats from client machine
    """
    stats = {}
    stats['cpu_usage'] = str(psutil.cpu_percent())
    stats['memory_usage'] = str(psutil.virtual_memory().percent)
    uptime_seconds = time.time() - psutil.boot_time()
    stats['uptime'] = str(timedelta(seconds=uptime_seconds))
    stats['client_ip'] = str(client_ip)
    stats_json = json.dumps(stats)
    return stats_json


def encrypt_data(raw_data):
    """
    AES Encryption  of raw data for security
    """
    key = "1234567890123456"
    BS = 16
    pad = lambda s: s + (BS - len(s) % BS) * chr(BS - len(s) % BS) 
#    pad = lambda s: s + (BS - len(s) % BS) * ' ' 

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
    except socket.error:
        if attempt < retryAttempts:
            attempt += 1
            send_data(host, port, data)
        else:
            raise socket.error

if __name__ == '__main__':
    raw_stats = collect_stats()
    encrypted_data = encrypt_data(raw_stats)
    send_data(host, port, encrypted_data)
