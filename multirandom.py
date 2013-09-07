#based on truerandom.py by sergio@infosegura.net 

import requests
#import pdb
#from sys import exc_info

def getnum(min,max,amount):
    global randlist
    global url_opener
    randlist = []
    url_opener = requests.Session()
    def randorg(min, max, amount):
        global randlist
        try:
            data = url_opener.get("http://www.random.org/integers/?num="+str(amount)+"&min="+str(min)+"&max="+str(max)+"&col=1&base=10&format=plain&rnd=new")
            for line in data.iter_lines():
                randlist.append(line)
            data.close()
            randlist[:] = [int(line.rstrip('\n')) for line in randlist]
            return randlist
        except:
            randlist=[-1]
            return randlist
    def anu(max, amount):
        global randlist
        dats = {}
        data = None
        try:
            url_opener.verify = False
            data = url_opener.get("https://qrng.anu.edu.au/API/jsonI.php?length="+str(amount)+"&type=uint8")
            if data.json()['success'] == 'false':
                raise StandardError
            dats = data.json()['data']
            data.close()
            return [ i % max for i in dats]
        except StandardError:
            randlist=[-1]
            return randlist
    randorg(min, max, amount)
    if randlist == [-1]:
        return anu(max, amount)
    else:
        return randlist
