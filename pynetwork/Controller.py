import threading
import abc
import time
import platform
import os
import warnings

if __package__:
    from .Handshakes import *
    from .SubroutineStreamer import *
    import pynetwork.backend2 as bk
else:
    from Handshakes import *

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
        socket = bk.get_socket()
        try:
            socket.connect( (self.gateway_ip, self.port))
        except Exception as inner_e:
            bk.safe_print('Error while connecting to gateway ',str(inner_e))
        status_code = bk.receive_int(socket)
        if status_code ==200:
            return Client(socket, self.download_dir, self.verbose)
        else:
            raise Exception(self,status_error[status_code])
        return None

class Client:

    def __init__(self, socket, download_dir = '', verbose = True):
        self.socket= socket
        self.download_dir = download_dir
        self.verbose = verbose

    def __check__(self, resp):
        if resp.result:
            return True
        else:
            raise Exception(resp.message)

    def __check2__(self,header):
        bk.send_header(self.socket, header)
        self.__check__(bk.receive_header( self.socket))

    def get_files_from_gateway(self,\
                               regex:str='',\
                               files:[]=[],\
                               folder:str=''):
        if regex == '' and files ==[] and folder =='':
            raise Exception('Either regex, file list & folder needs to provided')        
        bk.send_header( self.socket, SendFiles(regex= regex, files = files, folder= folder))        
        bk.receive_files(self.socket, self.download_dir, verbose = self.verbose)
        if self.verbose:
            bk.safe_print('Files are downloaded')

    def send_files_to_gateway(self,
                              dirname:str='',
                              files:[]=[]):
        if len(files)<=0:
            raise Exception('Cannot transfer files using empty list')
        filenames = [os.path.basename(f) for f in files]
        bk.send_header(self.socket, ReceiveFiles(dirname= dirname, filenames = filenames))
        bk.receive_ack(self.socket)
        bk.send_files(self.socket, files)
        if self.verbose:
            bk.safe_print('Files sent to gateway.')

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
        bk.send_header(self.socket, PingRequest(message=message) )
        resp = bk.receive_header( self.socket)
        self.__check__(resp)
        bk.safe_print('Response from Handler:',resp.message)

    def close_handler(self):
        bk.send_header(self.socket, DisposeRequest( mode = 0))
        self.__check__(bk.receive_header( self.socket))

    def close_gateway(self):
        bk.send_header(self.socket, DisposeRequest( mode = 1))
        self.__check__(bk.receive_header( self.socket))


def sample_callback(name,ident, buffer):
    bk.safe_print('steam callback from ',name,'= index:', ident, ' val:', bk.bytes_to_str(buffer))

def sample_eos_callback(name):
    bk.safe_print('Eos for:',name)

if __name__ == '__main__':

    try:
        gateway_ip = '192.168.0.105'
        controller = Controller(gateway_ip = gateway_ip)
        client1 = controller.get_client()
        bk.safe_print('pinging handler')
        client1.ping()
        d = r'C:\Users\703235761\Documents\License'

        bk.safe_print('\n\nDownloading files form gateway..')
        client1.get_files_from_gateway(folder = d)

        bk.safe_print('\n\nUploading files to gateway..')
        client1.send_files_to_gateway(dirname='test', files = [os.path.join(d,f) for f in os.listdir('Pictures')])
        
        bk.safe_print('\n\nTest for receiving subroutine streaming..')
        client1.get_subroutine_stream(name='str_sensor',\
                              callback= sample_callback,\
                              eos_callback= sample_eos_callback,\
                              arguments=[4, 55]
                        )

        bk.safe_print('\n\nTest for receiving subroutine data batch ..')
        bk.safe_print(bk.bytes_to_str( client1.get_subroutine_batch(name='str_sensor_batch',arguments=['123'])))
        bk.safe_print(bk.bytes_to_str( client1.get_subroutine_batch(name='str_sensor_batch',arguments=['456'])))

        bk.safe_print('\n\nTest for sending subroutine data batch ..')
        buffer = bk.str_to_bytes('sample data')
        bk.safe_print(client1.send_subroutine_batch(name='set_io', buffer = buffer ,arguments=[2,True]))
        bk.safe_print(client1.send_subroutine_batch(name='test'))

        input('Testing completed, Press enter to close gateway')
        bk.safe_print('closing gateway..')
        client1.close_gateway()
        
    except Exception as e:
        bk.safe_print('Error in client main')
        bk.safe_print(e)
    input('Enter to close')
    
        
    
            
            
            
