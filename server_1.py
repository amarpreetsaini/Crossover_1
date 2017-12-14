import paramiko
import socket
import threading
from Crypto.Cipher import AES
import sqlite3
import json
import xmltodict

con = sqlite3.connect("system_moniter", check_same_thread=False)
db_cursor = con.cursor()

# TODO Read config file for ip

client_ip = '10.50.1.185'
username = "amarpreetsingh"
password = "amar@661"
client_file_src = '/home/amarpreetsingh/client/client.py'
client_file_dest = '/tmp/client.py'

server_ip = '10.50.1.185'
server_port = 9999
paramiko.util.log_to_file("filename.log")


# TODO read config
with open('config.xml') as fd:
   doc = xmltodict.parse(fd.read())

print doc

def connect_ssh(client_ip, username, password):
    ssh_client = paramiko.SSHClient()
    ssh_client.load_system_host_keys()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh_client.connect(client_ip, username=username, password=password)
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
