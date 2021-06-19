import sys
import os
import json
import socket
import asyncio
import concurrent.futures
from zipfile import ZipFile
import shutil
import time
import datetime
from pathlib import Path
from random import seed
from random import randint

pom={}
if not os.path.exists('sample.json'):
    with open('sample.json', 'w') as f:
        json.dump(pom, f)

def rsa_algo(p: int, q: int, msg: str):
    n = p * q
    z = (p - 1) * (q - 1)
    e = find_e(z)
    d = find_d(e, z)

    cypher_text = ''
    for ch in msg:
        ch = ord(ch)
        cypher_text += chr((ch ** e) % n)

    plain_text = ''
    for ch in cypher_text:
        ch = ord(ch)
        plain_text += chr((ch ** d) % n)

    return cypher_text, plain_text


def find_e(z: int):
    e = 2
    while e < z:
        if gcd(e, z) == 1:
            return e
        e += 1


def find_d(e: int, z: int):
    d = 2
    while d < z:
        if ((d * e) % z) == 1:
            return d
        d += 1


def gcd(x: int, y: int):
    small, large = (x, y) if x < y else (y, x)

    while small != 0:
        temp = large % small
        large = small
        small = temp

    return large

def load():
    with open('sample.json') as json_file:
        data = json.load(json_file)
        return data


def register(dicto,login: str, password: str):
    new_data = {login: str(rsa_algo(3, 11, password))}
    with open('sample.json', 'r+') as file:
        file_data = json.load(file)
        file_data.update(new_data)
        file.seek(0)
        json.dump(file_data, file, indent=4)
        dicto=load()
        try:
            path = os.path.join(os.sep, "Synchronizacja", login)
            print("TWORZE FOLDER")
            print(path)
            os.mkdir(path)
        except OSError as error:
            print("Plik juz istnieje")




dicto = load()


def log(data, login: str, password: str):
    p = str(rsa_algo(3, 11, password))
    if data[login] == p:
        print("access permission")
        return 1
    else:
        print("Bad password !!!")
        return 0


dicto = load()  # trzeba wywoływać za każdym razem


def logowanie(data, login: str, password: str):
    data=load()
    if login in data:
        if log(data, login, password) == 1:
            print("Go on")
            return 1
        elif log(data, login, password) == 0:
            print("BAd Password")
            return 0  # błedne hasło
    else:
        print("Rejestracja")
        register(data,login, password)
        data=load()
        return 1  # nowe konto



def recvZip(client, port, full_size):
    s2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s2.connect(("localhost", int(port)))

    s2.sendall("READY\r\n\r\n".encode())

    temp_name = datetime.datetime.now().strftime("[%d.%m.%Y-%H;%M;%S]") + "synchronizacja" + str(client.name) + '.zip'
    main_dir = os.path.join(os.sep, "Synchronizacja")
    temp_zip = os.path.join(main_dir, temp_name)
    path_to_unzip = os.path.join(os.sep, "Synchronizacja", client.name)
    print("PATTTH:  " + path_to_unzip)

    f = open(temp_zip, 'wb')
    size = 0
    while size < int(full_size):
        f.write(s2.recv(1))
        size += 1
    f.close()
    print("SUCCESS FILE RECIVED")
    s2.sendall("203 SUCCESS\r\n\r\n".encode())
    s2.close()

    print("REMOVE PATH DIR:  " + path_to_unzip)
    shutil.rmtree(path_to_unzip)
    if (int(full_size) == 22):
        os.mkdir(path_to_unzip)
    else:
        shutil.unpack_archive(temp_zip, path_to_unzip)
    print("Rozpakowano archiwum")
    os.remove(temp_zip)


def givePort():
    port_download = randint(30000, 65535)
    return port_download


