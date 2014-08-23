import gevent

def connect(func):

    def wrap(self, *args, **kwargs):
        
        task = gevent.spawn(self.sm.connect, '127.0.0.1', self.server.server_port)
        task.run()
        return func(self, *args, **kwargs)
    return wrap

def run(func, *args):
    task = gevent.spawn(func, *args)
    task.run()
    return task.value
