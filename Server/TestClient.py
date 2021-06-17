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

 
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

def unpackZip(path):
    #name = path.split('\\')[-1].split('.zip')[0]
    #print(name)
    shutil.rmtree("Synchronizacja")
    shutil.unpack_archive(path,"Synchronizacja")


try:
    file_name = datetime.datetime.now().strftime("[%d.%m.%Y-%H;%M;%S]") + "synch.zip"
    s.connect(('localhost', 1337))
    s.sendall("SEND".encode())
    s.sendall("cosososos\r\n\r\n".encode())
    f = open(file_name, 'wb')
    file_b = b''    
    x=0
    while b'\r\n\r\n' not in file_b:
       file_b += s.recv(1024) 
       print(x)
       x +=1024
       

    
    f.write(file_b[:-4])

    print("\nPlik pobrany")
    #print("Sciezka do pliku: " + str(os.path.join(sys.path[0], file_name)) + "\n\n\n")

    f.close()
    s.close()

except socket.error:
    print ('Error')