def sendZip(client, path):
    newPort = givePort()
    s2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s2.bind(("localhost", newPort))
    s2.listen(1)

    size = Path(path).stat().st_size
    client.transport.write(("260 UPDATE " + str(newPort) + " " + str(size) + "\r\n\r\n").encode())

    client_download, addres_download = s2.accept()
    print("Download connected: " + addres_download[0])
    msg = b''
    while b'\r\n\r\n' not in msg:
        msg += client_download.recv(1)

    if (msg.decode() == "READY\r\n\r\n"):
        print("USER READY TO DOWNLOAD")

    file = open(path, 'rb')
    byte = file.read(1)
    while byte:
        client_download.sendall(byte)
        byte = file.read(1)

    msg = b''
    while b'\r\n\r\n' not in msg:
        msg += client_download.recv(1)

    if (msg.decode() == "SUCCESS\r\n\r\n"):
        print("USER SUCCESS DOWNLOAD")

    print("File sent\n")
    file.close()
    print("File closed \n")
    client_download.close()
    s2.close()
    print("Connection dowload closed \n")


def makeZip(login):
    name = datetime.datetime.now().strftime("[%d.%m.%Y-%H;%M;%S]") + "-synchronizacja-" + login
    zip_path = os.path.join(os.sep, "Synchronizacja", login)
    print("ZIP PATH: " + zip_path)
    print("NAME: " + name)
    path = shutil.make_archive(name, 'zip', zip_path)
    print("zip made for login: " + login)
    return str(path)


def delete_file(path):
    os.remove(path)
    print("File removed \n")


class SynchronizerServerClientProtocol(asyncio.Protocol):
    def connection_made(self, transport):
        self.transport = transport
        self.addr = transport.get_extra_info('peername')
        clients.append(self)

        print(transport.get_extra_info('socket'))
        print('Connection from {}'.format(self.addr))

    def connection_lost(self, exc):
        print('Client disconnected {}'.format(self.addr))
        clients.remove(self)

    def data_received(self, data):
        msg = data.decode()
        print("I recive: " + str(msg) + "FROM: " + str(self.transport.get_extra_info('peername')))

        if (msg == "HI\r\n\r\n"):
            print("I recive: {}".format(msg))
            self.transport.write("100 HELLO\r\n\r\n".encode())

        elif (msg.split('\r\n')[0] == "LOGIN"):
            print("I recive: {}".format(msg))
            login = str(msg.split('\r\n')[1])
            print("I recive: {}".format(login))
            password = str(msg.split('\r\n')[2])

            if (logowanie(dicto, login, password) == 1):
                print("LOGGED IN")
                self.name = login
                self.transport.write("240 LOGGED_IN\r\n\r\n".encode())
                path = makeZip(self.name)
                task = asyncio.create_task(self.async_sendZip(path))
            else:
                print("BAD PASSWORD")
                self.transport.write("403 BAD PASSWORD\r\n\r\n".encode())


        elif (msg.split('\r\n')[0] == "CHANGE"):
            print("I recive: {}".format(msg))
            print("SERVER NEED UPDATE")
            port = msg.split('\r\n')[1]
            full_size = msg.split('\r\n')[2]
            task = asyncio.create_task(self.async_recvZip(port, full_size))

        else:
            print("BAD COMMAND")
            self.transport.write("404 BAD REQUEST\r\n\r\n".encode())


    async def async_sendZip(self,path):
        resp = await loop.run_in_executor(thread_pool, sendZip, self, path)

    async def async_recvZip(self, port, fullsize):
        resp = await loop.run_in_executor(thread_pool, recvZip, self, port, fullsize)
        for client in clients:
            print("UPDATE OTHER CLIENTS")
            if ((client.name == self.name) and (client != self)):
                print("UPDATE CLIENT: " + str(client.transport.get_extra_info('peername')))
                path = makeZip(self.name)
                print("ZIP MADE PATH: " + str(path))
                task = asyncio.create_task(client.async_sendZip(path))



try:
    print("TWORZENIE FOLDERU GLOWNEGO")
    path = os.path.join(os.sep, "Synchronizacja")
    os.mkdir(path)
except OSError as error:
    print("FOLDER GLOWNY ISTNIEJE")

seed()
dicto = load()
clients = []
thread_pool = concurrent.futures.ThreadPoolExecutor()
loop = asyncio.get_event_loop()
coroutine = loop.create_server(SynchronizerServerClientProtocol, host='localhost', port=1337)
server = loop.run_until_complete(coroutine)
try:
    loop.run_forever()
except:
    pass

server.close()
############################################################################################################################
