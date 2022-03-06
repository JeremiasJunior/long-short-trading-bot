# -*- coding: utf-8 -*-
"""
Created on Thu Oct 29 23:03:15 2020

@author: zigoo
"""

import pandas as pd
import numpy as np
from statsmodels.tsa.stattools import coint
from backend.mt5_tools import mt5_historicaldata
from backend.mt5_tools import mt5_lastdata
from datetime import datetime
import matplotlib.pyplot as plt

from arch.unitroot import engle_granger

def volatility(df):
    data = []
    for i in range(len(df)-1):
        data.append((df[i+1]-df[i])/df[i])

    return data

class h_coint:


    def __new__(self,df, tf, threshold = 0.1, column = 'close', save=False, n_lags=None):

        symbol_list = list()

        for i in df.keys():
            if not (df[i].empty):
                symbol_list.append(i)

        print(symbol_list)

        raw_start = str(df[symbol_list[0]].index[0])
        raw_end =  str(df[symbol_list[0]].index[-1])
        date_start = '{}'.format(raw_start.split(' ')[0])
        date_end = '{}'.format(str(raw_end).split(' ')[0])

        fname = 'coint{}_{}x{}.xls'.format(tf,str(date_start), str(date_end))
        coint_list = {'pvalue':[], 'stdx':[], 'stdy':[],'x':[], 'y':[]}

        size = len(df.keys())*len(df.keys())

        for i in df.keys():
            for j in df.keys():

                #print('{}/{}'.format(counter,size))
                if(i != j):
                    try:
                        eg = engle_granger(df[i][column], df[j][column], lags=n_lags)
                        vol_i = volatility(df[i][column])
                        vol_j = volatility(df[i][column])

                        #print(vol_i, vol_j)


                    except:
                        continue
                    pvalue = eg.pvalue

                    if(pvalue <= threshold):

                        xstd = np.std(df[i]['close'])
                        ystd = np.std(df[j]['close'])

                        coint_list['pvalue'].append(float(pvalue))
                        coint_list['x'].append(i)
                        coint_list['y'].append(j)
                        coint_list['stdx'].append(xstd)
                        coint_list['stdy'].append(ystd)
                    #print(i,j)

        coint_df = pd.DataFrame(coint_list)
        if(save):
            coint_df.to_excel(fname)

        return coint_list

class l_coint:

    def __new__(self, timeframe,
                      count,
                      start = 0, 
                      threshold = 0.05,
                      column = 'close',
                      symbols='symbols.csv'):

        _file = open(symbols, 'r')
        symbol_list = list()

        for i in _file.readlines():
            symbol_list.append(i.strip('\n'))
        
        _file.close()

        print('--getting historical data--')


        data = dict()
        for symbol in symbol_list:
            data[str(symbol)] = mt5_lastdata(str(symbol), timeframe, start, count)

        labels = []
        x_symbols = []
        y_symbols = []
        p_value = []

        plot_data = {'x_symbols':[], 'y_symbols':[], 'p_value':[], 'liquidity':[]}
        ret_data = {}


        for i in symbol_list:

            for j in symbol_list:

                if(i != j):

                    print(i,j)

                    pvalue = coint(data[i][column], data[j][column])[1]

                    if(pvalue <= threshold):
                        
                        liq = sum(data[str(i)]['tickvolume']) + sum(data[str(j)]['tickvolume'])
                        plot_data['x_symbols'].append(i)
                        plot_data['y_symbols'].append(j)
                        plot_data['p_value'].append(pvalue)
                        plot_data['liquidity'].append(liq)
                        
                        ret_data['{},{}'.format(i,j)] = [pvalue, liq]

        plt.show()

        return tuple([data, ret_data])


from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import as_completed

import datetime
import time

class t_coint:

    def __new__(self, 
                    df, tf,
                    threshold = 0.0001,
                    column = 'close', 
                    symbols='symbols.csv',
                    noCoint=False):
        
        fname = 'coint{}_{}{}{}.xls'.format(tf,datetime.datetime.now().hour, datetime.datetime.now().minute, datetime.datetime.now().second)
        symbol_list = list()
        
        for i in df.keys():
            symbol_list.append(i.strip('\n'))
        
        coint_list = {'pvalue':[], 'stdx':[], 'stdy':[],'x':[], 'y':[]}

        future = []
        
        with ThreadPoolExecutor(500) as executor:
            
            for i in df.keys():
                print(i)
                for j in df.keys():
                    if(i!=j):
                        future.append(executor.submit(calc, df[i], df[j], i, j, threshold))

            f_size = len(future)
            counter = 1

            for f in as_completed(future):
                print('{}/{}'.format(counter, f_size))
                
                if(type(f.result()) != type(None)):
                    xstd, ystd, namex, namey, pval = f.result()

                    coint_list['pvalue'].append(pval)
                    coint_list['x'].append(namex)
                    coint_list['y'].append(namey)
                    coint_list['stdx'].append(xstd)
                    coint_list['stdy'].append(ystd)

                counter = counter + 1

        coint_df = pd.DataFrame(coint_list)
        coint_df.to_excel(fname)
        return coint_df

def calc(dfx, dfy, name_x, name_y, threshold):
    pvalue = coint(dfx['close'], dfy['close'])[1]

    x_std = np.std(dfx['close'])
    y_std = np.std(dfy['close'])

    if(pvalue <=  threshold):
        ret = [float(x_std), float(y_std), name_x, name_y, pvalue]
        return ret