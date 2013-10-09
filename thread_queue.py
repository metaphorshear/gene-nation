import threading
from Queue import Empty
import pdb
from sys import exc_info

class ThreadsnQueues(threading.Thread):
    """
    Abstract base class for a thread that uses a queue. A function to call may
    be provided; if a list is given for this argument, then it is assumed that
    the first item is a function, and the other items are its arguments.
    """
    def __init__(self, queue, out_queue=None, func=None, args=None, semaphore=None):
        super(ThreadsnQueues, self).__init__()
        self.queue = queue
        self.out_queue = out_queue
        self.semaphore = semaphore
        if func is None:
            try:
                func = self.queue.get(block=False)
            except Empty:
                self.func = None
                return
        if func is not None:
            if type(func) is list:
                self.func = func[0]
                self.args = func[1:]
            else:
                self.func = func
        if args != [] and args != None: self.args = args

class ThreadScore(ThreadsnQueues):
    def __init__(self, queue, out_queue, func, semaphore):
        super(ThreadScore, self).__init__(queue, out_queue, func, None, semaphore)
    def run(self):
        try:
            s = self.queue.get() #should be a stock object
        except Empty:
            print "Empty queue?!"
            return
        except:
            return
        while True:
            try:
                self.semaphore.acquire()
                ret = self.func(s) #should return a score (int)
                self.out_queue.put((s, ret)) #tuple with Stock, int
                self.queue.task_done()
                self.semaphore.release()
                return
            except KeyboardInterrupt:
                raise
            except ArithmeticError:
                a, b, c = exc_info()
                print a, b
                pdb.post_mortem(c)
            except StandardError:
                pass #I have failed you.

class ThreadTrue(ThreadsnQueues):
    """
    Thread for a function that returns True on success. Calls func(*args).
    """
    def __init__(self, queue, out_queue=None, func=None, args=None):
        super(ThreadTrue, self).__init__(queue, out_queue, func, args)
    def run(self):
        if self.func is None:
            return
        while True:
            try:
                ret = self.func(*self.args)
                if ret == True:
                    self.queue.task_done()
                    return
                else:
                    pass
                    #self.queue.put([self.func, self.args])
                    #return
            except KeyboardInterrupt:
                raise
            except ArithmeticError:
                a, b, c = exc_info()
                print a, b
                pdb.post_mortem(c)
