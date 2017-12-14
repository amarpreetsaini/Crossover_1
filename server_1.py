import os
import paramiko
import socket
import threading
from Crypto.Cipher import AES
import sqlite3
import json
import untangle

cwd = os.getcwd()

con = sqlite3.connect("system_moniter.db", check_same_thread=False)
db_cursor = con.cursor()

client_file_src = os.path.join(cwd, 'client.py')
client_file_dest = '/tmp/client.py'

server_ip = '192.168.1.5'
server_port = 9999

obj = untangle.parse('config.xml')
for client in obj:
    print client
    client_ip = client["ip"]
    username = client["username"]
    password = client["password"]


class Server(object):

    def __init__(self, host, port):
        self._host = host
        self._port = port

    def __enter__(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind((self._host, self._port))
        sock.listen(10)
        self._sock = sock
        return self._sock

    def __exit__(self, *exc_info):
        if exc_info[0]:
            import traceback
            traceback.print_exception(*exc_info)
        self._sock.close()


def client_handler(sock):
    client, address = sock.accept()
    threading.Thread(target=listenToClient,
                     args=(client, address)).start()


def connect_ssh(client_ip, username, password):
    ssh_client = paramiko.SSHClient()
    ssh_client.load_system_host_keys()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh_client.connect(client_ip,
                       username=username,
                       password=password,
                       allow_agent=False,
                       look_for_keys=False)
    return ssh_client


def copy_client_file(ssh_client, client_file_src, client_file_dest):
    sftp = ssh_client.open_sftp()
    sftp.put(client_file_src, client_file_dest)


def listen_socket(server_ip, server_port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind((server_ip, server_port))
    sock.listen(1)
    while True:
        client, address = sock.accept()
        threading.Thread(target=listenToClient,
                         args=(client, address)).start()


def listenToClient(client, address):
    size = 1024
    while True:
        try:
            data = client.recv(size)
            if data:
                decoded_data = json.loads(decode_data(data))
                insert_data(decoded_data)
        except:
            client.close()
            return False


def insert_data(decoded_data):
    query = "INSERT INTO system_stats " +\
            "(Ip, Cpu_usage, Mem_usage, Uptime) " +\
            " VALUES('{}','{}','{}','{}')"\
            .format(decoded_data['client_ip'],
                    decoded_data['cpu_usage'],
                    decoded_data['memory_usage'],
                    decoded_data['uptime'])
    db_cursor.execute(query)
    con.commit()


def run_client(ssh_client):
    stdin, stdout, stderr = ssh_client.exec_command("python /tmp/client.py")


def decode_data(raw_data):
    """
    """
    key = "1234567890123456"
    encryption_suite = AES.new(key, AES.MODE_CBC, 'This is an IV456')
    cipher_text = encryption_suite.decrypt(raw_data)

    unpad = lambda s: s[0:-ord(s[-1])]
    decrypted_text = unpad(cipher_text)
    return decrypted_text


if __name__ == '__main__':
    ssh_client = connect_ssh(client_ip, username, password)
    copy_client_file(ssh_client, client_file_src, client_file_dest)
    run_client(ssh_client)
    listen_socket(server_ip, server_port)
