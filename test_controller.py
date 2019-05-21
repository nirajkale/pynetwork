from pynet import *

c = Controller()
client1 = c.get_client()
client1.ping('hello')
