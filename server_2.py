import os
import sys
import paramiko
import socket
import threading
from Crypto.Cipher import AES
import sqlite3
import json
import untangle
from mail import send_mail_notification

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
        self._sock = sock
        return self._sock

    def __exit__(self, *exc_info):
        if exc_info[0]:
            import traceback
            traceback.print_exception(*exc_info)
        self._sock.close()

    @staticmethod
    def listenToClient(client, client_ip, memory_alert, cpu_alert, email_id):
        size = 1024
        try:
            data = client.recv(size)
            if data:
                decoded_data = json.loads(ClientData.decode(data))
                ClientData.insert(decoded_data, client_ip)
                email_alert(decoded_data, memory_alert, cpu_alert, email_id)
        except:
            return False
        client.close()


class ClientSetup(object):

    def __init__(self, client, server_ip, server_port):
        self.client_ip = client["ip"]
        self.username = client["username"]
        self.password = client["password"]
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


class ClientData(object):
    @staticmethod
    def insert(decoded_data, client_ip):
        query = "INSERT INTO system_stats " +\
                "(Ip, Cpu_usage, Mem_usage, Uptime) " +\
                " VALUES('{}','{}','{}','{}')"\
                .format(client_ip,
                        decoded_data['cpu_usage'],
                        decoded_data['memory_usage'],
                        decoded_data['uptime'])
        db_cursor.execute(query)
        con.commit()

    @staticmethod
    def decode(raw_data):
        """
        """
        key = "1234567890123456"
        encryption_suite = AES.new(key, AES.MODE_CBC, 'This is an IV456')
        cipher_text = encryption_suite.decrypt(raw_data)

        unpad = lambda s: s[0:-ord(s[-1])]
        decrypted_text = unpad(cipher_text)
        return decrypted_text


def email_alert(data, memory_alert, cpu_alert, email_id):
    if float(data['memory_usage']) > memory_alert:
#        data = json.dumps(data)
        send_mail_notification(data, email_id, 'MEMORY')
    if float(data['cpu_usage']) > cpu_alert:
#        data = json.dumps(data)
        send_mail_notification(data, email_id, 'CPU')


if __name__ == '__main__':

    server_ip = str(sys.argv[1])
    server_port = int(sys.argv[2])

    with Server(server_ip, server_port) as sock:
        obj = untangle.parse(os.path.join(os.getcwd(), 'config.xml'))
        for client_data in obj.xml.client:
            client_ip = client_data["ip"]
            email_id = client_data["mail"]
            memory_alert = int(client_data.alert[0]["limit"].rstrip('%'))
            cpu_alert = int(client_data.alert[1]["limit"].rstrip('%'))
            client = ClientSetup(client_data, server_ip, server_port)
            client.run()

            client_conn, _ = sock.accept()
            threading.Thread(target=Server.listenToClient,
                             args=(client_conn, client_ip, memory_alert, cpu_alert, email_id)).start()
            
