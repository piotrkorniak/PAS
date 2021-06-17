import os
from os.path import basename
import shutil
import datetime



import os
import zipfile
import socket
import os
from random import seed
from random import randint
import _thread
import time

def answ_data(server):
    answ = b''
    while b'\r\n' not in answ:
        answ += server.recv(1)
        
    print(answ.decode('UTF-8'))
    return answ.decode('UTF-8')


 
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

def unpackZip(path):
    #name = path.split('\\')[-1].split('.zip')[0]
    #print(name)
    shutil.rmtree("Synchronizacja")
    shutil.unpack_archive(path,"Synchronizacja")


try:
    file_name = datetime.datetime.now().strftime("[%d.%m.%Y-%H;%M;%S]") + "synch32131312.zip"
    s.connect(('localhost', 1337))
    s.sendall("SEND".encode())
    data = answ_data(s)
    port = int(data.split(" ")[2])
    fullsize = int(data.split(" ")[3])
    s2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s2.connect(("localhost",port))
    f = open(file_name, 'wb')
    size = 0
    while size < fullsize:
        f.write(s2.recv(1))
        size+=1
    f.close()
    s2.close()
    s.close()

except socket.error:
    print ('Error')



