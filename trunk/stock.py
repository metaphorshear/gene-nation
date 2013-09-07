import re
import os
import time
import requests


class Stock(object):
    """
    exchange is a four letter code consisting of 'X' + the first three letters
    of the exchange name. e.g., XNAS for NASDAQ.
    if csv is provided, then there is no need to call Stock.dl.
    """
    def __init__(self, exchange, symbol, csv=None):
        self.vals = {}
        self.csv = []
        self.deltas = [] #probably won't use this until I add a GUI
        self.high = 0
        self.low = 0
        self.open = 0
        self.close = 0
        self.vol = 0
        self.adjclose = 0
        self.csv = csv
        self.name = None
        self.symbol = symbol
        self.exchange = exchange
        self.price_data = []
        self.cur_date = '2012-01-01'
        self.commission = 5.0 #Five dollars, TradeKing's commission.
    def parse(self):
        if self.csv is None:
            print "Add self.csv first."
            return
        if self.price_data == []:
            print "Run dl with 'prices' as an argument."
            return
        years = re.compile(r'20[01]{2}')
        quote = re.compile(r'"')
        numbers = re.compile(r'"?-?[0-9][0-9,.]+"?')
        numbs = re.compile(r'[0-9][0-9]+')
        for line in self.csv:
            if re.findall(years, line) != []:
                pass
            elif re.findall(quote, line) != []:
                rez = re.findall(numbers, line)
                g = lambda x: x.strip('"').replace(',', '')
                stuff = [ g(i) for i in rez ]
                if stuff != []:
                    self.vals[re.split(numbers,line)[0]] = stuff
            elif re.findall(numbs, line) != []:
                v = line.rstrip('\n').split(',')
                self.vals[v[0]] = v[1:]
        self.price_data = self.price_data[-1:0:-1] #pop off the top line, and reverse
        tmp = {}
        for line in self.price_data:
            t = line.strip().split(',')
            tmp[t[0]] = t[1:]
        self.price_data = tmp
        return self.vals

    def convert(self):
        """
        Converts numbers to floating point
        """
        if self.csv is None:
            return
        if self.vals != {}: #parse has been run
            for key in self.vals:
                    y = lambda x: float(x) if x != '' else 0
                    self.vals[key] = [ y(i) for i in self.vals[key] ]
        return self.vals

    def dl(self, choice, date=None):
        """
        Downloads historical data if it does not exist on disk or is old, otherwise
        opens the existing file. Either way, the data is added to self.csv for later
        parsing (if morningstar) or some other thing (if yahoo)
        """
        day = month = year = 0
        if self.symbol is None or self.exchange is None:
            return
        if self.csv is None:
            self.csv = []
        def readin(url, source, dest):
            if source == 'disk':
                #print "Loading copy of", self.symbol, choice, "from disk"
                t = open('csvs/'+self.symbol+choice+'.csv', 'r')
                dest += t.readlines()
                t.close()
                return True
            elif source == 'net':
                print "Now downloading from ", choices[choice]
                s = requests.Session()
                resp = s.get(choices[choice.lower()])
                a = open('csvs/'+self.symbol+choice+'.csv', 'w')
                a.write(resp.content)
                a.close()
                for i in resp.iter_lines():
                    dest.append(i)
                s.close()
                return True
            else:
                return False
        if choice == 'prices':
            if date is None: return False
            month, day, year = date
        choices = {'key': 'http://financials.morningstar.com/ajax/exportKR2CSV.html?&callback=?&t=' \
        +self.exchange+':'+self.symbol+'&region=usa&culture=en-US&cur=USD',
            'income' : 'http://financials.morningstar.com/ajax/ReportProcess4CSV.html?&t=' \
        +self.exchange+':'+self.symbol+'&region=usa&culture=en-US&ops=clear&cur=USD&reportType=is&' \
        +'period=12&dataType=A&order=asc&columnYear=5&rounding=3&view=raw&r=305437&denominatorView=raw&number=3',
            'cash flow': 'http://financials.morningstar.com/ajax/ReportProcess4CSV.html?&t=' \
        +self.exchange+':'+self.symbol+'&region=usa&culture=en-US&cur=USD&reportType=cf&period=12&' \
        + 'dataType=A&order=asc&columnYear=5&rounding=3&view=raw&r=657620&denominatorView=raw&number=3',
            'balance sheet': 'http://financials.morningstar.com/ajax/ReportProcess4CSV.html?' + \
            '&t='+self.exchange+':'+self.symbol+'&region=usa&culture=en-US&cur=USD&reportType=bs&'  +\
            'period=12&dataType=A&order=asc&columnYear=5&rounding=3&view=raw&r=24616&denominatorView=raw&number=3',
            'prices' : 'http://ichart.finance.yahoo.com/table.csv?s=' + self.symbol + '&a=' + str(month) \
             + '&b='+ str(day) + '&c=' + str(year) + '&d='+ str(month) + '&e=' + str(day) + '&f='+ str(year+1) + '&g=d&ignore=.csv' }
        try:
            if choice == 'prices': dest = self.price_data
            else: dest = self.csv
            if (time.time() - os.path.getmtime('csvs/'+self.symbol+choice+'.csv')) < (86400*3):
                readin(choices[choice], 'disk', dest)
            else:
                readin(choices[choice], 'net', dest)
            return True
        except os.error:
            readin(choices[choice], 'net', dest)
        return True

    def update(self, date):
        """
        Make the current day the given date, and load the data for that day from
        Yahoo historical.
        """
        if type(date) is tuple:
            month, day, year = date
            month += 1
            if len(str(month)) == 1:
                month = '0'+str(month)
            if len(str(day)) == 1:
                day = '0' + str(day)
            date = str(year)+'-'+str(month)+'-'+str(day)
        if type(self.price_data) is not dict:
            print "Please run stock.parse"
            return
        try:
            op, high, low, close, volume, adjclose = [float(i) for i in self.price_data[date]]
            self.deltas = [op - self.open, high - self.high, low - self.low,
            close - self.close, volume - self.vol, adjclose - self.adjclose]
            self.open = op
            self.high = high
            self.low = low
            self.close = close
            self.vol = volume
            self.adjclose = adjclose
            return self.deltas
        except KeyError:
            pass #There's no info for this day, so just skip it and the deltas will still work right.
