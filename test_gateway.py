import pynetwork as pynet
import pynetwork.backend2 as bk
from pynetwork.Subroutines import *
import struct
import shutil
import os

if __name__ == '__main__':

  gw = pynet.Gateway(1857) #start gateway at port 1857
  gw.add_subroutine('str_sensor', fetch_sensor_data)
  gw.add_subroutine('str_sensor_batch', fetch_sensor_batch_data)
  gw.add_subroutine('set_io', set_io)
  gw.add_subroutine('test', test)
  #add above two subroutines with a key, that client can pass to request execution
  gw.start(blocking = True) #start listening to controller


 
