import os

import numpy as np

from backend import bkt

import time
import json
import warnings

import datetime
from secrets import token_hex as token

from scipy.stats import norm


warnings.simplefilter('ignore')


class runbkt:
    
    def __new__(self, symbol_x, 
                      symbol_y, 
                      name_x, 
                      name_y, 
                      _period, 
                      s_spread, 
                      l_spread, 
                      tp_s, 
                      tp_l,
                      stop_n,
                      c_min,
                      p_size,
                      t=False):


        
        self.results = bkt.bkt_godhand(independent_ticker=name_x, dependent_ticker=name_y,
                                        df_x = symbol_x, df_y = symbol_y,
                                        short_spread = s_spread, long_spread= l_spread,
                                        column = 'close', position_size=p_size, stop_number=stop_n, min_count=c_min,
                                        tp_long=tp_l, tp_short=tp_s,
                                        period=_period, f_name='', treino = t)

        self.results['profit'] = runbkt.profit(self.results['returns'])
        _profit = runbkt.profit(self.results['returns'])
        self.results['avg_expo'], self.results['stdv_expo'] = runbkt.avg_expo(self.results['expo'])
        self.results['roi'] = runbkt.roi(self.results['returns'], self.results['avg_expo'])
        self.results['ATR'] = runbkt.ATR(symbol_x, symbol_y, self.results['roi'], len(symbol_x))
    

        return self.results

    
    def profit(returns):
        return sum(returns)

    def avg_expo(expo):
        return np.mean(expo), np.std(expo)

   
    def roi(returns, expo):
        if(len(returns) == 0):
            return 0
        
        try:
            roi = sum(returns)/expo
            return roi
        except:
            return 0

    def ATR(x_price, y_price, _profit, _n):
        _TRx = []
        _TRy = []
        _std = np.std(_profit)

        for i in range(1,len(x_price)):
            _TRx.append(max(x_price['high'][i], x_price['close'][i-1]) - min(x_price['low'][i], x_price['close'][i-1]))
        for i in range(1,len(y_price)):
            _TRy.append(max(y_price['high'][i], y_price['close'][i-1]) - min(y_price['low'][i], y_price['close'][i-1]))

        #por enquanto eu não quero o ATR num determinado momento, então vou pegar o total


        ATRx = sum(_TRx)/len(_TRx)
        ATRy = sum(_TRy)/len(_TRy)

        return (ATRx, ATRy, _std)   
