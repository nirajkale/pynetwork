import pynetwork as pynet
import pynetwork.backend2 as bk
import struct
import shutil
import os

def get_usage_percentage(path, **kwargs):
  '''
  Logic to calculate mount/overall hdd usage
  '''
  print('checking usage:')
  total, used, free = shutil.disk_usage("home")
  usage_per = used/ total
  bk.safe_print('usage', usage_per) # safe_print make sure that output from multiple client/handler threads to console do not mix-up
  b = struct.pack('f', usage_per)    #convert the data bytes that needs to be sent back
  return b

def remove_logs(dirpath:str, **kwargs):
  files = [os.path.join(dirpath,f) for f in os.listdir(dirpath)]
  for f in files: #iterate over files delete each one
      os.remove(f)
  bk.safe_print(len(files),' files deleted')
  return bk.int_to_bytes(len(files)) 

if __name__ == '__main__':

  gw = pynet.Gateway(1857) #start gateway at port 1857
  gw.add_subroutine('mount_usage', get_usage_percentage)
  gw.add_subroutine('remove_logs', remove_logs)
  #add above two subroutines with a key, that client can pass to request execution
  gw.start(blocking = True) #start listening to controller
