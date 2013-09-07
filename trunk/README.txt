NOTE: This code contains some silly references at the moment, because it helps keep me entertained while staring a screen for hours. All mentioned names belong to their respective owners.


You can start running the program by typing ./test.py or python test.py.

A Pool object will be created. It will choose 100 random symbols from the NASDAQ (assuming ./csvs is empty, otherwise, it uses as many of those as possible), (down)load the historical fundamental data from Morningstar and the Yahoo historical price data for each Stock, and parse this data to be used by the Genomes.

Initially, it might take a while to download everything.

The Pool also creates the Genomes. There are initially 12. Weights are chosen randomly for each of these based on the keys in Morningstar's historical data. These weights are then used to score Stocks, and sort them by that score. Based on a Genome's assessment of the most valuable Stocks, it will place bids. If a stock can be afforded in the quantity desired, they are bought at "market price" (really the day's open). If the stock is a little too expensive, then a limit order will be queued. Otherwise, the stock will be removed from consideration. That may be tweaked a bit soon.

After a stock has been purchased, there will be a trailing stop sell queued for that stock at 25%. Commission for buys and sells is $5.

Each quarter, the Genome with the lowest worth will be culled from the pool, and the two fittest will breed. Mutation has not been added yet, and crossing over is approached fairly simply.

Most important of all: if you want to stop the simulation, you can press CONTROL+C anytime after stocks have been parsed. Your work will be saved (pickled) and can be resumed later.
