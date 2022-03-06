import numpy as np
import pandas as pd

from arch.unitroot import engle_granger

import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.io as pio

import matplotlib.pyplot as plt

class two_plot:

    def __new__(self, x0, y0):

        fig = make_subplots(rows = 2, cols=1, specs=[[{'secondary_y':True}],[{'secondary_y':True}]])

 
        df_x = x0.copy()
        df_y = y0.copy()

        versus = engle_granger(df_x['close'], df_y['close'], trend='n').return_df()

        versus = versus['Cointegrating Residual']
        versus_x = [i for i in range(len(versus))]
        versus.index = versus_x

        versus_diff = np.diff(versus)
        v_std = np.std(versus_diff)
        #print(v_std)



        for i in range(len(versus))[1:-2]:
            
            if versus[i] < -v_std*(0.8) or versus[i] > v_std*(0.8):
                versus[i] = np.nan
                versus[i-1] = np.nan

        
        versus = versus[1:-2]

 
        df_x = df_x.replace(0, np.nan)
        df_y = df_y.replace(0, np.nan)

        df_x.index = [i for i in range(len(df_x['close']))]
        df_y.index = [i for i in range(len(df_y['close']))]
        
        
        x_x0 = [i for i in range(len(versus))]

        fig.add_trace(go.Candlestick(x=df_x.index,
                                     name='x', 
                                     open=df_x['open'],
                                     high=df_x['high'],
                                     low=df_x['low'],
                                     close=df_x['close']), secondary_y=False, row=1, col=1)

        fig.add_trace(go.Candlestick(x=df_y.index,
                                     name='y',
                                     open=df_y['open'],
                                     high=df_y['high'],
                                     low=df_y['low'],
                                     close=df_y['close'],
                                     increasing_line_color= 'blue', decreasing_line_color= 'gray'), secondary_y=True, row=1, col=1)          
        
        fig.update_layout(xaxis_rangeslider_visible=False)
        
        fig.add_trace(go.Scatter(x=versus.index,
                                 y=((versus)),
                                 name='residuos cointegracao'
        ), secondary_y=False, row=2, col=1)
        '''
        fig.add_trace(go.Scatter(x=versus.index,
                                 y=((versus_diff)),
                                 name='diffresiduos cointegracao'
        ), secondary_y=True, row=2, col=1)
        '''


        fig.layout['yaxis']['range'] = [min(df_x['low']), max(df_x['high'])]
        fig.layout['yaxis2']['range'] = [min(df_y['low']), max(df_y['high'])]

        #fig.show()
        return versus



class moving_avg:

    def __new__(self, df, n):
        n
        cumsum = np.cumsum(np.insert(df, 1, 0)) 
        new = (cumsum[n:] - cumsum[:-n]) / float(n)
        return new


class boillinger_bands:

    def __new__(self, df, n, delta):

        mavg = moving_avg(df, n)
        y0 = list()
        y1 = list()


        for i in range(len(mavg)):
            
            y0_i = mavg[i] + 2*np.std(mavg[:i]) 
            y1_i = mavg[i] - 2*np.std(mavg[:i]) 
            
            y0.append(y0_i)
            y1.append(y1_i)


        return y0, y1


class nan_to_zero:

    def __new__(self, df):

        numpy_df = np.array(df)
        n_df = np.nan_to_num(numpy_df)

        return n_df


class rm_zero:

    def __new__(self, df):

        new_df = list()
        
        for i in df:
            if(i != 0):
                new_df.append(i)

        return np.array(new_df)


class getspread:
    def __init__(self, symbol_x, symbol_y, period):
        new = self.__new__(symbol_x, symbol_y, period)

    def __new__(self, symbol_x, symbol_y, period):
        
        loop_x = list()
        loop_y = list()
        i = int(0)

        ret_spread = list()

        while (i < len(symbol_x)):
            #print(i)
            loop_x.append(symbol_x[i])
            loop_y.append(symbol_y[i])



            if(i >= period):
            
                x_period = np.array(getspread.m_movel(period, loop_x))
                y_period = np.array(getspread.m_movel(period, loop_y))

                spread = x_period/y_period
                precise_ratio = spread[-1]
                spread_z = getspread.zscore(spread)
                ret_spread.append(spread_z[-1])

            i= i+1

        return np.array(np.nan_to_num(ret_spread))

    def m_movel(_period, data):

        data_r = getspread._reverse                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               (data)
        data_r = data_r[0:_period]

        return np.array(data_r)
    
    def _reverse(lst):
        lst.reverse()
        return lst

    def zscore(series):
        return (series - series.mean()) / np.std(series)

