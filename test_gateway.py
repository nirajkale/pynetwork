from pynet import *

if __name__ == '__main__':

    gateway = Gateway(1857, max_poolsize = 5)
    gateway.add_subroutine('str_sensor', fetch_sensor_data)
    gateway.add_subroutine('str_sensor_batch', fetch_sensor_batch_data)
    gateway.add_subroutine('set_io',set_io)
    gateway.add_subroutine('test',test)
    gateway.start(blocking = True)
    input('Press Enter to close..')
