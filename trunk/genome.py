#!/usr/bin/env python
import Queue
from thread_queue import *
from time import sleep
import multirandom
import threading
from thread import error as threrror

class Portfolio_item(object):

    def __init__(self, stock, number, price_ea, total):
        self.stock = stock
        self.number = number
        self.price_ea = price_ea
        self.total = total
    def update(self):
        self.gl = (self.stock.high - self.price_ea) * self.number
        return self.gl

class Genome(object):
    keys = []
    maxsize = 12
    def __init__(self):
        self.weights = {}
        self.portfolio = {}
        self.prefers = {}
        self.scores = {}
        #self.replacements = {}
        self.money = 1000 #USD
        self.active_genes = 0
        self.open_orders = {}
        self.first_run = True
        self.worth = 1000
        self.name = 'Nobody'
    def build_keys(self, h):
        for k in h:
            if k not in self.keys:
                self.keys.append(k)
        self.keys = list(set(self.keys))
        for k in self.keys:
            self.weights[k] = 0
        return self.weights
    def randomize(self):
        """
        Sets randomized weights for a Genome using a true random number source.
        """
        if self.first_run == True:
            try:
                ints = multirandom.getnum(1, 10, len(self.keys)*3)
                if ints == [-1]:
                    raise StandardError, "Connection troubles, most likely. I'll try again in a bit."
                else:
                    idx = 0
                    for key in self.keys:
                        if ints[idx+1]-3 > ints[idx]+3:
                            self.weights[key] = ints[idx+2]
                            self.active_genes += 1
                        idx += 3
                self.first_run = False
            except StandardError, e:
                print e
                sleep(3)
                return False
        self.weights = {key:value for key,value in self.weights.items() if value != 0}
        return self.weights

    def appraise(self, s):
        """
        Appraises stocks based on randomized weights.
        """
        score = 0
        def c(l):
            tmp = []
            if (len(l) % 2) != 0:
                l.insert(0, 1.0)
            for i in range(0, len(l), 2):
                if float(l[i]) != 0:
                    tmp.append((float(l[i+1])*100.0)/float(l[i]))
            return (sum(tmp)/len(tmp)) if len(tmp) != 0 else 0
        for k in s.vals:
            try:
                score += ((float(self.weights[k])/10.0) * c(s.vals[k]))
            except KeyError:
                pass #screw it
        return score/self.active_genes if self.active_genes != 0 else 0

    def choose(self, stocks):
        """
        Scores the whole list of stocks, and puts the top twelve on a list to be
        purchased.
        """
        tmp = {}
        queue = Queue.Queue()
        out_queue = Queue.Queue()
        procs = []
        thread_limit = 15
        sym = threading.BoundedSemaphore(thread_limit)
        for stock in stocks:
            queue.put(stock)
        while queue.empty() != True:
            try:
                for j in range(thread_limit):
                    t = ThreadScore(queue=queue, out_queue=out_queue, func=self.appraise, semaphore=sym)
                    t.daemon = True
                    t.start()
                    procs.append(t)
            except ArithmeticError:
                raise
            except threrror:
                [ p.join() for p in procs ]
                procs = []
            except KeyboardInterrupt:
                raise
            except StandardError as e:
                print e
                [ p.join() for p in procs ]
                procs = []
        [ p.join(timeout=2.5) for p in procs ]
        print "Finished scoring stocks, sorting..."
        while out_queue.qsize() > 0:
            l, r = out_queue.get() #unpack tuples of Stock, int
            tmp[l] = r #tmp[<Stock>] = score
        pmt = sorted(tmp, key=lambda x: tmp.get(x), reverse=True)
        self.prefers = { key: value for (key, value) in zip(pmt, sorted(tmp.values(), reverse=True))}
        self.scores = self.prefers.copy()
        return self.prefers

    def cond_order(self, stock=None, price=None, number=None, btype=None, inc=None):
        """
        Adds the stock to a dict of open orders. Checks daily to see if the order
        should be executed yet.
        Price is the total that will be spent (num stocks * stock.open)+stock.commission
        Btype is one of limit_buy, limit_sell, trailing_sell, or trailing_buy (as a string)
        If provided, the optional increment should be between zero and one, and it will be used
        as a percentage
        """
        if (stock is not None) and (price is not None) and (number is not None) and (btype is not None):
            if (btype == 'limit_buy' or btype=='limit_sell'):
                self.open_orders[stock] = (price, number, btype)
            elif (btype == 'trailing_sell' or btype=='trailing_buy'):
                if inc is None:
                    inc = .25
                #total price, # shares, type, peg, trigger, increment
                self.open_orders[stock] = (price, number, btype, stock.open,\
                stock.open*(1-inc), inc)
        else:
            reap = []
            for stock in self.open_orders:
                tup = self.open_orders[stock]
                if len(tup) == 6:
                    price, number, btype, peg, trigger, inc = tup
                else:
                    price, number, btype = tup
                if btype == 'limit_buy':
                    if (price-stock.commission)/number <= stock.low:
                        self.portfolio[stock.symbol] = Portfolio_item(stock,\
                        number, stock.open, price)
                        print "Limit order executed for ", number, " shares of ", \
                        stock.symbol, " at ", stock.low
                elif btype == 'limit_sell':
                    if (price-stock.commission)/number >= stock.high:
                        self.portfolio.pop(stock.symbol)
                        reap.append(stock)
                        #handle the money elsewhere for limit orders, temporarily
                elif btype == 'trailing_sell':
                    peg = max(stock.high, peg)
                    trigger = peg * (1-inc)
                    if trigger >= stock.high:
                        print stock.symbol, " fell below trigger of ", trigger
                        self.money += ((stock.high * number) - stock.commission)
                        self.portfolio.pop(stock.symbol)
                        reap.append(stock)
                else:
                    pass
            for key in reap:
                self.open_orders.pop(key)
                print "Choosing replacement stock..."
                self.bids()
    def update(self):
        self.cond_order()
        worth = self.money
        print "GAIN/LOSS -------------------"
        for key in self.portfolio:
            worth += (self.portfolio[key].stock.high * self.portfolio[key].number)
            print key, self.portfolio[key].update()
        self.worth = worth
        return True

    def bids(self, stock=None):
        """
        Buys the preferred stocks (based on the appraisal function) if they can
        be afforded. If the price is only a little more than what is available (<50% above budget)
        then a limit order will be queued.
        """
        queue = Queue.Queue()
        self.divisor = sum(self.prefers.values()[:self.maxsize])
        if self.divisor == 0: return None
        mlock = threading.RLock()
        self.tmp = sorted(self.prefers, key=lambda x: self.prefers[x], reverse=True)
        self.tmp = self.tmp[:self.maxsize]
        for key in self.tmp:
            queue.put(key)
        def callback(self, key):
            ideal = ((self.scores[key]/self.divisor) * self.money) + key.commission
            if key.open == 0:
                if ideal > key.commission:
                    if self.money < ideal:
                        return True
                    mlock.acquire()
                    self.cond_order(key, ideal, 1, 'limit_buy')
                    self.money -= ideal
                    mlock.release()
                else:
                    self.prefers.pop(key)
                    self.divisor = sum(self.prefers.values()[:self.maxsize])
                return True
            elif ideal<= key.commission:
                self.prefers.pop(key)
                self.divisor = sum(self.prefers.values()[:self.maxsize])
                return True
            tst = ideal - key.commission
            if key.open / tst > 1.5:
                self.prefers.pop(key)
                self.divisor = sum(self.prefers.values()[:self.maxsize])
                #print key.symbol+" is way too expensive."
            elif key.open / tst > 1:
                if self.money < ideal:
                    return True
                self.cond_order(key, ideal, 1, 'limit_buy')
                print "Putting in a limit order for 1 share of "+key.symbol+" at "+str(ideal)
                mlock.acquire()
                self.money -= ideal
                mlock.release()
            else:
                num = int(tst/key.open)
                price = (num * key.open)+key.commission
                if self.money < price:
                    return True
                if (num != 0) and ( price <= self.money):
                    print "Buying", num,"shares of", key.symbol, "@", key.open, "a share, for a total of", price
                    self.portfolio[key.symbol] = Portfolio_item(key, num,\
                         key.open, (num * key.open))
                    mlock.acquire()
                    self.money -= (num * key.open)
                    mlock.release()
                else:
                    self.prefers.pop(key)
                    self.divisor = sum(self.prefers.values()[:self.maxsize])
                    #Ideal must be fairly low, and key.open sort of high?
            return True #either we were successful, or we popped a key and set it up for the next guy
        while queue.empty() != True:
            ts = []
            for i in range(self.maxsize):
                try:
                    t = ThreadTrue(queue=queue, func=callback, args=[self, queue.get()])
                    t.daemon = True
                    t.start()
                    ts.append(t)
                except threrror:
                    [ t.join() for t in ts]
        [ t.join() for t in ts]
        stops = int(self.money/5.0) #Hard-coding the commission. Wanna fight about it?
        it = iter(self.portfolio) #iterator over keys
        for i in range(stops):
            try:
                p = self.portfolio[it.next()]
                self.cond_order(p.stock, p.total, p.number, 'trailing_sell', .15)
            except StopIteration:
                break
        return self.portfolio

class LinkedGenome(Genome):
    #children on the left, parents on the right
    def __init__(self, parents=[]):
        super(LinkedGenome, self).__init__()
        self.parents = parents
    def is_child(self, genome):
        if genome in self.parents:
            return True
        else: return False
    def is_parent(self, genome):
        if self in genome.parents:
            return True
        else: return False
    def is_abomination(self):
        #will need to be updated if siblings are introduced
        if self.parents == []: return False
        for parent in self.parents:
            try:
                for grandparent in parent.parents:
                    if self.is_child(grandparent):
                        return True
            except AttributeError:
                return False
            ret = is_abomination(parent)
        return ret
    #def incesticide(self, mercy=None):
        #"""
        #If mercy is True, then just make this kid a little less fit
        #"""
        #if self.is_abomination():
            #if mercy == True:
                #t = sorted(self.weights, key=lambda x: self.weights[x])
                #t[0] += t[-1]
                #t[-1] *= -1
            #else:
                #destroy somehow?