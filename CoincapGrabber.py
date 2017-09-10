#!/usr/bin/env python
import math
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
import matplotlib.dates as mdates
from datetime import datetime

# Toggle runtime warnings
warnings_on = False

# Todays datetime
now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# Enter your coin tickers and time masks here:
tickermasks = {
    'BTC'   : ['2014-01-01 00:00:00', str(now)],
    'ETH'   : ['2017-01-01 00:00:00', str(now)],
    'BTS'   : ['2017-08-30 00:00:00', str(now)],
    'STEEM' : ['2017-08-21 00:00:00', str(now)]}

my_tickers = list(tickermasks.keys())
        
# Empty dict that will be filled with len(my_tickers) number of dataframes
df = {}
dfx = {}
times = {}
marketcap = {}
volume = {}
price = {}


fig, axes = plt.subplots(len(my_tickers), figsize=(8,12))
fig.subplots_adjust(hspace=0.5)

# Create dataframes for all tickers in my_tickers
for ticker in my_tickers:
    
    df[ticker] = pd.DataFrame(pd.read_json("http://socket.coincap.io/history/%s" % ticker)) 
    times[ticker] = ((df[ticker]['market_cap'].apply(pd.Series)[0])/1000).astype('int').astype('datetime64[s]')
    marketcap[ticker] = df[ticker]['market_cap'].apply(pd.Series)[1]
    price[ticker] = df[ticker]['price'].apply(pd.Series)[1]
    volume[ticker] = df[ticker]['volume'].apply(pd.Series)[1]    
    
    dfx[ticker] = pd.DataFrame(dict(\
        time = times[ticker],
        marketcap = marketcap[ticker],
        volume = volume[ticker],
        price = price[ticker]))
        
    # Re-index dfx with time column
    dfx[ticker].set_index('time', inplace=True)
    
    # Check if now is out of bounds wrt dataset
    if (datetime.strptime(tickermasks[ticker][0], "%Y-%m-%d %H:%M:%S")) < dfx[ticker].index.min():
        tickermasks[ticker][0] = str(dfx[ticker].index.min())
        if warnings_on:
            print("WARNING: Chosen startdate for %s ticker is outside Coincap.io dataset. Timemask has been adjusted." % ticker)
    if (datetime.strptime(tickermasks[ticker][1], "%Y-%m-%d %H:%M:%S")) > dfx[ticker].index.max():
        tickermasks[ticker][1] = str(dfx[ticker].index.max())
        if warnings_on:
            print("WARNING: Chosen stopdate for %s ticker is outside Coincap.io dataset. Timemask has been adjusted." % ticker)

    # Create time mask based on tickermask input
    tickerindex = my_tickers.index(ticker)
    starttime = tickermasks[ticker][0]
    stoptime = tickermasks[ticker][1]
    mask = (dfx[ticker].index > starttime) & (dfx[ticker].index <= stoptime)
    mask_delta = datetime.strptime(stoptime, "%Y-%m-%d %H:%M:%S")-\
        datetime.strptime(starttime, "%Y-%m-%d %H:%M:%S")
    
    # Adjust visible ticks according to length of dataset
    x_major_interval = int(math.ceil((mask_delta.days/30)/10))
    if mask_delta.days < 14:    
        x_minor_interval = 1
    else:
        x_minor_interval = int(mask_delta.days/10)
    
    # Plot ticker price vs chosen time interval
    axes[tickerindex].plot(dfx[ticker].index[mask], dfx[ticker]['price'][mask], color='black', label='Price')
    axes[tickerindex].grid(True)

    # Plot ticker market cap vs chosen time interval on seperate axis
    ax_mcap = axes[tickerindex].twinx()
    ax_mcap.plot(dfx[ticker].index[mask], dfx[ticker]['marketcap'][mask], '-.', color='black', label='Market Cap')

    # Add vertical padding to bottom part of price/marketcap plots to make 
    # room for barplot. Adjust pad as needed.
    pad = 0.25
    yl = axes[tickerindex].get_ylim()
    axes[tickerindex].set_ylim(yl[0]-(yl[1]-yl[0])*pad,yl[1]) 
    y2 = ax_mcap.get_ylim()
    ax_mcap.set_ylim(y2[0]-(y2[1]-y2[0])*pad,y2[1])  

    # Dynamic adjustment of y-axis labels depending on magnitude
    def ytickfrmt(value, pos):
        if 0 < value < 0.1:
            return '$%1.0fm' % (value*1e3)
        elif 0.1 <= value < 10:
            return '$%1.2f' % (value)
        elif 10 <= value < 1e3:
            return '$%1.0f' % (value) 
        elif 1e3 <= value < 1e6:
            return '$%1.0fk' % (value*1e-3)
        elif 1e6 <= value < 1e9:
            return '$%1.0fM' % (value*1e-6)
        elif 1e9 <= value < 1e12:
            return '$%1.0fB' % (value*1e-9)
        elif value < 0:
            return ''
        else:
            return '$%1.0f' % value

    yformatter = FuncFormatter(ytickfrmt)

    # Set market cap axis labels
    ax_mcap.yaxis.set_major_formatter(yformatter)
    ax_mcap.locator_params(nbins=6, axis='y') 
    ax_mcap.set_ylabel('Market Cap', fontsize=14)    
    ax_volume = axes[tickerindex].twinx()
    
    # Plot bars with last element removed to avoid overlapping bars
    ax_volume.bar(dfx[ticker].index[mask][:-1].values, \
        dfx[ticker]['volume'][mask][:-1], \
        width=1, color='black', alpha=0.1, label='Volume')

    # Turn off ticks for volume barplot. We're only looking at the 
    # changes in volume here and are less interested in the absolute values.
    ax_volume.axes.yaxis.set_ticklabels([])
    ax_volume.grid(False)
    
    # Increase scalefactor to reduce height of bars 
    scalefactor = 1.3
    ax_volume.set_ylim(0, scalefactor*dfx[ticker]['volume'][starttime:stoptime].values.max())    
    
    # Add empty dummy plots to get labels for twin axis
    axes[tickerindex].plot(np.nan, '-.', label = 'Market cap', color='black')
    axes[tickerindex].bar(dfx[ticker].index[mask].values, dfx[ticker]['volume'][mask]/1e16, \
        width=0.5, color='black', alpha=0.1, label='Volume')
    
    # Dynamic adjustment of x-axis labels 
    if 1 <= mask_delta.days < 60:
        axes[tickerindex].xaxis.set_major_formatter(mdates.DateFormatter("\n%b\n%Y"))
        axes[tickerindex].xaxis.set_minor_formatter(mdates.DateFormatter("%d"))
    else:
        axes[tickerindex].xaxis.set_major_formatter(mdates.DateFormatter("%b\n%Y"))
    
    # Title, legend, etc
    axes[tickerindex].xaxis.set_major_locator(mdates.MonthLocator(interval=x_major_interval))
    axes[tickerindex].xaxis.set_minor_locator(mdates.DayLocator(interval=x_minor_interval))
    axes[tickerindex].set_title('%s data -- Last update: %s' % (ticker, dfx[ticker].index[-1]))
    axes[tickerindex].locator_params(nbins=6, axis='y')    
    axes[tickerindex].legend(bbox_to_anchor=(1.4, 1.0), fontsize=10, loc=1, borderaxespad=0.)
    axes[tickerindex].set_ylabel('Price', fontsize=14)
    axes[tickerindex].yaxis.set_major_formatter(yformatter)

plt.savefig('CoincapGrabber_%s.png' % (str(datetime.now().strftime("%Y%m%d_%H%M%S"))), bbox_inches='tight')