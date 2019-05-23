
class SendFiles:

    def __init__(self, regex:str='', files:[]=[], folder:str=''):
        self.regex = regex
        self.files = files
        self.folder = folder

    def __str__(self):
        return str.format('SendFiles:- Regex:{0} Files:{1} Folder:{2}', self.regex, self.files, self.folder)

class ReceiveFiles:

    def __init__(self, dirname:str='', filenames:[]=[]):
        self.dirname = dirname
        self.filenames = filenames

    def __str__(self):
        return str.format('ReceiveFiles:- Dirname:{0} filenames:{1}', self.dirname, self.filenames)

class ExecSubroutine:

    def __init__(self, name:str='', \
                 direction:str='get', \
                 mode:str='stream', \
                 arguments:[]=[],\
                 kwargs:{}={}):
        if direction not in ('get','set'):
            raise Exception('Invalid mode')
        if mode not in ('stream','batch'):
            raise Exception('Invalid mode')
        if direction =='set' and mode =='stream':
            raise Exception('Stream mode is only available for "Get" direction')
        self.direction = direction
        self.name= name
        self.mode = mode
        self.arguments = arguments
        self.kwargs = kwargs

    def __str__(self):
        return str.format('ExecSubroutine:- mode:{0} Subroutine:{1}', self.mode, self.name)

class PingRequest:

    def __init__(self, message:str=''):
        self.message = message

    def __str__(self):
        return str.format('PingRequest:- message:{0}',self.message)

class Response:

    def __init__(self,result:bool=False, message:str = ''):
        self.result = result
        self.message = message

    def __str__(self):
        return str.format('Response:- result:{0} message:{1}', self.result, self.message)

class FilesResponse(Response):

    def __init__(self,result:bool=False, message:str = '', files:[]=[]):
        super(FilesResponse, self).__init__(result, message)
        self.files = files

    def __str__(self):
        return str.format('Response:- result:{0} message:{1} file count: {2}', self.result, self.message, len(self.files))

class DisposeRequest:

    def __init__(self, mode:int=0):
        self.mode = mode
        #0: dispose handler only
        #1: dispose both handler & gateway

    def __str__(self):
        return str.format('DisposeRequest:- mode:{0}', self.mode)

if __name__ =='__main__':
    a = ['D:\\Niraj\\glove.6B\\glove.6B.100d.txt', 'D:\\Niraj\\glove.6B\\glove.6B.200d.txt']
    f =FilesResponse(True, 'sdfsd', a)
