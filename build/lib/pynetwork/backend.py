import socket
import json
import re
import threading

extract_re = lambda r,s: re.search(r,s).group()

str_to_bytes = lambda message: message.encode(encoding = 'utf-8')

bytes_to_str = lambda _bytes: _bytes.decode("utf-8")

default_chunk_size = 8* 1024

def int_to_bytes(i: int, header_size:int = 8) -> bytes:
    return i.to_bytes(header_size, byteorder='big', signed=False)

def bytes_to_int(b: bytes) -> int:
    return int.from_bytes(b, byteorder='big', signed=False)

def receive_bytes(client, chunk_size = default_chunk_size):
    #messgage format: 8 byte header followed by indefinite payload
    payload_size = bytes_to_int(client.recv(8))
    buffer = b''
    while payload_size >0:
        payload  = client.recv(min(chunk_size, payload_size))
        buffer += payload
        payload_size -= len(payload)
    return  buffer

def send_one_shot_message(client,message):
    payload = message.encode(encoding = 'utf-8')
    data = int_to_bytes(len(payload))+ payload
    client.send(data)

def send_bytes(client,message, chunk_size = default_chunk_size):
    payload = message.encode(encoding = 'utf-8')
    data = int_to_bytes(len(payload))+ payload
    client.send(data)

def get_socket():
    sock= socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    return sock

def serialize_obj(obj):

    obj_str= json.dumps(obj.__dict__, indent=1)
    class_name =  extract_re("(?<=<class '"+__name__+".).+(?='>)", str(obj.__class__))
    return class_name+':'+obj_str

def de_serialize_obj(string):
    class_name = string[:string.index(':')]
    obj = globals()[class_name]()
    obj.__dict__ = json.loads(string[string.index(':')+1:])
    return obj

class BaseMessage:

    def __init__(self,data='',exit_flag = False,next_port = 1857):
        self.data = data
        self.exit_flag = exit_flag
        self.next_port = next_port


class Listener:

    def __init__(self, callback, port=1857,
                 allow_closure_by_client=True):
        self.port = port
        self.flag_stop_listening = False
        self.socket = get_socket()
        if not hasattr(callback,'__call__'):
            raise Exception('Server needs a callback method')
        self.callback = callback
        self.listener_flag = True
        self.allow_closure_by_client = allow_closure_by_client

    def start_listening(self):
        self.socket.bind(('',self.port))
        #print('Listener binded to port ',self.port)
        self.socket.listen(1)
        client, address = self.socket.accept()
        base_msg = de_serialize_obj(receive_message(client))
        self.callback(base_msg.data)
        send_message(client, '_')  # send acknowledge to client
        client.close()
        self.socket.close()
        if (not (self.allow_closure_by_client and base_msg.exit_flag)) and (not self.flag_stop_listening):
            self.socket = get_socket()
            self.start_listening()
        else:
            self.flag_stop_listening = False
            print('closing listener')

    def stop_listening(self):
        self.flag_stop_listening = True
        client  = Connector('',self.port)
        client.close_listener()

class Connector:

    def __init__(self, ip:str, port:int = 1857,timeout = 5):
        self.ip = ip
        self.port= port
        self.timeout = timeout


    def test_connection(self):
        self.socket = get_socket()
        self.socket.connect((self.ip, self.port))
        print('connected to server')
        try:
            send_message(self.socket,'test message')
            return receive_message(self.socket) == '_'
        finally:
            self.socket.close()

    def send_message(self, message):
        self.socket = get_socket()
        self.socket.settimeout(self.timeout)
        self.socket.connect((self.ip, self.port))
        bm = BaseMessage(data= message,exit_flag=False,next_port= self.port)
        try:
            send_message(self.socket, serialize_obj(bm))
            if receive_message(self.socket) != '_':
                raise Exception('Client acknowledgement not received')
        finally:
            self.socket.close()

    def close_listener(self):
        self.socket = get_socket()
        self.socket.settimeout(self.timeout)
        self.socket.connect((self.ip, self.port))
        bm = BaseMessage(data= '',exit_flag=True,next_port= self.port)
        try:
            send_message(self.socket, serialize_obj(bm))
            if receive_message(self.socket) != '_':
                raise Exception('Client acknowledgement not received after closure')
        finally:
            self.socket.close()


class BufferedListner():

    def __init__(self,
                 port=1857,
                 allow_closure_by_client=True,
                 buffer_size = 50):
        #no need for special data structure as python lists are inherently thread safe
        self.buffer = []
        self.buffer_size = buffer_size
        self.listner = Listener(self.__callback__,
                                port,
                                allow_closure_by_client)
        self.listner_thread = None
        self._request_closure = False

    def start_listening(self):
        self._request_closure  = False
        self.listner_thread = threading.Thread(target= self.listner.start_listening)
        self.listner_thread.start()
        print('listener thread started')
        self.is_listener_alive = True

    def stop_listening(self):
        self._request_closure = True
        if self.listner_thread and self.listner_thread.isAlive():
            self.listner.close_listener()
            self.listner_thread.join()
            print('listener thread closed')

    def is_alive(self):
        return  self.listner_thread and self.listner_thread.isAlive()

    def __callback__(self,data):

        if len(self.buffer)> self.buffer_size:
            _ = self.buffer.pop()
        #print('data added to the buffer')
        self.buffer.append(data)










