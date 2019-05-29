if __package__:
    from pynetwork.backend2 import *
else:
    from backend2 import *

'''
These are just sample subroutines for reference
'''

def fetch_sensor_data(sensor_pin:int, norm_factor:int, **kwargs):

    i = 10
    for i in range(10):
        data = str.format('{0}:sample string val from pin {1} & facotr {2}',i,sensor_pin, norm_factor)
        print('sensor value of i:',i)        
        yield (i, to_bytes(DataType.string, data))
    yield (-1, None)

def fetch_sensor_batch_data(str_input:str):
    return to_bytes(DataType.string, 'Fake str data: '+str_input)


def set_io(pin:int, value:bool,**kwargs):
    print('setting io pin ',pin,' to ',value)
    print('kwargs:',kwargs)
    return pin


def test(**kwargs):
    print('calling test')
    return 0
