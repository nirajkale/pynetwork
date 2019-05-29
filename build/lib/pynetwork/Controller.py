import threading
import abc
import time
import platform
import os
import warnings

if __package__:
    from .Handshakes import *
    from .SubroutineStreamer import *
    from pynetwork.backend2 import *
else:
    from Handshakes import *
    from backend2 import *

class Controller:

    def __init__(self, gateway_ip = '', port = 1857, download_dir = '', verbose = False):
        self.download_dir = download_dir
        if self.download_dir=='':
            self.download_dir = 'Downloads'
        if not os.path.exists(self.download_dir):
            os.makedirs(self.download_dir)
        self.port = port
        self.gateway_ip = gateway_ip
        if self.gateway_ip =='' and platform.os.name =='nt':
            self.gateway_ip = 'localhost'
        self.status_error = {
            500: 'Gateway encountered an error while allocating handler for the client',
            503: 'Gateway handler pool has reach its max capacity, try again later'
            }
        self.verbose = verbose
        
    def get_client(self):
        socket = get_socket()
        try:
            socket.connect( (self.gateway_ip, self.port))
        except Exception as inner_e:
            safe_print('Error while connecting to gateway ',str(inner_e))
        status_code = receive_custom_data(socket, data_type= DataType.int)
        if status_code ==200:
            return Client(socket, self.download_dir, self.verbose)
        else:
            raise Exception(self, self.status_error[status_code])
        return None

    def close_gateway(self):
        c1 = self.get_client()
        c1.close_gateway()

class Client:

    def __init__(self, socket, download_dir = '', verbose = True):
        self.socket= socket
        self.download_dir = download_dir
        self.verbose = verbose
        self.connected = True
        self.with_flag = False

    def __check__(self, resp):
        if resp.result:
            return True
        else:
            raise Exception(resp.message)

    def __check2__(self,header):
        send_header(self.socket, header)
        self.__check__(receive_header( self.socket))

    def get_files_from_gateway(self,\
                               regex:str='',\
                               files:[]=[],\
                               folder:str=''):
        if regex == '' and files ==[] and folder =='':
            raise Exception('Either regex, file list & folder needs to provided')        
        send_header( self.socket, SendFiles(regex= regex, files = files, folder= folder))
        receive_files(self.socket, self.download_dir, verbose = self.verbose)
        if self.verbose:
            safe_print('Files are downloaded')

    def send_files_to_gateway(self,
                              dirname:str='',
                              files:[]=[]):
        if len(files)<=0:
            raise Exception('Cannot transfer files using empty list')
        filenames = [os.path.basename(f) for f in files]
        send_header(self.socket, ReceiveFiles(dirname= dirname, filenames = filenames))
        receive_signal(self.socket, expected_signal= Signal.ack)
        send_files(self.socket, files)
        if self.verbose:
            safe_print('Files sent to gateway.')

    def get_subroutine_stream(self, name:str,\
                              callback,\
                              eos_callback=None,\
                              arguments:[]=[], \
                              **kwargs):
        self.__check2__(ExecSubroutine( name= name,direction= 'get', mode ='stream', arguments = arguments, kwargs= kwargs))
        receive_subroutine_stream(socket= self.socket,\
                                  subroutine_name = name,\
                                  callback= callback,\
                                  eos_callback = eos_callback)

    def get_subroutine_batch(self, name:str,\
                              arguments:[]=[], \
                              **kwargs):
        self.__check2__(ExecSubroutine( name= name,direction= 'get', mode ='batch', arguments = arguments, kwargs= kwargs))
        return receive_subroutine_batch(socket= self.socket)

    def send_subroutine_batch(self, name:str='',\
                              buffer:[] = None,\
                              arguments:[]=[], \
                              **kwargs):
        self.__check2__(ExecSubroutine( name= name,direction= 'set', mode ='batch', arguments = arguments, kwargs= kwargs))
        return send_batch_to_subroutine(socket = self.socket, buffer = buffer)

    def ping(self, message:str='ping'):
        send_header(self.socket, PingRequest(message=message) )
        resp = receive_header( self.socket)
        self.__check__(resp)
        safe_print('Response from Handler:',resp.message)

    def close_handler(self):
        self.connected = False
        if self.with_flag:
            warnings.warn('Explicit handler closing is not necessary when the object is utilized under "with" statement.')
        send_header(self.socket, DisposeRequest( mode = 0))
        self.__check__(receive_header( self.socket))

    def close_gateway(self):
        send_header(self.socket, DisposeRequest( mode = 1))
        self.__check__(receive_header( self.socket))

    def __enter__(self):
        self.with_flag = True
        return self

    def __exit__(self, type, value, traceback):
        try:
            if self.connected:
                self.with_flag = False
                self.close_handler()
        except Exception as e1:
            pass
        if value != None:
            raise Exception(str(value))


def sample_callback(name,ident, buffer):
    s = from_bytes(DataType.string, buffer)
    safe_print('stream callback from ',name,'= index:', ident, ' val:', s)

def sample_eos_callback(name):
    safe_print('Eos for:',name)

if __name__ == '__main__':

    try:
        gateway_ip = '192.168.0.105'
        controller = Controller(gateway_ip = gateway_ip)
        client1 = controller.get_client()
        safe_print('pinging handler')
        client1.ping()
        d = r'C:\Users\703235761\Documents\License'

        safe_print('\n\nDownloading files form gateway..')
        client1.get_files_from_gateway(folder = d)

        safe_print('\n\nUploading files to gateway..')
        client1.send_files_to_gateway(dirname='test', files = [os.path.join(d,f) for f in os.listdir('Pictures')])
        
        safe_print('\n\nTest for receiving subroutine streaming..')
        client1.get_subroutine_stream(name='str_sensor',\
                              callback= sample_callback,\
                              eos_callback= sample_eos_callback,\
                              arguments=[4, 55]
                        )

        safe_print('\n\nTest for receiving subroutine data batch ..')
        safe_print(from_bytes(DataType.string, client1.get_subroutine_batch(name='str_sensor_batch', arguments=['123'])))
        safe_print(from_bytes(DataType.string, client1.get_subroutine_batch(name='str_sensor_batch', arguments=['456'])))

        safe_print('\n\nTest for sending subroutine data batch ..')
        buffer = to_bytes(DataType.string, 'sample data')
        safe_print(client1.send_subroutine_batch(name='set_io', buffer = buffer ,arguments=[2,True]))
        safe_print(client1.send_subroutine_batch(name='test'))

        input('Testing completed, Press enter to close gateway')
        safe_print('closing gateway..')
        client1.close_gateway()
        
    except Exception as e:
        safe_print('Error in client main')
        safe_print(e)
    input('Enter to close')
    
        
    
            
            
            
