import socket
import json
import re
import threading
import platform
import time
import os
from tqdm import tqdm,tqdm_notebook
from threading import Lock

if __package__:
    from .Handshakes import *
else:
    from Handshakes import *


extract_re = lambda r,s: re.search(r,s).group()

str_to_bytes = lambda message: message.encode(encoding = 'utf-8')

bytes_to_str = lambda _bytes: _bytes.decode("utf-8")

default_chunk_size = 8* 1024

print_lock = Lock()

def safe_print(*args, **kwargs):
    with print_lock:
        print (*args, **kwargs)

def register_class_for_serialization(_type):
    name = str(_type)
    class_name =  name[name.index('.')+1:name.rindex('\'')]
    if class_name not in globals():
        globals()[class_name] = _type

def int_to_bytes(i: int, header_size:int = 4) -> bytes:
    return i.to_bytes(header_size, byteorder='big', signed=False)

def long_to_bytes(i: int, header_size:int = 8) -> bytes:
    return i.to_bytes(header_size, byteorder='big', signed=False)

def bytes_to_int(b: bytes) -> int:
    return int.from_bytes(b, byteorder='big', signed=False)


def serialize_obj(obj):

    obj_str= json.dumps(obj.__dict__, indent=1)
    name = str(obj.__class__)
    class_name = name[name.rindex('.')+1:name.rindex('\'')]
    #class_name =  get_classname(obj.__class__)#extract_re("(?<=<class '__.+__).+(?='>)", str(obj.__class__))
    return class_name+':'+obj_str

def de_serialize_obj(string):
    class_name = string[:string.index(':')]
##    print(globals())
    obj = globals()[class_name]()
    obj.__dict__ = json.loads(string[string.index(':')+1:])
    return obj

def receive_data(client, expect_disposal = False, chunk_size = default_chunk_size):
    '''
        returns (type , buffer)
    '''
    #messgage format: 4 bytes of packet type + 8 byte of payload size + payload
    data_type = bytes_to_int(client.recv(4))
    if data_type == (0, 3):
        return (data_type, None) #for ack & eos
    elif data_type in (1,2):
        payload_size = bytes_to_int(client.recv(8))
        buffer = b''
        while payload_size >0:
            payload  = client.recv(min(chunk_size, payload_size))
            buffer += payload
            payload_size -= len(payload)
        if data_type ==2:
            header = de_serialize_obj( bytes_to_str(buffer))
            if header.__class__ is Response and (not header.result):
                #intercept & raise Exception
                raise RemoteException('Backend:'+header.message)
            elif header.__class__ is DisposeRequest and (not expect_disposal):
                raise Exception('Received unexpected disposal requet')
            return (data_type, header)
        return (data_type, buffer)
    else:
        return (data_type, None)

def send_data(client,
              buffer,
              data_type = 1,
              chunk_size = default_chunk_size):
    payload_size = len(buffer)
    packet = int_to_bytes(data_type) + long_to_bytes(payload_size)
    if payload_size <= chunk_size:
        packet += buffer
        client.send(packet)
    else:
        packet += buffer[:chunk_size]
        start_index = chunk_size
        while packet:
            client.send(packet)
            packet = buffer[start_index: start_index+ chunk_size]
            start_index += chunk_size

def send_ack(client):
    client.send(int_to_bytes(0))

def receive_ack(client):
    data_type,_ = receive_data(client)
    if data_type !=0 :
        raise Exception('NaN ack')    

def send_eos(client):
    client.send(int_to_bytes(3))

def receive_eos(client):
    data_type,_ = receive_data(client)
    if data_type !=3 :
        raise Exception('NaN eos') 

def send_raw_bytes(client,buffer):
    send_data(client,
              buffer,
              data_type = 1)

def send_str(client, string):
    buffer = str_to_bytes(string)
    send_data(client,
              buffer = buffer,
              data_type = 1)

def receive_str(client):
    packet_type, buffer =receive_data(client)
    if packet_type==1:
        #print(bytes_to_str(buffer))
        return bytes_to_str(buffer)

def send_int(client, num):
    buffer = int_to_bytes(num)
    send_data(client,
              buffer = buffer,
              data_type = 1)

