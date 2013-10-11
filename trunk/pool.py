#!/usr/bin/env python
from stock import Stock, re, os
from genome import Genome, LinkedGenome
from thread_queue import *
from math import ceil
from time import time
from itertools import combinations
import random
import Queue
import cPickle as pickle
import gc




class Pool(object):
    """
    A gene pool, containing ssize Stocks to be analyzed, and psize Genomes.
    Currently, only NASDAQ is used, for simplicity's sake.
    """
    exc = None #Should these be static? I only plan on having one Pool for now, but I haven't made it a Singleton, and I don't think I will.
    symbols = []
    ssize = 100
    psize = 12
    stocks = []
    genomes = []
    names = ['Travis Touchdown', 'Margaret Moonlight', 'Sylvia V', 'Charlie MacDonald',
    'Matt Helms', 'Tyler Durden', 'Marla Singer', 'Chloe Walsh', 'Shinobu Jones', 'Fox Mulder',
    'Dana Scully', 'Randy Savage', 'Anna Kournikova', 'Molly Summers', 'Buffy Summers',
    'Dr. Peace', 'Dr. Feelgood', 'Dr. Strangelove', 'Chun Li', 'Barnaby Jones', 'Tank Abbot',
    'Kate Beckinsale', 'Lara Croft', 'Bruce Campbell', 'Master Blaster', 'Romper Stomper']
    start_date = (0, 3, 2012) #Yahoo uses 00 as January, 11 as December; market opens on the 3rd, I guess
    end_date = (0, 3, 2013) #Don't sell until after tax season
    cur_date = start_date
    def __init__(self):
        """
        saved_state is a flag indicating whether this has been loaded from a saved state, and
        is set by load_state
        """
        try:
            tmp = os.listdir('csvs')
            for i in range(len(tmp)):
                tmp[i] = re.findall(r'[A-Z]+', tmp[i])[0]
                self.symbols = list(set(tmp))
        except OSError:
            pass
        self.ssize -= len(self.symbols)
        self.saved_state = False

    def pick_symbols(self):
        """
        Choose 100 random symbols from the NASDAQ, and create Stock objects for
        them.
        """
        import httplib
        nas = open('nasdaqlisted.txt', 'r')
        #other = open('otherlisted.txt', 'r')
        self.exc = nas.readlines()
        #self.exc += other.readlines()
        nas.close()
        #other.close()
        while len(self.symbols) < self.ssize:
            sym = self.exc.pop(random.randrange(0, len(self.exc))).split('|')[0]
            try:
                con = httplib.HTTPConnection("finance.yahoo.com")
                con.request("HEAD", "/q/hp?s="+sym)
                stat = con.getresponse().status
                if stat == 200:
                    self.symbols.append(sym)
            except httplib.BadStatusLine:
                self.ssize -= 1
        while len(self.symbols) > 0:
            t = self.symbols.pop()
            self.stocks.append(Stock('XNAS', t))
        return self.stocks

    def new_pool(self):
        """
        Perform all the setup tasks: picking symbols, downloading and parsing data,
        and buying the stocks for each Genome's initial portfolio.
        """
        if not self.saved_state:
            self.pick_symbols()
            print "Picked the symbols."
            self.parse_stocks()
        try:
            for gene in self.genomes:
                print gene.name, gene.worth
                if gene.weights == {}:
                    self.genomes.remove(gene)
                if gene.active_genes == 0:
                    gene.randomize()
                if len(gene.scores) != len(self.stocks):
                    gene.choose(self.stocks)
                if gene.money == 1000:
                    gene.bids()
            while len(self.genomes) < self.psize:
                g = Genome()
                g.name = self.names.pop(0)
                print g.name
                for s in self.stocks:
                    g.build_keys(s.vals)
                print "Randomizing keys..."
                ret = False
                while ret == False:
                    ret = g.randomize()
                print "Choosing stocks"
                g.choose(self.stocks)
                print "Buying stocks"
                g.bids()
                self.genomes.append(g)
            gc.collect() #Have to see what this does for me
        except KeyboardInterrupt:
            self.save_state()
            exit()

    def parse_stocks(self):
        """
        Downloads data for each stock (if needed), loads it into the appropriate
        places, and processes it. Since network sockets are kind of slow, this
        function is multithreaded.
        """
        print "Starting to load stock data..."
        queue = Queue.Queue()
        for thing in ['key', 'cash flow', 'income', 'prices']:
            for s in self.stocks:
                queue.put([s.dl, thing, self.start_date])
            print "Loaded queue with new jobs..."
            threads = int(ceil(queue.qsize()/5))
            if threads == 0:
                threads = 1
            while queue.qsize() > 0:
                tpool = []
                for i in range(threads):
                    try:
                        t = ThreadTrue(queue)
                        t.daemon = True
                        tpool.append(t)
                        t.start()
                    except StandardError as e:
                        print "Exception", e
                        [t.join() for t in tpool]
                print "Waiting for threads to complete..."
                [t.join() for t in tpool]
            print "Threads finished"
            queue.join()
        print "Processing stock data..."
        for s in self.stocks:
            s.parse()
            s.convert()
            s.update(self.start_date)
        return self.stocks

    def new_day(self):
        month, day, year = self.cur_date
        days = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
        day += 1
        if day > days[month]:
            day = 1
            month += 1
        if month == len(days):
            month = 0
            year += 1
        self.cur_date = (month, day, year)
        print str(month+1) + "-" + str(day) + "-" + str(year)
        for s in self.stocks:
            s.update(self.cur_date)

    def breed(self, g1, g2, mutation=False, incest=True, mercy=None): #Note to self: add mutation
        """
        g1 and g2 are the parents, mutation causes a random gene to be affected/activated, and
        incest affects the obvious. mutation and incest must be in [True, False]
        """
        print "The fittest shall now breed!"
        if incest == False:
            child = LinkedGenome([g1, g2])
            if child.is_abomination():
                return
        else:
            child = Genome()
        if random.randrange(1, 12) in [7, 12]:
            child.name = self.names.pop(0)
        else:
            child.name = g1.name.split()[0] + ' ' + g2.name.split()[1]
            n = [g.name for g in self.genomes]
            if child.name in n:
                child.name = self.names.pop(0)
        print g1.name, "and", g2.name, "begat", child.name
        n = 2
        name = child.name + 'II'
        def romnum(n):
            roman = { 1 : 'I', 5: 'V', 10: 'X', 50: 'L' }
            if n in roman:
                return roman[n]
            if n < 5:
                if n == 4:
                    return 'IV'
                else:
                    return 'I' + romnum(n-1)
            elif n < 10:
                if n == 9: return 'IX'
                else:
                    return 'V' + romnum(n-5)
            elif n < 50:
                if n == 49: return 'IL'
                elif n == 40: return 'XL'
                else:
                    return 'X' + romnum(n-10)
        while name in self.names:
            n += 1
            name = child.name + romnum(n)
        self.names.append(name)
        child.build_keys(g1.keys)
        tmi = g1.weights.keys() + g2.weights.keys()
        for key in tmi:
            if key not in g1.weights: g1.weights[key] = 0
            if key not in g2.weights: g2.weights[key] = 0
        tmp = zip(g1.keys, map((lambda x, y: g1.weights[x]+g2.weights[y]), tmi, tmi))
        tmp = dict(tmp)
        for k in tmp:
            if tmp[k] > 10:
                child.weights[k] = (tmp[k] % 10)
            elif tmp[k] <= 10:
                child.weights[k] = (tmp[k] % 5)
            if child.weights[k] != 0:
                child.active_genes += 1
        print "Baby's first gamble..."
        child.choose(self.stocks)
        child.bids()
        return child

    def save_state(self):
        """
        Save the contents of the pool in a pickle file, to be restored later.
        """
        print "Now freezing everyone in carbonite..."
        self.__dict__['stocks'] = self.stocks
        self.__dict__['genomes'] = self.genomes
        self.__dict__['names'] = self.names
        pickle.dump(self, open("stock_gene_pool"+str(ceil(time())), "wb"))
        return True

    def load_state(self, filestr):
        """
        Assuming you ran new_pool before saving your state, you can just continue
        with run_pool here, and it'll pick up where you left off.
        """
        print "Unthawing..."
        tmp = pickle.load(open(filestr, "rb"))
        self.__dict__ = tmp.__dict__
        self.saved_state = True
        return True

    def run_pool(self, iterations=1, samespan=True, newspan=None, incest=True, mutation=False, mercy=None):
        """
        Step through each day in the time span, and assess the worth of genomes quarterly.
        If samespan is False, then a newspan must be given either of the form [start_date, end_date]
        with both dates as tuples of (month-1, day, year), or as a generator/iterator over such values
        """
        print "Running through the past to predict the future..."
        def cull(self):
            if len(self.genomes) <= (self.psize/2): #Don't cull; instead, generate some fresh genomes. 
                while len(self.genomes) < (self.psize/2):
                    g = Genome()
                    g.name = self.names.pop(0)
                    print g.name
                    for s in self.stocks:
                        g.build_keys(s.vals)
                    print "Randomizing keys..."
                    ret = False
                    while ret == False:
                        ret = g.randomize()
                    print "Choosing stocks"
                    g.choose(self.stocks)
                    print "Buying stocks"
                    g.bids()
                    self.genomes.append(g)
                gc.collect()
                return
            s = sorted(self.genomes, key=lambda x: x.worth, reverse=True)
            print "Culling ", s[-1].name
            self.genomes.remove(s[-1])
            s = s[:-1]
            print "The survivors will become more set in their ways..."
            for gene in self.genomes:
                for k in gene.weights:
                    if gene.weights[k] > 4:
                        gene.weights[k] += 1
                    else: gene.weights[k] -= 1
                print gene.name
                gene.choose(self.stocks)
                gene.bids()
            kid = None
            k = combinations(range(len(s)), 2)
            while kid == None:
				try:
					i, j = k.next()
					kid = self.breed(s[i], s[j], mutation, incest, mercy)
				except StopIteration:
					break
        try:
            for i in range(iterations):
                while self.cur_date != self.end_date:
                    self.new_day()
                    for gene in self.genomes:
                        print gene.name, gene.worth
                        gene.update()
                    month, day, year = self.cur_date
                    if (month % 4)  == 3 and day == 2:
                        gc.collect()
                        cull(self)
                if samespan==True:
                    pass
                else:
                    try:
                        if type(newspan) == list:
                            self.start_date, self.end_date = newspan
                        else:
                            assert(type(newspan) == type( (i for i in range(1)) ))
                            self.start_date, self.end_date = newspan.next()
                    except: pass
                self.cur_date = self.start_date
                for gene in self.genomes:
                    gene.open_orders = {}
                    for s in gene.portfolio:
                        gene.money += (gene.portfolio[s].stock.high * gene.portfolio[s].number)
                    gene.portfolio = {}
                cull(self)
                #for gene in self.genomes: self.money = 1000
        except KeyboardInterrupt:
            self.save_state()
            exit()