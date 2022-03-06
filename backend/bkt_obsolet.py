# -*- coding: utf-8 -*-

import pandas as pd
import numpy as np
from numpy import log

import json

from datetime import datetime

import time
import math

from backend.bkt_tools import bkt_tools
from scipy.stats import norm

import sys


def godhandlog_start():
    
    godhandlog = {'price':{'y_price':[], 'x_price':[], 'time':[]},
              'spread':[],
              'profit':[],
              'rawlog':{},
              'cumprofit':[],
              'returns':[],
              'stop_count':int(0),
              'positions':{},
              'positions_list':[],
              'max_profit':[],
              'expo':[],
              'loop':{'returns':[]}}

    return godhandlog.copy()



def godhandlog_open(_type,
                    i_date,
                    y_ticket,
                    y_price,
                    y_volume,
                    x_ticket,
                    x_price,
                    x_volume,
                    status,
                    i):

    position_log = {'type':_type,
                    'time':[i_date, None],
                    'x_type':str(),
                    'y_type':str(),
                    'y_ticket':y_ticket,
                    'y_price':[y_price, None],
                    'y_volume':y_volume,
                    'x_ticket':x_ticket,
                    'x_price':[x_price, None],
                    'x_volume':x_volume,
                    'status':'open',
                    'lucro':None,
                    'i':[i, None]}

    return position_log

def godhandlog_save(_dict, x_symbol, y_symbol, name):
    df = pd.DataFrame(_dict)
    df.to_json(name)

