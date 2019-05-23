from pynetwork import *

if __name__ == '__main__':

    try:
        gateway_ip = '192.168.0.105'
        controller = Controller(gateway_ip = gateway_ip, port = 443)
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
