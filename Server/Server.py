import sys
import os
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
    

def makeZip():
     name = datetime.datetime.now().strftime("[%d.%m.%Y-%H;%M;%S]") + "synchronizacja"
     path = shutil.make_archive(name, 'zip',  r"d:\Synchronizacja")
     print("zip made")
     return str(path)
    

def make_send_deleteZip(client):
    
    path = makeZip()

    print(path)

    file = open(path,'rb')
    byte = file.read(1024)
    fb = b''
    x = 1024
    while byte:
        fb += byte
        client.write(byte)
        print("reading ")
        print(x)
        x += 1024
        byte = file.read(1024)

      
    client.write(('\r\n\r\n').encode('utf-8'))
    print("File sent\n")    
    file.close()
    print("File closed \n")
    delete_file(path)
    
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
            self.transport.write("240 HELLO\r\n".encode())
            self.transport.write("SEND ME <204 LOGIN PASSWORD>\r\n\r\n".encode())
        
        #  if(msg.split(' ')[0] == "204" <204 LOGIN PASSWORD>

        if(msg.split(' ')[0] == "204"):
            print("I recive: {}".format(msg))
            account = checkLogin(accounts,msg.split(' ')[1])
            if( account != None):
                password = msg.split(' ')[2]
                if(checkPassword(account,password)):
                    print("LOGGED IN")
                    #cały folder do zipa
                    newPort = givePort()
                    s2 = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
                    s2.bind(("localhost",newPort))
                    s2.listen(1)                  
                    path = makeZip()
                    size = Path(path).stat().st_size
                    self.transport.write(("240 LOGGED_IN "+ str(newPort) + " " + size +"\r\n\r\n").encode())

                    #przełączenie na nowy socket i wysłanie nowego portu
                    #długość zipa
                    #zipa w bajtach
                else:
                    print("BAD PASSWORD")
                    self.transport.write("404 BAD PASSWORD\r\n\r\n".encode())
            else:
                #CREATE ACC
                return     
        
        if(msg == "SEND"): #sprawdzajaca tymczasowa
            print("I recive: {}".format(msg))
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

        if(msg.split(' ')[0] == "105"):
            print("I recive: {}".format(msg))
            print("SERVER NEED UPDATE")
            #FUNKCJA UPDATE SERWERA

            #po update 
            for client in clients:
                client.transport.write("104 YOU NEED UPDATE dłuość zipa / nowy port\r\n\r\n".encode())
                #wyslanie do wszystkich otrzymanego zipa 


    async def async_sendZip(self):
        resp = await loop.run_in_executor(thread_pool,make_send_deleteZip,self.transport)

seed(1)        
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

import socket
import os
from random import seed
from random import randint

seed(1)

s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
s.bind(("localhost",1337))
s.listen(5)

files_list = os.listdir("D:FTP")

while True:
    client,addres = s.accept()
    print ("Connected: " + addres[0])

    data = b''

    while b'\r\n\r\n' not in data:
        data += client.recv(1)

    file = str(data.decode('utf-8'))
    file_name = file[:len(file)-4].lower()
    print ("Looking for: " + file_name + " in: " + "D:FTP" )

    if file_name in files_list:
        print("File exists")
        client.sendall(("File exists" + '\r\n\r\n').encode('utf-8'))

        port_download = randint(10000,65535)
        print ("Download Port: "+ str(port_download))
        client.sendall((str(port_download) +'\r\n\r\n').encode('utf-8'))
        
        s2 = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        s2.bind(("localhost",port_download))
        s2.listen(1)
        client_download,addres_download = s2.accept()
        print("Download connected: " + addres_download[0])

        f = open(('D:FTP\\' + file_name),'rb')
        byte = f.read(1)
        while byte:
            client_download.sendall(byte)
            byte = f.read(1)

        client_download.sendall(('\r\n\r\n').encode('utf-8'))
        print("File sent")
        
        f.close()
        client_download.close()
        s2.close()

        print("Connection closed \n\n\n")

    else:
        client.sendall(("File does not exist" + '\r\n\r\n').encode('utf-8'))
        print("File does not exist")
        print("Connection closed \n\n\n")
    
    client.close()
s.close()