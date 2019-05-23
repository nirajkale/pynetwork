import inspect

if __package__:
    from .Handshakes import *
    import pynetwork.backend2 as bk
else:
    from Handshakes import *
    import backend2 as bk


def stream_from_subroutine(socket,name,function, arguments, kwargs):
    try:  
        generator = function(*arguments, **kwargs)
        try:
            ident, buffer = next(generator)
            while buffer!=None and ident>=0:
                payload = bk.long_to_bytes(ident) + buffer
                bk.send_raw_bytes(socket, payload)
                bk.receive_ack(socket)
                ident, buffer = next(generator)
            bk.send_eos(socket)
        except StopIteration as e_si:
            bk.safe_print('StopIteration from subroutine')
            bk.send_eos(socket)
        except bk.RemoteException as re:
            bk.safe_print('Streaming aborted by client')
            return
        except Exception as e_gen:
            bk.safe_print('Error in subroutine execution')
            bk.send_header(socket, Response(False, str(e_gen)))
    except TypeError as e_fun:
        bk.send_header(socket, Response(False, 'Argument mismatch while calling the subroutine'))
    except Exception as e:
        bk.safe_print('Error in stream_data_from_subroutine')
        raise e

def batch_from_subroutine(socket,name,function, arguments, kwargs):
    try:  
##        bk.safe_print('calling function', name)
##        bk.safe_print('arguments:',arguments, kwargs)
        payload = function(*arguments, **kwargs)
        bk.send_raw_bytes(socket, payload)
        bk.receive_ack(socket)
    except TypeError as e_fun:
        bk.send_header(socket, Response(False, 'Argument mismatch while calling the subroutine'))
    except Exception as e:
        bk.safe_print('Error in subroutine execution/transmission')
        bk.send_header(socket, Response(False, str(e)))
        raise e

def receive_subroutine_stream(socket, subroutine_name, callback, eos_callback):
    '''This function assumes that a succcessfule handshake has already happened between
    transmitter & receiver
    '''
    try:
        result = None
        data_type, payload = bk.receive_data(socket)
        while data_type==1:
            if result!= None and result.__class__ is bool and result==False:
                bk.safe_print('Stream reception abort requested by callback')
                bk.send_header(socket, Response(False, 'Subroutine stream reception aborted by client'))
                return
            bk.send_ack(socket)
            ident, buffer = bk.bytes_to_int(payload[:8]), payload[8:]
            result = callback(subroutine_name, ident, buffer)
            data_type, payload = bk.receive_data(socket)
        if data_type == 3: #eos
            bk.safe_print('stream eos reached, raising eos_callback')
            if eos_callback !=None:
                eos_callback(subroutine_name)
            return
        elif data_type == 2:# header in the middle of the stream means an error in generator execution
            if payload.result: #payload is already converted to an obj by backend
                warnings.warn('Stream interrupted by message from gateway:'+resp.message)
    except Exception as e:
        bk.safe_print('Error in receive_subroutine_stream')
        raise e

def receive_subroutine_batch(socket):
    '''This function assumes that a succcessfule handshake has already happened between
    transmitter & receiver
    '''
    try:
        data_type, payload = bk.receive_data(socket)
        if data_type==1:
            bk.send_ack(socket)
            return payload
        if data_type == 3: #eos
            raise Exception('Client was not expecting a EOS from batch subroutine')
        elif data_type == 2:# header in the middle of the stream means an error in generator execution
            if payload.result: #payload is already converted to an obj by backend
                warnings.warn('Stream interrupted by message from gateway:'+resp.message)
    except Exception as e:
        bk.safe_print('Error in receive_subroutine_batch')
        raise e

def forward_batch_to_subroutine(socket, function, arguments, kwargs):
    try:
        data_type, payload = bk.receive_data(socket)
        if data_type==1:
            if not arguments:
                kwargs ={}
            kwargs['buffer'] = payload
            result = function(*arguments, **kwargs)
            bk.send_int(socket,[result if result.__class__ is int else 0][0])
        if data_type == 3: #eos
            raise Exception('Server was not expecting a EOS while sending data to subroutine.')
        elif data_type == 2:# header in the middle of the stream means an error in generator execution
            if payload.result: #payload is already converted to an obj by backend
                warnings.warn('Stream interrupted by message from client:'+resp.message)
    except TypeError as e_fun:
        bk.send_header(socket, Response(False, 'Send:Argument mismatch while calling the subroutine'))
    except Exception as e:
        bk.safe_print('Error in forward_batch_to_subroutine')
        raise e


def send_batch_to_subroutine(socket, buffer):

    if not buffer:
        buffer = bk.int_to_bytes(0)
    bk.send_raw_bytes(socket, buffer)
    return bk.receive_int(socket)
    

    
