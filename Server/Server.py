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
def rsa_algo(p: int,q: int, msg: str):
    # n = pq
    n = p * q
    # z = (p-1)(q-1)
    z = (p-1)*(q-1)

    # e -> gcd(e,z)==1      ; 1 < e < z
    # d -> ed = 1(mod z)        ; 1 < d < z
    e = find_e(z)
    d = find_d(e, z)

    # Convert Plain Text -> Cypher Text
    cypher_text = ''
    # C = (P ^ e) % n
    for ch in msg:
        # convert the Character to ascii (ord)
        ch = ord(ch)
        # encrypt the char and add to cypher text
        # convert the calculated value to Characters(chr)
        cypher_text += chr((ch ** e) % n)

    # Convert Plain Text -> Cypher Text
    plain_text = ''
    # P = (C ^ d) % n
    for ch in cypher_text:
        # convert it to ascii
        ch = ord(ch)
        # decrypt the char and add to plain text
        # convert the calculated value to Characters(chr)
        plain_text += chr((ch ** d) % n)

    return cypher_text, plain_text

def find_e(z: int):
    # e -> gcd(e,z)==1      ; 1 < e < z
    e = 2
    while e < z:
        # check if this is the required `e` value
        if gcd(e, z)==1:
            return e
        # else : increment and continue
        e += 1

def find_d(e: int, z: int):
    # d -> ed = 1(mod z)        ; 1 < d < z
    d = 2
    while d < z:
        # check if this is the required `d` value
        if ((d*e) % z)==1:
            return d
        # else : increment and continue
        d += 1

def gcd(x: int, y: int):
    # GCD by Euclidean method
    small,large = (x,y) if x<y else (y,x)

    while small != 0:
        temp = large % small
        large = small
        small = temp

    return large


def register(login,password):  
   new_data={login:str(rsa_algo(3,11,password))}
   with open('sample.json','r+') as file:
        file_data = json.load(file)
        file_data.update(new_data)
        file.seek(0)
        json.dump(file_data, file, indent = 4)
        try:
            path = os.path.join("C:","Synchronizacja", login)
            os.mkdir(path)
        except OSError as error:
            print("Plik juz istnieje")

def load():    
    with open('sample.json') as json_file: 
        data = json.load(json_file)
        return data

def log(data,login,password):
    p=str(rsa_algo(3,11,password))
    if data[login]==p:
        print("access permission")
        return 1
    else:
        print("Bad password !!!")
        return 0

data=load() #trzeba wywoływać za każdym razem

def logowanie(data,login,password):
    if login in data:
        if log(data,login,password) == 1:
            return 1
        elif log(data,login,password) == 0:
            return 0 # błedne hasło
    else:
        register(login,password)
        return 1 #nowe konto


class Account:
    login = ''
    password = ''

    def setPassword(self,password):
        self.password = password
    
    def setLogin(self,login):
        self.login = login



def checkLogin(login_list,login):
    for obj in login_list:
        if(obj.login == login):
            return obj
    return None

def checkPassword(account, password):
    if( account.password == password ):
        return True
    return False



def givePort():
    port_download = randint(10000,65535)    
    return port_download
    


def recvZip(client,port):
    newPort = givePort()
    s2 = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    s2.bind(("localhost",newPort))
    s2.listen(1)   

    client_download,addres_download = s2.accept()
    print("Download connected: " + addres_download[0])

    s2.send("OK GO\r\n\r\n".encode())
    
    b = b''
    while "\r\n\r\n" not in msg:
        b += s2.recv()
    msg = b.decode()
    full_size = msg.split(" ")[0]
    

    temp_name = datetime.datetime.now().strftime("[%d.%m.%Y-%H;%M;%S]") + "synchronizacja" + str(client.name)    
    main_dir =  os.path.join("C:","Synchronizacja","")
    temp_zip = os.path.join(main_dir,temp_name)
    path_to_unzip = os.path.join("C:","Synchronizacja", client.name)
    
    f = open(temp_zip, 'wb')
    size = 0
    while full_size < size:
        f.write(s2.recv(1))
        size +=1
    f.close()

    shutil.rmtree(path_to_unzip)
    shutil.unpack_archive(temp_zip,path_to_unzip)
    os.remove(temp_zip)


