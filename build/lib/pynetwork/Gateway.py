import threading
import abc
import time
import os
import re
import inspect
import warnings

if __package__:
    import pynetwork.SubroutineStreamer as ss
    import pynetwork.backend2 as bk
    from .Handshakes import *
    from .Subroutines import *
else:
    import SubroutineStreamer as ss
    from Handshakes import *
    from Subroutines import *

''' server response codes:
200: ok
500: error while allocating handler
503: max pool size reached
'''

def try_dispose_client(client):
    try:
        if client != None:
            client.close()
    except Exception as e:
        pass
    

class Gateway:
    
    def __init__(self, port:int, max_poolsize:int = 5, download_dir =''):
        self.port = port
        self.max_poolsize = max_poolsize
        self.handler_pool = {}
        self.subroutines = {}
        self.download_dir = download_dir
        self.is_running = False
        if self.download_dir=='':
            self.download_dir = 'Downloads'
            if not os.path.exists(self.download_dir):
                os.makedirs(self.download_dir)

    def start(self, blocking = False):
        self.listener = bk.Listener(self.callback_listener , self.port)
        self.is_running = True
        self.listener.start()
        if blocking:
            self.listener.join()

    def stop(self):
        self.listener.stop()
        self.listener.join()
        for handler_id in self.handler_pool:
            self.handler_pool[ handler_id].request_closure()
        self.is_running = False
        bk.safe_print('Gateway stopped')

    def callback_handler(self, handler_id, flag_gateway):
        del self.handler_pool[ handler_id]
        if not flag_gateway:
            bk.safe_print('Gatway termination requested by a handler <- client')
            self.stop()

    def callback_listener(self, client):
        if len(self.handler_pool) >= self.max_poolsize:
            bk.send_int(client, 503)
            try_dispose_client( client)
            return
        handler = Handler(client, self.subroutines, self.callback_handler, self.download_dir)
        self.handler_pool[handler.id] = handler
        handler.start()
        return

    def add_subroutine(self, name, subroutine):
        if not hasattr(subroutine,'__call__'):
            raise Exception('Invalid argument provided instead of a subroutine')
        if not inspect.isgeneratorfunction(subroutine):
            warnings.warn('A non-generator function was added to the gateway (Non-generator functions cannot be used in stream mode)')
        self.subroutines[name] = subroutine

    def remove_subroutine(self, name):
        if name in self.subroutines:
            del self.subroutines[self.name]
        else:
            raise Exception('subroutine with identity "'+name+'" does not exist')


