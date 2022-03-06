'''
period: periodo da média movel





'''




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
                    y_ticket,
                    y_price,
                    y_volume,
                    x_ticket,
                    x_price,
                    x_volume,

                    status,
                    i):

    position_log = {'type':_type,
                    'x_type':str(),
                    'y_type':str(),
                    'y_ticket':y_ticket,
                    'df_y':None,
                    'df_x':None,
                    'df_yprice':[float(), float()],
                    'df_xprice':[float(), float()],
                    'y_volume':y_volume,
                    'x_ticket':x_ticket,
                    'x_volume':x_volume,
                    'status':'open',
                    'count':int(),
                    'profit':float(),  #abertura, fechamento
                    'x_profit':float(),
                    'y_profit':float(),
                    'df_iteration':[int(), int()],
                    'df_date':[None, None]}

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
                       stop_number,
                       min_count,
                       tp_long,
                       tp_short,
                       period,
                       treino=False,
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


        df_index = df_x.index
        df_iteration = 0
        

        ###
        
        
        self.godhandlog['info'] = {'x_symbol': independent_ticker,
                              'y_symbol': dependent_ticker,
                              'short_spread':short_spread,
                              'long_spread':long_spread,
                              'position_size':position_size,
                              'stop_number':stop_number,
                              'tp_short':tp_short,
                              'tp_long':tp_long,
                              'min_count':min_count,
                              'period':period,
                              'days':None, 
                              'date':[str(df_x.index[0]), str(df_x.index[-1])],
                              'std_returns':None,
                              'std_profit':None
                              }

        # initializing loop counter
        df_size = len(df_x[column])

        self.godhandlog['spread'] = []
        i_list = []

        count = 0 # contador de periodos - inicia 


        for df_iteration in range(len(df_index)): # da pra melhorar isso aqui


            i_list.append(df_iteration)
            date = df_index[df_iteration]
            date_timestamp = df_index[df_iteration]
            endtime = (date_timestamp.hour == 16 and date_timestamp.minute >= 50)
            #endtime = False
            
            
            canTrade = True

            symbol_x['df_iteration'] = df_iteration
            symbol_y['df_iteration'] = df_iteration

            current_y_price = self.tools.bkt_getprice(df_y, column, df_iteration)[0]
            current_x_price = self.tools.bkt_getprice(df_x, column, df_iteration)[0]

            self.godhandlog['price']['y_price'].append(current_y_price)
            self.godhandlog['price']['x_price'].append(current_x_price)
            self.godhandlog['price']['time'].append(date)

            

            returns = 0
            if len(self.godhandlog['price']['time']) >= period:

                

                #verifica se os valores estão é uma posição com valor zero
                if self.godhandlog['price']['x_price'][-1] == 0 or self.godhandlog['price']['y_price'][-1] == 0:
                    canTrade = False
                if len(self.godhandlog['spread']) == 0:
                    canTrade = False

                independent_period  = self.m_movel(period, self.godhandlog['price']['x_price'])
                dependent_period    = self.m_movel(period, self.godhandlog['price']['y_price'])

                #verifica se a ultima posição do dependent period e independent period vale zero (buga no calculo do)
                if(dependent_period[-1] == 0 or independent_period[-1] == 0):
                    spread_today = bkt_godhand.getspread(x_period = independent_period, y_period = dependent_period)
                    if(spread_today != 0):
                        self.godhandlog['spread'].append(spread_today)
                    continue
                
                
                spread_today = bkt_godhand.getspread(x_period = independent_period, y_period = dependent_period)

                curr_return = sum(self.godhandlog['returns'])

                ratiolot = bkt_godhand.roundlot2(current_x_price, current_y_price, position_size)

                if canTrade:

                    
                    
                    ###  SHORT SPREAD
                    if (spread_today > short_spread) and (position_open == False)  and df_iteration < len(df_index)-5:
                        '''
                        operação de SHORT-SPREAD entra com short no ativo Y e com long no ativo X
                        _long_val vai armazenar o valor na posição long e _short_val vai armezenar
                        o valor no short
                        '''

                        short_data = self.short_spread(self, symbol_x, symbol_y, position_size, ratiolot, df_iteration, date_index=df_index)
                        
                        current_expo = short_data['x_price']*short_data['x_volume'] + short_data['y_price']*short_data['y_volume']
                        
                        #self.godhandlog['positions'][position_key]['df_x'] = df_x[df_iteration:min_count]
                        #self.godhandlog['positions'][position_key]['df_y'] = df_y[df_iteration:min_count]
                        
                        self.godhandlog['rawlog']['df_x'] = df_x
                        self.godhandlog['rawlog']['df_y'] = df_y


                        position_key = str(short_data['key'])
                        self.godhandlog['positions'][position_key]['df_iteration'][0] = df_iteration
                        self.godhandlog['positions'][position_key]['df_x'] = df_x
                        self.godhandlog['positions'][position_key]['df_y'] = df_y
                        self.godhandlog['positions'][position_key]['df_yprice'][0] = self.godhandlog['positions'][position_key]['df_y']['close'][df_iteration]
                        self.godhandlog['positions'][position_key]['df_xprice'][0] = self.godhandlog['positions'][position_key]['df_x']['close'][df_iteration]
                        self.godhandlog['positions'][position_key]['df_date'][0] = df_index[df_iteration]


                        position_open = True
                        count = 0 # zera contagem quando abre short-spread '5279b846,19c1188e'
        
                    
                    ### LONG SPREAD
                    elif (spread_today < long_spread) and (position_open == False)  and df_iteration < len(df_index)-5:

                        '''
                        operação de LONG-SPREAD entra com long no ativo Y e com short no ativo X
                        _long_val vai armazenar o valor na posição long e _short_val vai armezenar
                        o valor no short
                        '''

                        long_data = self.long_spread(self, symbol_x, symbol_y, position_size, ratiolot, df_iteration, date_index=df_index)
                        current_expo = long_data['x_price']*long_data['x_volume'] + long_data['y_price']*long_data['y_volume']

                        position_key = str(long_data['key']) #colocar um discriminante de quantidade de posições
                        self.godhandlog['positions'][position_key]['df_iteration'][0] = df_iteration
                        self.godhandlog['positions'][position_key]['df_x'] = df_x
                        self.godhandlog['positions'][position_key]['df_y'] = df_y
                        self.godhandlog['positions'][position_key]['df_yprice'][0] = self.godhandlog['positions'][position_key]['df_y']['close'][df_iteration]
                        self.godhandlog['positions'][position_key]['df_xprice'][0] = self.godhandlog['positions'][position_key]['df_x']['close'][df_iteration]
                        self.godhandlog['positions'][position_key]['df_date'][0] = df_index[df_iteration]

                        position_open = True
                        count = 0 # zera contagem quando abre long-spread


                    ### CLOSE POSITION
                    
                    force_close = False
                    if df_iteration >= (df_size-5):
                        force_close = True

                    #if (position_open == True and count >= min_count) or (force_close==True and (position_key=='long_spread' or position_key == 'short_spread')):
                    
                    #if (position_open == True and count >= min_count):
                    if (position_open == True):
                        if(self.godhandlog['positions'][position_key]['type'] == 'long_spread'):

                            '''
                            A logica de bater a porcentagem teria de ser implementada aqui''

                            -valor da cotação atual dos ativos x,y
                            -volume de cada um dos ativos
                            -calcula exposição
                            -verifica se satisfaz a condição de stop loss ou take profit
                            
                            
                            '''
                              
                            if(bkt_godhand.stopvalue(self.godhandlog['positions'][position_key]['df_xprice'][0],
                                                    self.godhandlog['positions'][position_key]['df_yprice'][0],
                                                    current_x_price,
                                                    current_y_price,
                                                    self.godhandlog['positions'][position_key]['x_volume'],
                                                    self.godhandlog['positions'][position_key]['y_volume'],
                                                    'long_spread', current_expo) == True and treino == False):
                                force_close = True
                            

                            if ((spread_today >= tp_long) and count >= min_count) or force_close == True:
                            #if ((curr_return >= tp_return) or (spread_today >= tp_long)):
  
                                #fecha posição
                                _a, _b, _c, _d = self.close_position(self, position_key, _x = df_x, _y = df_y, _i = df_iteration, c_date = date, _count=count, date_index=df_index)
                                returns = _d
                                self.godhandlog['positions'][position_key]['df_date'][1] = df_index[df_iteration]
                                self.godhandlog['positions'][position_key]['df_iteration'][1] = df_iteration
                                position_open=False
                                #force_close = False
                                position_key = 'empty'
                                self.godhandlog['expo'].append(current_expo)
                                self.godhandlog['returns'].append(returns)
                                count = 0 # zera contagem quando fecha posição 
                                
                                
                                if((len(self.godhandlog['returns']) >= stop_number)) or force_close == True:
                                #if(True):
                                    net_profit = 0
                                    for pos in self.godhandlog['positions_list']:
                                        net_profit += pos['profit']
                                        self.godhandlog['profit'] = net_profit
                                    
                                    
                                    self.godhandlog['info']['returns'] = self.godhandlog['returns']
                                    #self.godhandlog['info']['days'] = (dataframe_date[i+1] - dataframe_date[i+1]).days
                                    return self.godhandlog 

                        elif(self.godhandlog['positions'][position_key]['type'] == 'short_spread'):
                        
                            '''
                            A logica de bater a porcentagem teria de ser implementada aqui''

                            -valor da cotação atual dos ativos x,y
                            -volume de cada um dos ativos
                            -calcula exposição
                            -verifica se satisfaz a condição de stop loss ou take profit
                            '''

                            if(bkt_godhand.stopvalue(self.godhandlog['positions'][position_key]['df_xprice'][0],
                                                    self.godhandlog['positions'][position_key]['df_yprice'][0],
                                                    current_x_price,
                                                    current_y_price,
                                                    self.godhandlog['positions'][position_key]['x_volume'],
                                                    self.godhandlog['positions'][position_key]['y_volume'],
                                                    'short_spread', current_expo) == True and treino == False):
                            
                                force_close = True

                                #|->basicamente verifica as saidas do long&short|      -> and verifica se as iterações feitas pelo program são maiores que o 'df_iteration' | caso contrario o programa força a finalização |
                            if ((spread_today <= (tp_short)) and count >= min_count) or force_close==True:

                                #fecha posição
                                _a, _b, _c, _d = self.close_position(self, position_key, _x = df_x, _y = df_y, _i = df_iteration, c_date = date, _count=count, date_index=df_index)
                                returns = _d
                                self.godhandlog['positions'][position_key]['df_date'][1] = df_index[df_iteration-1]
                                self.godhandlog['positions'][position_key]['df_iteration'][1] = df_iteration-1
                                position_open=False
                                #force_close = False
                                position_key = 'empty'
                                self.godhandlog['expo'].append(current_expo)
                                self.godhandlog['returns'].append(returns)
                                count = 0 # zera contagem quando fecha posição

                                if((len(self.godhandlog['returns']) >= stop_number)) or force_close == True:   
                                #if(True):
                                    net_profit = 0
                                    for pos in self.godhandlog['positions_list']:
                                        net_profit += pos['profit']
                                        self.godhandlog['profit'] = net_profit
                                    

                                    
                                    
                                    self.godhandlog['info']['returns'] = self.godhandlog['returns']
                                    #self.godhandlog['info']['days'] = (dataframe_date[i+1] - dataframe_date[).days
                                    return self.godhandlog 
                        
                        count += 1
                        
                
                self.godhandlog['loop']['returns'].append(returns)
                self.godhandlog['spread'].append(spread_today)

                net_profit = 0
                for pos in self.godhandlog['positions_list']:
                    net_profit += pos['profit']

                self.godhandlog['profit'] = net_profit
  
                self.godhandlog['df_iteration'] = df_iteration
            
            df_iteration += 1
            #count += 1

        self.godhandlog['info']['df_x'] = df_x
        self.godhandlog['info']['df_y'] = df_y
        self.godhandlog['info']['days'] = 10
        self.godhandlog['info']['std_returns'] = np.std(self.godhandlog['loop']['returns'])
        self.godhandlog['info']['std_profit'] = np.std(np.cumsum(self.godhandlog['loop']['returns']))
        

        try:
            _expo = self.godhandlog['expo']
            _sum_return = sum(self.godhandlog['loop']['returns'])
            _roi = _sum_return/_expo
        except:
            _roi = 0
            _expo = 0
        
        self.godhandlog['info']['roi'] = _roi
        self.godhandlog['info']['expo'] = _expo
        


        return self.godhandlog
    

    def short_spread(self, x_symbol, y_symbol, position_size, ratio, i, date_index):

        

        y_ticket, y_price, y_volume = self.tools.bkt_sell(y_symbol, 0, 0, ratio[1])
        x_ticket, x_price, x_volume = self.tools.bkt_buy(x_symbol, 0, 0, ratio[0])

        self.godhandlog['positions']['{},{}'.format(str(x_ticket),str(y_ticket))] = godhandlog_open('short_spread',
                                                                                y_ticket,
                                                                                float(y_price),
                                                                                y_volume,
                                                                                x_ticket,
                                                                                float(x_price),
                                                                                x_volume,
                                                                                'open', i, 

                                                                                )
        #openpositions.append('{},{}'.format(str(x_ticket), str(y_ticket)))
        self.godhandlog['positions']['{},{}'.format(str(x_ticket),str(y_ticket))]['df_iteration'][0] = i
        self.godhandlog['positions']['{},{}'.format(str(x_ticket),str(y_ticket))]['y_type'] = 'sell'
        self.godhandlog['positions']['{},{}'.format(str(x_ticket),str(y_ticket))]['x_type'] = 'buy'
        
        return {'key':'{},{}'.format(str(x_ticket), str(y_ticket)),
                'x_price':x_price,
                'y_price':y_price,
                'x_volume':x_volume,
                'y_volume':y_volume}

    def long_spread(self, x_symbol, y_symbol, position_size, ratio, i, date_index):

        y_ticket, y_price, y_volume = self.tools.bkt_buy(y_symbol, 0, 0, ratio[1])
        x_ticket, x_price, x_volume = self.tools.bkt_sell(x_symbol, 0, 0, ratio[0])

        self.godhandlog['positions']['{},{}'.format(str(x_ticket),str(y_ticket))] = godhandlog_open('long_spread',
                                                                                y_ticket,
                                                                                float(y_price),
                                                                                y_volume,
                                                                                x_ticket,
                                                                                float(x_price),
                                                                                x_volume,
                                                                                'open',
                                                                                i)

        self.godhandlog['positions']['{},{}'.format(str(x_ticket),str(y_ticket))]['df_iteration'][0] = i
        self.godhandlog['positions']['{},{}'.format(str(x_ticket),str(y_ticket))]['x_type'] = 'sell'
        self.godhandlog['positions']['{},{}'.format(str(x_ticket),str(y_ticket))]['y_type'] = 'buy'

        return {'key':'{},{}'.format(str(x_ticket), str(y_ticket)),
                'x_price':x_price,
                'y_price':y_price,
                'x_volume':x_volume,
                'y_volume':y_volume}


    def close_position(self, position_ticket, _x, _y, _i, c_date, _count, date_index):
        
        x_ticket, y_ticket = position_ticket.split(',')
        x_close_data = self.tools.bkt_close(x_ticket, _x, _i).copy()
        y_close_data = self.tools.bkt_close(y_ticket, _y, _i).copy()

        _expo = 0
        _profit = 0

        y_volume = int(y_close_data[2])
        x_volume = int(x_close_data[2])
        
        self.godhandlog['positions'][position_ticket]['status'] = 'null'
        self.godhandlog['positions'][position_ticket]['count'] = _count
        #volume ?

        self.godhandlog['positions'][position_ticket]['df_yprice'][1] = y_close_data[1]
        self.godhandlog['positions'][position_ticket]['df_xprice'][1] = x_close_data[1]


        ### LONG SPREAD

        if self.godhandlog['positions'][position_ticket]['type'] == 'long_spread':
            
              
            _curr_price_x = x_close_data[1]
            _curr_price_y = y_close_data[1]

            self.godhandlog['positions'][position_ticket]['df_xprice'][1] = _curr_price_x
            self.godhandlog['positions'][position_ticket]['df_yprice'][1] = _curr_price_y

            _opened_price_x = self.godhandlog['positions'][position_ticket]['df_xprice'][0]
            _opened_price_y = self.godhandlog['positions'][position_ticket]['df_yprice'][0]
            
            #short x, long y
            _profit_x = (_opened_price_x - _curr_price_x)*x_volume
            _profit_y = (_curr_price_y - _opened_price_y)*y_volume

            _profit = _profit_x + _profit_y

            self.godhandlog['positions'][position_ticket]['x_profit'] = _profit_x
            self.godhandlog['positions'][position_ticket]['y_profit'] = _profit_y
            self.godhandlog['positions'][position_ticket]['profit'] = _profit



        ###SHORT SPREAD

        if self.godhandlog['positions'][position_ticket]['type'] == 'short_spread':
            
            _curr_price_x = x_close_data[1]
            _curr_price_y = y_close_data[1]

            self.godhandlog['positions'][position_ticket]['df_xprice'][1] = _curr_price_x
            self.godhandlog['positions'][position_ticket]['df_yprice'][1] = _curr_price_y

            _opened_price_x = self.godhandlog['positions'][position_ticket]['df_xprice'][0]
            _opened_price_y = self.godhandlog['positions'][position_ticket]['df_yprice'][0]

            #long x, short y
            _profit_x = (_curr_price_x - _opened_price_x)*x_volume
            _profit_y = (_opened_price_y - _curr_price_y)*y_volume

            _profit = _profit_x + _profit_y

            self.godhandlog['positions'][position_ticket]['x_profit'] = _profit_x
            self.godhandlog['positions'][position_ticket]['y_profit'] = _profit_y
            self.godhandlog['positions'][position_ticket]['profit'] = _profit

        if x_close_data[0] == 1 and y_close_data[0] == 1:

            self.godhandlog['positions'][position_ticket]['status'] = 'close'
            self.godhandlog['positions'][position_ticket]['df_iteration'][1] = _i
            #self.godhandlog['positions'][position_ticket]['data_index'][1]= str(date_index[_i])


        self.godhandlog['positions_list'].append(self.godhandlog['positions'][position_ticket])
        
        return [x_close_data[0], y_close_data[0], _expo, _profit]
    
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

    def roundlot2(x_price, y_price, lot=10000):
        
        try:
            alpha = lot/(2*x_price)
        except:
            alpha = 100
        
        try:
            beta = lot/(2*y_price)
        except:
            beta = 100
        
        try:
            x_buy = int(math.ceil(alpha / 100.0)) * 100
        except:
            x_buy = 100
        try: 
            y_buy = int(math.ceil(beta / 100.0)) * 100 
        except:
            y_buy = 100

        if(x_buy < 100):
            x_buy = 100
        if(y_buy < 100):
            y_buy = 100

        return x_buy, y_buy
    
    def stopvalue(df_xprice, df_yprice, curr_xprice, curr_yprice, x_volume, y_volume, type, expo,tp=0.025, sl=-0.01, tp_n=3000, sl_n=-1000):

        
        if(type == 'long_spread'):
            _lucro = 0
            _lucro_x = (df_xprice - curr_xprice)*x_volume
            _lucro_y = (curr_yprice - df_yprice)*y_volume
            _lucro = _lucro_x + _lucro_y
            expo = df_yprice*y_volume + df_xprice*x_volume
            percentage = _lucro/expo

            if(percentage >= tp and percentage != 0):
                return True
            if(percentage <= sl and percentage != 0):
                return True
            
            return False

        if(type == 'short_spread'):
            _lucro = 0
            _lucro_x = (-df_xprice + curr_xprice)*x_volume
            _lucro_y = (-curr_yprice + df_yprice)*y_volume
            _lucro = _lucro_x + _lucro_y
            expo = df_yprice*y_volume + df_xprice*x_volume
            percentage = _lucro/expo

            if(percentage >= tp and percentage != 0):
                return True
            if(percentage <= sl and percentage != 0):
                return True
            
            return False
    
    def max_all(iterable):
        
        max_value = 0
        if type(iterable) != list():
            max_value = iterable
            return max_value
            
        for num in iterable:
            if(num > max_value):
                max_value = num

        return max_values
