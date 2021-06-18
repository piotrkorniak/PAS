import json
import os
import hashlib

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
            os.mkdir(str(login))
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
        log(data,login,password)
    else:
        register(login,password)
    return

logowanie(data,"andzej","andzej1")
