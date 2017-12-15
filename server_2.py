import os
import sys
import paramiko
import socket
import threading
from Crypto.Cipher import AES
import sqlite3
import json
import untangle

# Create DB connection
con = sqlite3.connect("system_moniter.db", check_same_thread=False)
db_cursor = con.cursor()


class Server(object):

    def __init__(self, host, port):
        self._host = host
        self._port = port

    def __enter__(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((self._host, self._port))
        sock.listen(10)
        print "nListening for incoming connections..."
        self._sock = sock
        return self._sock

    def __exit__(self, *exc_info):
        if exc_info[0]:
            import traceback
            traceback.print_exception(*exc_info)
        self._sock.close()


class ClientSetup(object):

    def __init__(self, client_ip, username, password, server_ip, server_port):
        self.client_ip = client_ip
        self.username = username
        self.password = password
        self.client_file_src = os.path.join(os.getcwd(), 'client.py')
        self.client_file_dest = None
        self.server_ip = server_ip
        self.server_port = server_port

    def connect_ssh(self):
        ssh_client = paramiko.SSHClient()
        ssh_client.load_system_host_keys()
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh_client.connect(self.client_ip,
                           username=self.username,
                           password=self.password,
                           allow_agent=False,
                           look_for_keys=False)
        self._ssh_client = ssh_client

    def copy_client_file(self):
        sftp = self._ssh_client.open_sftp()
        sftp.put(self.client_file_src, self.client_file_dest)

    def run_client_file(self):
        stdin, stdout, stderr = self._ssh_client\
            .exec_command("python {} {} {}".format(self.client_file_dest,
                                                   self.server_ip,
                                                   self.server_port))

    def close_conn(self):
        self._ssh_client.close()

    def verify_client_platform(self):
        stdin, stdout, stderr = self._ssh_client\
            .exec_command("python -c 'import platform; print(platform.system())' ")
        client_os = str(stdout.readlines()[0].replace('\n', ''))
        if client_os == 'Linux':
            self.client_file_dest = '/tmp/client.py'
        elif client_os == 'Windows':
            #TODO Windows file path
            pass

    def run(self):
        self.connect_ssh()
        self.verify_client_platform()
        self.copy_client_file()
        self.run_client_file()
        self.close_conn()


def listenToClient(client, address, client_ip):
    size = 1024
    try:
        data = client.recv(size)
        if data:
            decoded_data = json.loads(decode_data(data))
            insert_data(decoded_data, client_ip)
    except:
        return False
    client.close()


def insert_data(decoded_data, client_ip):
    query = "INSERT INTO system_stats " +\
            "(Ip, Cpu_usage, Mem_usage, Uptime) " +\
            " VALUES('{}','{}','{}','{}')"\
            .format(client_ip,
                    decoded_data['cpu_usage'],
                    decoded_data['memory_usage'],
                    decoded_data['uptime'])
    db_cursor.execute(query)
    con.commit()


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

    server_ip = str(sys.argv[1])
    server_port = int(sys.argv[2])

    with Server(server_ip, server_port) as sock:
        obj = untangle.parse(os.path.join(os.getcwd(), 'config.xml'))
        for client in obj.xml.client:
            client_ip = client["ip"]
            username = client["username"]
            password = client["password"]

            client = ClientSetup(client_ip,
                                 username,
                                 password,
                                 server_ip,
                                 server_port)
            client.run()

            client_conn, address = sock.accept()
            threading.Thread(target=listenToClient,
                             args=(client_conn, address, client_ip)).start()