class Handler(threading.Thread):

    handler_count = 1001

    def __init__(self, client, subroutines:dict, exit_callback =None, download_dir=''):
        if not hasattr(exit_callback,'__call__'):
            raise Exception('Exit callback needs to be a method')
        threading.Thread.__init__(self)
        self.client = client
        self.exit_callback = exit_callback
        self.id = Handler.handler_count
        Handler.handler_count +=1
        #bk.safe_print('handler thread with id ',self.id,' constructed')
        self.exitflag = False
        self.flag_gateway = True
        self.download_dir = download_dir
        self.subroutines = subroutines

    def send_positive_resp(self, message = ''):
        resp = Response(result = True, message = message)
        bk.send_header(self.client, resp)

    def send_negative_resp(self, message = ''):
        resp = Response(result = False, message = message)
        bk.send_header(self.client, resp)

    def send_files_to_client(self, header):
        try:
            bk.safe_print('inside:send_files_to_client', os.path.exists(header.folder))
            if len(header.files)> 0:
                bk.safe_print('sending files to client from a list')
                bk.send_files(self.client, header.files)
            elif header.folder !='':
                if not os.path.exists(header.folder):
                    self.send_negative_resp('Selected directory does not exist on gateway')
                    return
                files = [os.path.join(header.folder, f) for f in os.listdir(header.folder)]
                if header.regex!='':
                    files = [f for f in files if re.match(header.regex, f)]
                bk.safe_print('sending files to client from a folder:',files)                    
                bk.send_files(self.client, files)
        except Exception as e:
            bk.safe_print('Error in send_files_to_client')
            raise e

    def get_files_from_client(self, header):
        try:
            basedir = self.download_dir
            if header.dirname!='':
                basedir = os.path.join(self.download_dir, header.dirname)
            if not os.path.exists(basedir):
                os.makedirs(basedir)
            bk.send_ack(self.client)
            bk.receive_files(self.client, basedir)
        except Exception as e:
            bk.safe_print('Error in get_files_from_client')
            raise e

    def batch_data_from_subroutine(self, header):
        function = self.subroutines[header.name]
        self.send_positive_resp(message = header.name)
        ss.batch_from_subroutine(socket = self.client,\
                                 name = header.name,\
                                 function = function, \
                                 arguments = header.arguments, \
                                 kwargs = header.kwargs)

    def stream_data_from_subroutine(self, header):
        try:
            function = self.subroutines[header.name]
            if not inspect.isgeneratorfunction( function):
                bk.send_header(self.client, Response(False, 'Non-generator subroutines cannot be used for streaming data'))
                return
            self.send_positive_resp(message = header.name)
            ss.stream_from_subroutine(socket =self.client,\
                                     name = header.name, \
                                     function = function, \
                                     arguments = header.arguments,\
                                     kwargs = header.kwargs)
        except Exception as e:
            bk.safe_print('Error in stream_data_from_subroutine')
            raise e
        
    def send_data_to_subroutine(self,header):
        try:
            self.send_positive_resp(message = header.name)
            function = self.subroutines[header.name]
            ss.forward_batch_to_subroutine(socket = self.client,\
                                           function = function, \
                                           arguments = header.arguments,\
                                           kwargs = header.kwargs)
        except Exception as e:
            bk.safe_print('Error in send_data_to_subroutine')
            raise e            

    def run(self):
        try:
            #first thing that a Handler oughtta do is acknowledge client
            bk.safe_print('handler with id ',self.id,' has started')
            bk.send_int(self.client, 200)
            while not self.exitflag:
                header = bk.receive_header(self.client)
                #bk.safe_print('request to ',self.id,' ',str(header))
                if header.__class__ is SendFiles:
                    self.send_files_to_client(header)
                    #backend has its own implementation of resp
                elif header.__class__ is ReceiveFiles:
                    self.get_files_from_client(header)
                    #backend has its own implementation of resp
                elif header.__class__ is ExecSubroutine:
                    if header.name not in self.subroutines:
                        bk.send_header(self.client, Response(False, 'Subroutine with given identity does not exist.')) 
                    elif header.direction == 'get' and header.mode =='stream':
                        self.stream_data_from_subroutine(header)
                    elif header.direction == 'get' and header.mode =='batch':
                        self.batch_data_from_subroutine(header)
                    elif header.direction == 'set':
                        self.send_data_to_subroutine(header)
                    else:
                        bk.send_header(self.client, Response(False, 'Invalid Subroutine configuration provided to gateway.')) 
                elif header.__class__ is PingRequest:
                    self.send_positive_resp(message = header.message)
                elif header.__class__ is DisposeRequest:
                    if header.mode in (0,1):
                        self.send_positive_resp()
                        self.flag_gateway = not header.mode == 1
                        break
                    else:
                        bk.send_header(self.client, Response(False, 'Invalide Dispose mode'))    
                else:
                    bk.safe_print('request to '+self.id+' Invalid header')
                    bk.send_header(self.client, Response(False, 'Invalide Header'))
        except Exception as e:
            bk.safe_print('Error in handler ', str(e))
        finally:
            try:
                #bk.safe_print('disposeing handler socket')
                try_dispose_client( self.client)
                self.exit_callback(self.id, self.flag_gateway)
            except Exception as e1:
                bk.safe_print('Error in gateway callback:',str(e1))
        bk.safe_print('Handler with id',self.id,'closed')


    def request_closure(self):
        if self.flag_gateway:
            self.exitflag = True
            try:
                self.client.close()
            except Exception as e:
                bk.safe_print('Error in closure request ',str(e))



if __name__ == '__main__':

    gateway = Gateway(1857, max_poolsize = 5)
    gateway.add_subroutine('str_sensor', fetch_sensor_data)
    gateway.add_subroutine('str_sensor_batch', fetch_sensor_batch_data)
    gateway.add_subroutine('set_io',set_io)
    gateway.add_subroutine('test',test)
    gateway.start(blocking = True)
    input('Press Enter to close..')
        
