if __package__:
    import pynetwork.backend2 as bk
else:
    import backend2 as bk

'''
These are just sample subroutines for reference
'''

def fetch_sensor_data(sensor_pin:int, norm_factor:int, **kwargs):

    i = 10
    for i in range(10):
        data = str.format('{0}:sample string val from pin {1} & facotr {2}',i,sensor_pin, norm_factor)
        print('sensor value of i:',i)        
        yield (i,bk.str_to_bytes(data))
    yield (-1, None)

def fetch_sensor_batch_data(str_input:str):
    return bk.str_to_bytes('Fake str data: '+str_input)


def set_io(pin:int, value:bool,**kwargs):
    print('setting io pin ',pin,' to ',value)
    print('kwargs:',kwargs)
    return pin


def test(**kwargs):
    print('calling test')
    return 0
