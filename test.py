#!/usr/bin/python

import pool
#import yappi
#Try adding heapy to test memory usage of this code. Switching to SQL might not be the answer.
import pdb
from sys import exc_info
from os import listdir

#yappi.start()
p = pool.Pool()

states = [ float(i[15:]) for i in listdir('.') if i.startswith('stock_gene_pool')]
if states != []:
    p.load_state("stock_gene_pool"+str(max(states)))
try:
    p.new_pool()
    span = (dates for dates in [[(0, 3, 2007), (11, 31, 2008)], [(0, 3, 2008), (11, 31, 2010)],
    [(0, 3, 2010), (0, 3, 2012)], [(0, 3, 2013), (6, 4, 2013)]])
    p.run_pool(iterations=5, incest=False, samespan=False, newspan=span)
except StandardError:
    a, b, c = exc_info()
    print a, b
    pdb.post_mortem(c)
tmp = sorted([gene for gene in p.genomes], key=lambda x: x.worth, reverse=True)
for gene in tmp:
    print gene.worth
    print gene.portfolio.keys()
try:
    print "Winner was", gene.name
    pmt = {key:value for key,value in tmp[0].weights.items() if value != 0}
    mtp = zip(sorted(pmt, key=lambda x: pmt[x], reverse=True), sorted(pmt.values(), reverse=True))
    del pmt
    del tmp
    for key, value in mtp:
        print key, '\t', value
        print
except IndexError:
    print "Ran out of genomes?"
    #print gene.weights

#yappi.stop()
#yappi.print_stats()
