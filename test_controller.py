from pynetwork import *

if __name__ == '__main__':

    try:

##        safe_print('closing gateway..')
##        client1.close_gateway()
        pass 
    except Exception as e:
        safe_print('Error in client main')
        safe_print(e)

    gateway_ip = '' #package will automatically replace '' with localhost for windows
    controller = Controller(gateway_ip = gateway_ip, port = 1857)
    with controller.get_client() as client1:
        safe_print('pinging handler')
        client1.ping()
        d = r'C:\Users\703235761\Documents\Approvals'
        safe_print('\n\nDownloading files form gateway..')
        client1.get_files_from_gateway(folder = d)

        safe_print('\n\nUploading files to gateway..')
        client1.send_files_to_gateway(dirname='29_May', files = [os.path.join(d,f) for f in os.listdir(d)])
        
        safe_print('\n\nTest for receiving subroutine streaming..')
        client1.get_subroutine_stream(name='str_sensor',\
                              callback= sample_callback,\
                              eos_callback= sample_eos_callback,\
                              arguments=[4, 55]
                        )

        safe_print('\n\nTest for receiving subroutine data batch ..')
        safe_print(from_bytes(DataType.string, client1.get_subroutine_batch(name='str_sensor_batch',arguments=['123'])))
        safe_print(from_bytes(DataType.string, client1.get_subroutine_batch(name='str_sensor_batch',arguments=['456'])))

        safe_print('\n\nTest for sending subroutine data batch ..')
        buffer = to_bytes(DataType.string, 'sample data')
        safe_print(client1.send_subroutine_batch(name='set_io', buffer = buffer ,arguments=[2,True]))
        safe_print('testing argless subroutine..')
        safe_print(client1.send_subroutine_batch(name='test'))

        input('Testing completed, Press enter to close handler')
    input('Enter to close')