class bkt_godhand():

    def __init__(self):

        obj = self.__new__(*args, **kargs)

    def __new__(self,  dependent_ticker, df_x,
                       independent_ticker, df_y,
                       column, f_name,
                       short_spread,
                       long_spread,
                       position_size,
                       stop_return,
                       stop_number,
                       min_count,
                       tp_long,
                       tp_short,
                       tp_return,
                       period,
                       more=False,
                       exchange='IBOV'):
        
        
            
            
        

        self.godhandlog = godhandlog_start()
        self.tools = bkt_tools(self.godhandlog)
        

        position_open = False
        position_key = str

        symbol_x = {'data_frame':df_x,
                    'name':independent_ticker,
                    'column':column,
                    'i':0}

        symbol_y = {'data_frame':df_y,
                    'name':dependent_ticker,
                    'column':column,
                    'i':0}


        dataframe_date = df_x.index
        try:
            days_pass = (dataframe_date[-1] - dataframe_date[0]).days
        except:
            days_pass = 0
        
        self.godhandlog['info'] = {'x_symbol': independent_ticker,
                              'y_symbol': dependent_ticker,
                              'short_spread':short_spread,
                              'long_spread':long_spread,
                              'position_size':position_size,
                              'stop_return':stop_return,
                              'stop_number':stop_number,
                              'tp_short':tp_short,
                              'tp_long':tp_long,
                              'period':period,
                              'date':[str(dataframe_date[0]), str(dataframe_date[-1])],
                              'days':days_pass}

        # initializing loop counter
        loop_counter = 0
        dataframe_size = len(df_x[column])

        self.godhandlog['spread'].append(0)
        i_list = []
        for i in range(dataframe_size):
            i_list.append(i)

            date_timestamp = dataframe_date[i]
            endtime = (date_timestamp.hour == 16 and date_timestamp.minute >= 50)
            #endtime = False
            

            date = str(dataframe_date[i])
            
            stoped = False
            canTrade = True

            symbol_x['i'] = i
            symbol_y['i'] = i

            current_x_price = self.tools.bkt_getprice(df_x, column, i)[0]
            current_y_price = self.tools.bkt_getprice(df_y, column, i)[0]

            self.godhandlog['price']['y_price'].append(current_y_price)
            self.godhandlog['price']['x_price'].append(current_x_price)
            self.godhandlog['price']['time'].append(date)


            returns = 0
            if len(self.godhandlog['price']['time']) >= period:

                if self.godhandlog['price']['x_price'][-1] == 0 or self.godhandlog['price']['y_price'][-1] == 0:
                    canTrade = False
                if len(self.godhandlog['spread']) == 0:
                    canTrade = False

                independent_period  = self.m_movel(period, self.godhandlog['price']['x_price'])
                dependent_period    = self.m_movel(period, self.godhandlog['price']['y_price'])

                if(dependent_period[-1] == 0 or dependent_period[-1] == 0):
                    spread_today = bkt_godhand.getspread(x_period = independent_period, y_period = dependent_period)
                    self.godhandlog['spread'].append(spread_today)
                    continue

                spread_today = bkt_godhand.getspread(x_period = independent_period, y_period = dependent_period)
                
                curr_return = sum(self.godhandlog['returns'])
                


                ratiolot = bkt_godhand.roundlot(current_x_price, current_y_price, position_size)

                if canTrade:


                    if (spread_today >= short_spread) and (position_open == False):

                        '''
                        operação de SHORT-SPREAD entra com short no ativo Y e com long no ativo X
                        _long_val vai armazenar o valor na posição long e _short_val vai armezenar
                        o valor no short
                        '''

                        short_data = self.short_spread(self, symbol_x, symbol_y, position_size, ratiolot, i, date)
                        
                        current_expo = short_data['x_price']*short_data['x_volume'] + short_data['y_price']*short_data['y_volume']
                        

                        position_key = (str(short_data['key']))
                        position_open = True

                    elif (spread_today <= long_spread) and (position_open == False):

                        '''
                        operação de LONG-SPREAD entra com long no ativo Y e com short no ativo X
                        _long_val vai armazenar o valor na posição long e _short_val vai armezenar
                        o valor no short
                        '''

                        long_data = self.long_spread(self, symbol_x, symbol_y, position_size, ratiolot, i, date)
                        current_expo = long_data['x_price']*long_data['x_volume'] + long_data['y_price']*long_data['y_volume']


                        position_key = (str(long_data['key']))
                        position_open = True


                    if position_open == True:
                        
                        if(self.godhandlog['positions'][position_key]['type'] == 'long_spread'):

                            '''
                            A logica de bater a porcentagem teria de ser implementada aqui
                            '''
                            if ((curr_return >= tp_return or spread_today >= (tp_long)) and i > self.godhandlog['positions'][position_key]['i'][0]):
  
                                #fecha posição
                                _a, _b, _c, _d = self.close_position(self, position_key, _x = df_x, _y = df_y, _i = i, c_date = date)
                                returns = _d
                                position_open=False
                                position_key = ''
                                self.godhandlog['expo'].append(current_expo)
                                self.godhandlog['returns'].append(returns)

                                if((sum(self.godhandlog['returns']) <= stop_return) or (len(self.godhandlog['returns']) >= stop_number)):

                                    self.godhandlog['profit'] = sum(self.godhandlog['returns'])
                                    self.godhandlog['info']['returns'] = self.godhandlog['returns']
                                    return self.godhandlog 

                        elif(self.godhandlog['positions'][position_key]['type'] == 'short_spread'):
                            if ((curr_return >= tp_return or spread_today <= (tp_short)) and i > self.godhandlog['positions'][position_key]['i'][0]):

                                #fecha posição
                                _a, _b, _c, _d = self.close_position(self, position_key, _x = df_x, _y = df_y, _i = i, c_date = date)
                                returns = _d
                                position_open=False
                                position_key = ''

                                self.godhandlog['expo'].append(current_expo)
                                self.godhandlog['returns'].append(returns)
                                
                                if(sum(self.godhandlog['returns']) <= stop_return or (len(self.godhandlog['returns']) >= stop_number)):
                                    
                                    self.godhandlog['profit'] = sum(self.godhandlog['returns'])
                                    return self.godhandlog 
                
                self.godhandlog['loop']['returns'].append(returns)
                self.godhandlog['spread'].append(spread_today)
                self.godhandlog['profit'] = sum(self.godhandlog['returns'])



        self.godhandlog['profit'] = sum(self.godhandlog['returns'])
        return self.godhandlog
    

    def short_spread(self, x_symbol, y_symbol, position_size, ratio, i, i_date):

        y_ticket, y_price, y_volume = self.tools.bkt_sell(y_symbol, 0, 0, ratio[1])
        x_ticket, x_price, x_volume = self.tools.bkt_buy(x_symbol, 0, 0, ratio[0])

        self.godhandlog['positions']['{},{}'.format(str(x_ticket),str(y_ticket))] = godhandlog_open('short_spread',
                                                                                i_date,
                                                                                y_ticket,
                                                                                float(y_price),
                                                                                y_volume,
                                                                                x_ticket,
                                                                                float(x_price),
                                                                                x_volume,
                                                                                'open', i
                                                                                )
        #openpositions.append('{},{}'.format(str(x_ticket), str(y_ticket)))

        self.godhandlog['positions']['{},{}'.format(str(x_ticket),str(y_ticket))]['y_type'] = 'sell'
        self.godhandlog['positions']['{},{}'.format(str(x_ticket),str(y_ticket))]['x_type'] = 'buy'

        
        return {'key':'{},{}'.format(str(x_ticket), str(y_ticket)),
                'x_price':x_price,
                'y_price':y_price,
                'x_volume':x_volume,
                'y_volume':y_volume}

    def long_spread(self, x_symbol, y_symbol, position_size, ratio, i, i_date):

        y_ticket, y_price, y_volume = self.tools.bkt_buy(y_symbol, 0, 0, ratio[1])
        x_ticket, x_price, x_volume = self.tools.bkt_sell(x_symbol, 0, 0, ratio[0])

        self.godhandlog['positions']['{},{}'.format(str(x_ticket),str(y_ticket))] = godhandlog_open('long_spread',
                                                                                i_date,
                                                                                y_ticket,
                                                                                float(y_price),
                                                                                y_volume,
                                                                                x_ticket,
                                                                                float(x_price),
                                                                                x_volume,
                                                                                'open',
                                                                                i
                                                                                )
        self.godhandlog['positions']['{},{}'.format(str(x_ticket),str(y_ticket))]['y_type'] = 'buy'
        self.godhandlog['positions']['{},{}'.format(str(x_ticket),str(y_ticket))]['x_type'] = 'sell'
        self.godhandlog['positions']['{},{}'.format(str(x_ticket),str(y_ticket))]['y_type'] = 'buy'
        
        return {'key':'{},{}'.format(str(x_ticket), str(y_ticket)), 
                'x_price':x_price,
                'y_price':y_price,
                'x_volume':x_volume,
                'y_volume':y_volume}


    def close_position(self, position_ticket, _x, _y, _i, c_date):
        
        x_ticket, y_ticket = position_ticket.split(',')
        x_close_data = self.tools.bkt_close(x_ticket, _x, _i).copy()
        y_close_data = self.tools.bkt_close(y_ticket, _y, _i).copy()

        _expo = 0
        _lucro = 0

        y_volume = y_close_data[2]
        x_volume = x_close_data[2]

        self.godhandlog['positions'][position_ticket]['status'] = 'null'
        self.godhandlog['positions'][position_ticket]['time'][1] = c_date
        #volume ?

        self.godhandlog['positions'][position_ticket]['y_price'][1] = y_close_data[1]
        self.godhandlog['positions'][position_ticket]['x_price'][1] = x_close_data[1]

        if self.godhandlog['positions'][position_ticket]['type'] == 'long_spread':

            x_lucro = (self.godhandlog['positions'][position_ticket]['x_price'][0] - self.godhandlog['positions'][position_ticket]['x_price'][1])*x_volume
            y_lucro = (self.godhandlog['positions'][position_ticket]['y_price'][1] - self.godhandlog['positions'][position_ticket]['y_price'][0])*y_volume
            

            _lucro = x_lucro+y_lucro
            
            self.godhandlog['positions'][position_ticket]['lucro'] = _lucro


        if self.godhandlog['positions'][position_ticket]['type'] == 'short_spread':

            x_lucro = (self.godhandlog['positions'][position_ticket]['x_price'][1] - self.godhandlog['positions'][position_ticket]['x_price'][0])*x_volume
            y_lucro = (self.godhandlog['positions'][position_ticket]['y_price'][0] - self.godhandlog['positions'][position_ticket]['y_price'][1])*y_volume
            
            _lucro = x_lucro+y_lucro

            self.godhandlog['positions'][position_ticket]['lucro'] = _lucro

        if x_close_data[0] == 1 and y_close_data[0] == 1:

            self.godhandlog['positions'][position_ticket]['status'] = 'close'
            self.godhandlog['positions'][position_ticket]['i'][1]= _i

        self.godhandlog['positions_list'].append(self.godhandlog['positions'][position_ticket])
        
        return [x_close_data[0], y_close_data[0], _expo, _lucro]
    
    def m_movel(period, data):

        #data_r = bkt_godhand._reverse(data)
        data_r = list(data).copy()

        data_r.reverse()
        data_r = data_r[0:int(period)]

        return np.array(data_r)
    
    def getspread(x_period, y_period):

        spread = x_period/y_period
        spread = np.nan_to_num(spread)

        

            
        spread_z = (spread - spread.mean()) / np.std(spread)
        spread_today = spread_z[-1]
        
        return spread_today
    
    def roundlot(x_price, y_price, lot):
    
        x_buy = 1
        y_buy = 1


        x_ratio = x_price/y_price
        y_ratio = y_price/x_price


        if(x_ratio > 1):
            x_buy = round(y_ratio, 1)*lot
            y_buy = lot
            return x_buy, y_buy

        if(y_ratio > 1):
            y_buy = round(x_ratio, 1)*lot
            x_buy = lot
            return x_buy, y_buy

        if(x_buy < 100):
            x_buy = 100
        if(y_buy < 100):
            y_buy = 100

        return x_buy, y_buy