import socket
import json
import re
import threading
import platform
import time
import os
from tqdm import tqdm,tqdm_notebook
from threading import Lock
import struct
from enum import Enum
import warnings

if __package__:
    from .Handshakes import *
else:
    from Handshakes import *

extract_re = lambda r,s: re.search(r,s).group()

default_chunk_size = 16* 1024

print_lock = Lock()

class DataType(Enum):

    char = 'c'
    bool = '?'
    int = 'i'
    int_unsigned = 'I'
    long = 'q'
    long_unsigned = 'Q'
    float = 'f'
    double = 'd'
    string = 's'
    list = 'list'
    tuple = 'tuple'
    dict = 'dict'
    none = 'none'

class Signal(Enum):

    ack = 0
    data =1
    header = 2
    eos = 3
    
def to_bytes(data_type:DataType, value):
    if data_type == DataType.string:
        return value.encode(encoding = 'utf-8')
    elif data_type in (DataType.list, DataType.tuple, DataType.dict, DataType.none):
        return json.dumps(value).encode(encoding = 'utf-8')
    return struct.pack(data_type.value, value)

def from_bytes(data_type:DataType, bytes):
    if data_type == DataType.string:
        return bytes.decode("utf-8")
    elif data_type == DataType.tuple:
        return tuple(json.loads(bytes.decode("utf-8")))
    elif data_type in (DataType.list, DataType.dict, DataType.none): 
        return json.loads(bytes.decode("utf-8"))
    return struct.unpack(data_type.value, bytes)[0]

def safe_print(*args, **kwargs):
    with print_lock:
        print (*args, **kwargs)

def register_class_for_serialization(_type):
    name = str(_type)
    class_name =  name[name.index('.')+1:name.rindex('\'')]
    if class_name not in globals():
        globals()[class_name] = _type


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

def receive_data_v2(client, expect_disposal = False, chunk_size = default_chunk_size):
    '''
        returns (signal, buffer/header/None)
    '''
    #messgage format: 4 bytes of packet type + 8 byte of payload size + payload
    signal = Signal( from_bytes(DataType.int, client.recv(4)))
    if signal in ( Signal.ack, Signal.eos): #for ack & eos
        return (signal, None)
    elif signal in (Signal.data, Signal.header):
        payload_size = from_bytes(DataType.long_unsigned, client.recv(8))
        buffer = b''
        while payload_size >0:
            payload  = client.recv(min(chunk_size, payload_size))
            buffer += payload
            payload_size -= len(payload)
        if signal == Signal.header:
            header = de_serialize_obj( from_bytes(DataType.string, buffer))
            if header.__class__ is Response and (not header.result):
                #intercept & raise Exception
                raise RemoteException('Backend:'+header.message)
            elif header.__class__ is DisposeRequest and (not expect_disposal):
                raise Exception('Received unexpected disposal requet')
            return (signal, header)
        return (signal, buffer)
    else:
        return (signal, None)

def send_data_v2(client,signal:Signal,buffer=None, chunk_size = default_chunk_size):
    if buffer == None:
        client.send( to_bytes(DataType.int, signal.value))
    else:
        payload_size = len(buffer)
        packet = to_bytes(data_type= DataType.int, value= signal.value) \
                 + to_bytes(data_type= DataType.long_unsigned, value= payload_size)
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
                
def send_signal(client, signal:Signal):
    send_data_v2(client, signal, None)

def receive_signal(client, expected_signal:Signal):
    signal, _ =  receive_data_v2(client)
    if signal == expected_signal:
        return
    raise SignallingError(expected_signal= expected_signal, acutal_signal= signal)

def send_raw_bytes(client, buffer, chunk_size = default_chunk_size):
    send_data_v2(client, Signal.data , buffer=buffer, chunk_size= chunk_size)

def receive_raw_bytes(client, chunk_size = default_chunk_size):
    signal, buffer = receive_data_v2(client, chunk_size= chunk_size)
    if signal == Signal.data:
        return buffer
    raise SignallingError(expected_signal= Signal.data, acutal_signal=signal)

def send_custom_data(client, data_type:DataType, data):
    buffer = to_bytes(data_type, data)
    send_raw_bytes(client, buffer)

def receive_custom_data(client, data_type:DataType):
    buffer = receive_raw_bytes(client)
    return from_bytes(data_type, buffer)

def send_header(client, header):
    obj_str= serialize_obj(header)
    buffer = to_bytes(DataType.string, obj_str)
    send_data_v2(client, Signal.header, buffer)

def receive_header(client):
    signal, header = receive_data_v2(client, expect_disposal=True)
    if signal == Signal.header:
        return header
    raise SignallingError(expected_signal= Signal.header, acutal_signal= signal)

def send_file(client, filepath:str, chunk_size:int = default_chunk_size):
    safe_print('\tSending file:',filepath)
    with open(filepath, 'rb') as f:
        buffer = f.read(chunk_size)
        while buffer:
            send_raw_bytes(client, buffer, chunk_size= chunk_size)
            buffer = f.read(chunk_size)
        send_signal(client, signal=Signal.eos)

def receive_file(client, filepath:str, size:int,chunk_size:int = default_chunk_size, verbose:bool=True):
    safe_print('\tReceiving file:',filepath, 'with size:',str(size/1024))
    with tqdm(total = size/1024, disable = (not verbose), unit ='KB') as pbar:
        with open(filepath, 'wb') as f:
            signal, buffer = receive_data_v2(client, chunk_size= chunk_size)
            if buffer:
                pbar.update(len(buffer)/1024.0)
            while signal == Signal.data:
                f.write(buffer)
                signal, buffer = receive_data_v2(client, chunk_size= chunk_size)
                if buffer:
                    pbar.update(len(buffer)/1024.0)
            if signal != Signal.eos: #end of stream
                raise SignallingError(expected_signal= Signal.eos, acutal_signal= signal)

def send_files(client, files):
    #send verified file list back to the client
    verfied_files = [f for f in files if os.path.isfile(f)]
    filenames = [ (os.path.basename(f),os.path.getsize(f)) for f in verfied_files]
    send_header(client, FilesResponse(True, '', filenames))
    if len(filenames)==0:
        warnings.warn('No files selected for transmission')
        return 0
    #wait for client to acknowlege this renewed file list
    receive_signal(client, expected_signal= Signal.ack)
    #now start sending files one by one
    for file in tqdm(verfied_files, desc = 'Sending Files'):
        send_file(client, filepath= file)
        receive_signal(client, expected_signal= Signal.ack)
    return len(filenames)

def receive_files(client, base_dir, verbose = True):
    header = receive_header(client)
    if header.__class__ is not FilesResponse:
        raise Exception('Out of sync header receied from file transmitter')
    #ack server for verified file list
    if len(header.files)>0:
        send_signal(client, Signal.ack)
        for fname,size in tqdm(header.files, total= len(header.files),desc='Receiving Files'):
            filepath = os.path.join(base_dir, fname)
            receive_file(client=client, filepath= filepath, size= size, verbose= verbose)
            send_signal(client, Signal.ack)
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
            #safe_print('Listener binded to port ',self.port)
            self.socket.listen(5)
            client, address = self.socket.accept()
            safe_print('Received request from ',address)
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

class SignallingError(Exception):

    def __init__(self, expected_signal:Signal, acutal_signal:Signal):
        super().__init__('was expecting a signal -'+expected_signal.name+' but instead got -'+ acutal_signal.name)

if __name__ == '__main__':

    safe_print('ready..')
        
        
        
        
        


    
            
        

    
    
    
