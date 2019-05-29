import inspect

if __package__:
    from .Handshakes import *
    from pynetwork.backend2 import *
else:
    from Handshakes import *
    from backend2 import *


def stream_from_subroutine(socket,name,function, arguments, kwargs):
    try:  
        generator = function(*arguments, **kwargs)
        try:
            ident, buffer = next(generator)
            while buffer!=None and ident>=0:
                payload = to_bytes(DataType.long, ident) + buffer
                send_raw_bytes(socket,payload)
                receive_signal(socket,expected_signal= Signal.ack)
                ident, buffer = next(generator)
            send_signal(socket, Signal.eos)
        except StopIteration as e_si:
            safe_print('StopIteration from subroutine')
            send_signal(socket, Signal.eos)
        except RemoteException as re:
            safe_print('Streaming aborted by client')
            return
        except SignallingError as se:
            safe_print(se)
            return
        except Exception as e_gen:
            safe_print('Error in subroutine execution')
            send_header(socket, Response(False, str(e_gen)))
    except TypeError as e_fun:
        send_header(socket, Response(False, 'Argument mismatch while calling the subroutine'))
    except Exception as e:
        safe_print('Error in stream_data_from_subroutine')
        raise e

def batch_from_subroutine(socket,name,function, arguments, kwargs):
    try:
        payload = function(*arguments, **kwargs)
        send_raw_bytes(socket, payload)
        receive_signal(socket,expected_signal= Signal.ack)
    except TypeError as e_fun:
        send_header(socket, Response(False, 'Argument mismatch while calling the subroutine'))
    except Exception as e:
        safe_print('Error in subroutine execution/transmission')
        send_header(socket, Response(False, str(e)))
        raise e

def receive_subroutine_stream(socket, subroutine_name, callback, eos_callback):
    '''This function assumes that a succcessfule handshake has already happened between
    transmitter & receiver
    '''
    try:
        result = None
        signal, payload = receive_data_v2(socket)
        while signal == Signal.data:
            if result!= None and result.__class__ is bool and result==False:
                safe_print('Stream reception abort requested by callback')
                send_header(socket, Response(False, 'Subroutine stream reception aborted by client'))
                return
            send_signal(socket,Signal.ack)
            ident, buffer = from_bytes(DataType.long, payload[:8]), payload[8:]
            result = callback(subroutine_name, ident, buffer)
            signal, payload = receive_data_v2(socket)
        if signal == Signal.eos: #eos
            safe_print('stream eos reached, raising eos_callback')
            if eos_callback !=None:
                eos_callback(subroutine_name)
            return
        else:# header in the middle of the stream means an error in generator execution
            raise SignallingError(expected_signal= Signal.eos, acutal_signal= signal)
    except Exception as e:
        safe_print('Error in receive_subroutine_stream')
        raise e

def receive_subroutine_batch(socket):
    '''This function assumes that a succcessfule handshake has already happened between
    transmitter & receiver
    '''
    try:
        signal, payload = receive_data_v2(socket)
        if signal == Signal.data:
            send_signal(socket, Signal.ack)
            return payload
        else:
            raise SignallingError(expected_signal= Signal.data, acutal_signal= signal)
    except Exception as e:
        safe_print('Error in receive_subroutine_batch')
        raise e

def forward_batch_to_subroutine(socket, function, arguments, kwargs):
    try:
        signal, payload = receive_data_v2(socket)
        if signal == Signal.data:
            if payload != b'':
                kwargs['buffer'] = payload
            result = function(*arguments, **kwargs)
            safe_print('result:',result)
            if result != None and result.__class__ is int:
                send_custom_data(socket, DataType.int, result)
            else:
                send_custom_data(socket, DataType.int, 0)
        else:
            raise SignallingError(expected_signal= Signal.data, acutal_signal= signal)
    except TypeError as e_fun:
        send_header(socket, Response(False, 'Send:Argument mismatch while calling the subroutine'))
    except Exception as e:
        safe_print('Error in forward_batch_to_subroutine')
        raise e


def send_batch_to_subroutine(socket, buffer):
    if not buffer:
        buffer = b''
    send_raw_bytes(socket, buffer)
    return receive_custom_data(socket,DataType.int)
    

    