def sendZip(client,path):
    newPort = givePort()
    s2 = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    s2.bind(("localhost",newPort))
    s2.listen(1)   
                   
    size = Path(path).stat().st_size
    client.transport.write(("UPDATE "+ str(newPort) + " " + str(size) +"\r\n\r\n").encode())
    
    client_download,addres_download = s2.accept()
    print("Download connected: " + addres_download[0])
    
    bytes = b''
    while "\r\n\r\n" not in bytes:
        bytes += s2.recv(1)

    if(bytes.decode() == "READY\r\n\r\n"):
        print("USER READY TO DOWNLOAD")

    file = open(path,'rb')
    byte = file.read(1)
    fb = b''
    while byte:
        client_download.sendall(byte)
        byte = file.read(1)


    bytes = b''
    while "\r\n\r\n" not in bytes:
        bytes += s2.recv(1)

    if(bytes.decode() == "SUCCESS\r\n\r\n"):
        print("USER SUCCESS DOWNLOAD")

    print("File sent\n")    
    file.close()
    print("File closed \n")
    s2.close()
    print("Connection dowload closed \n")


def makeZip(login):
     name = datetime.datetime.now().strftime("[%d.%m.%Y-%H;%M;%S]") + "-synchronizacja-" + login
     path = shutil.make_archive(name, 'zip',  os.path.join("C:","Synchronizacja",login))
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
        print('Connection from {}'.format(self.addr))


    def connection_lost(self, exc):
        print('Client disconnected {}'.format(self.addr))
        clients.remove(self)

    def data_received(self, data):
        msg = data.decode()
        if(msg == "HI"):
            print("I recive: {}".format(msg))
            self.transport.write("100 HELLO\r\n\r\n".encode())
            #self.transport.write("SEND ME <204 LOGIN PASSWORD>\r\n\r\n".encode())
            
        #  if(msg.split(' ')[0] == "204" <204 LOGIN PASSWORD>
        
        if(msg.split('\r\n')[0] == "LOGIN"):
            print("I recive: {}".format(msg))
            login = str(msg.split('\r\n')[1])
            password = msg.split('\r\n')[2]
            if(logowanie(data,login,password) == 1):
                print("LOGGED IN")
                self.name = login
                #caly folder do zipa
                #przelaczenie na nowy socket i wyslanie nowego portu
                #dlugosc zipa
                #zipa w bajtach
                #dir =  os.path.join("C:","Synchronizacja",login)
                #path = makeZip(dir)# sciezka do folderu uzytkownika
                self.transport.write("240 LOGGED_IN\r\n\r\n".encode())
                #sesion_id = 1 ########### DO GENEROWANIA
                #self.transport.write("SESIONID " + str(sesion_id) + "\r\n".encode())
                task = asyncio.create_task(self.async_sendZip())
            else:
                print("BAD PASSWORD")
                self.transport.write("403 BAD PASSWORD\r\n\r\n".encode())
  
        
        if(msg == "SEND"): #sprawdzajaca tymczasowa
            print("I recive: {}".format(msg))
            self.name = "LOGIN" + str(self.addr)
            for a in clients:
                print(a.name)
            task = asyncio.create_task(self.async_sendZip())
        
        if(msg.split(' ')[0] == "202"):
            print("I recive: {}".format(msg))
            print("CLIENT HAS SAME FILES")
        
        if(msg.split(' ')[0] == "505"):
            print("I recive: {}".format(msg))
            task = asyncio.create_task(self.async_sendZip())

        if(msg.split(' ')[0] == "203"):
            print("I recive: {}".format(msg))
            print("FILES RECEIVED SUCCESSFULLY")
            
        if(msg.split(' ')[0] == "503"):
            print("I recive: {}".format(msg))
            print("FILES RECEIVED NOT SUCCESSFULLY")

        if(msg.split('\r\n')[0] == "CHANGE"):
            print("I recive: {}".format(msg))
            print("SERVER NEED UPDATE")
            #FUNKCJA UPDATE SERWERA
            #po update 
            for client in clients:
                if(client.name == self.name):
                    client.transport.write("267 CHANGE dlugosc zipa / nowy port\r\n\r\n".encode())
                    task = asyncio.create_task(self.async_sendZip())
                #wyslanie do wszystkich otrzymanego zipa 


    async def async_sendZip(self):
        dir =  os.path.join("C:","Synchronizacja",self.login)
        path = makeZip(dir)
        resp = await loop.run_in_executor(thread_pool,sendZip,self,path)

seed(1)   
data=load()
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