def receive_int(client):
    packet_type, buffer =receive_data(client)
    if packet_type==1:
        #print(bytes_to_str(buffer))
        return bytes_to_int(buffer)

def send_header(client, header):
    obj_str= serialize_obj(header)
    buffer = str_to_bytes(obj_str)
    send_data(client,
              data_type = 2,
              buffer = buffer)

def receive_header(client):
    data_type, obj= receive_data(client, expect_disposal = True)
    if data_type ==2:
        return obj
    raise Exception('Out of Sync response, Was expecting a header but a got a data_type:'+str(data_type))


def send_file(client, filepath:str, chunk_size:int = default_chunk_size):
    safe_print('\tSending file:',filepath)
    with open(filepath, 'rb') as f:
        buffer = f.read(chunk_size)
        while buffer:
            send_data(client,buffer, chunk_size = chunk_size)
            buffer = f.read(chunk_size)
        send_eos(client)

def receive_file(client, filepath:str, size:int,chunk_size:int = default_chunk_size, verbose:bool=True):
    safe_print('\tReceiving file:',filepath, 'with size:',str(size/1024))
    with tqdm(total = size/1024, disable = (not verbose), unit ='KB') as pbar:
        with open(filepath, 'wb') as f:
            data_type, buffer = receive_data(client, chunk_size = chunk_size)
            if buffer:
                pbar.update(len(buffer)/1024.0)
            while data_type==1:
                f.write(buffer)
                data_type, buffer = receive_data(client, chunk_size = chunk_size)
                if buffer:
                    pbar.update(len(buffer)/1024.0)
            if data_type !=3: #end of stream
                raise Exception('Invalid data type received in file stream')

def send_files(client, files):
    #send verified file list back to the client
    verfied_files = [f for f in files if os.path.isfile(f)]
    filenames = [ (os.path.basename(f),os.path.getsize(f)) for f in verfied_files]
    send_header(client, FilesResponse(True, '', filenames))
    if len(filenames)==0:
        safe_print('No files selected for transmission')
        return 0
    #wait for client to acknowlege this renewed file list
    receive_ack(client)
    #now start sending files one by one
    for file in tqdm(verfied_files, desc = 'Sending Files'):
        send_file(client, filepath= file)
        receive_ack(client)
    return len(filenames)

def receive_files(client, base_dir, verbose = True):
    header = receive_header(client)
    if header.__class__ is not FilesResponse:
        raise Exception('Out of sync header receied from file transmitter')
    #ack server for verified file list
    if len(header.files)>0:
        send_ack(client)
        for fname,size in tqdm(header.files, total= len(header.files),desc='Receiving Files'):
            filepath = os.path.join(base_dir, fname)
            receive_file(client=client, filepath= filepath, size= size, verbose= verbose)
            send_ack(client)
        return len(header.files)
    else:
        safe_print('No files selected for reception')
        return 0

def get_socket():
    sock= socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    return sock


class Listener(threading.Thread):

    def __init__(self,
                 client_callback,
                 port = 1857):
        if not hasattr(client_callback,'__call__'):
            raise Exception('Listener needs a callback method')
        threading.Thread.__init__(self)
        self.port = port
        self.flag_stop_listening = False
        self.client_callback = client_callback
        self.ip = ''
        if platform.os.name =='nt':
            self.ip = 'localhost'

    def run(self):
        while not self.flag_stop_listening:
            self.socket = get_socket()
            self.socket.bind((self.ip,self.port))
            safe_print('Listener binded to port ',self.port)
            self.socket.listen(5)
            client, address = self.socket.accept()
            safe_print('Listener received request from ',address)
            if not self.flag_stop_listening:
                self.client_callback(client)
        
    def stop(self):
        self.flag_stop_listening = True
        temp_client = get_socket()
        temp_client.connect((self.ip, self.port))
        temp_client.send(b'')

class RemoteException(Exception):
    
    def __init__(self, message):
        super().__init__(message)


def callback(client):
    send_int(client, 200)

if __name__ == '__main__':

    pass
        
        
        
        
        


    
            
        

    
    
    
