import pandas as pd
import numpy as np
import statsmodels.formula.api as smf

import json

from datetime import datetime
import time
import math

from backend.mt5_tools import mt5_currentprice
from backend.mt5_tools import mt5_buy
from backend.mt5_tools import mt5_sell
from backend.mt5_tools import mt5_close
from backend.mt5_tools import mt5_singlehistoricaldata
from backend.mt5_tools import mt5_lastdata

from secrets import token_hex as token

def godhandlog_start():
    
    godhandlog = {'price':{'y_price':[], 'x_price':[], 'time':[]},
              'spread':[],
              'profit':[],
              'cumprofit':[],
              'info':{},
              'returns':[],
              'stop_count':int(0),
              'positions':{},
              'positions_list':[],
              'indicators':{},
              'max_profit':[],
              'rawlog':{},
              'Long':[],
              'Short':[],
              'precise_ratio_x':[],
              'precise_ratio_y':[],
              'loop':{'returns':[]}}

    return godhandlog.copy()

def godhandlog_open(_type,
                    y_ticket,
                    y_price,
                    y_volume,
                    x_ticket,
                    x_price,
                    x_volume,
                    status):


    position_log = {'type':_type,
                    'time':[str(datetime.now()), None],
                    'y_ticket':y_ticket,
                    'y_price':[y_price, None],
                    'y_volume':y_volume,
                    'x_ticket':x_ticket,
                    'x_price':[x_price, None],
                    'x_volume':x_volume,
                    'status':'open',
                    'lucro':None}

    return position_log

def godhandlog_save(_dict, x_symbol, y_symbol, name):
    file = open(name, 'w')
    rd = json.dump(_dict, file)     
    
    

class fourteenbis_live():
        
    def __init__(self, independent_ticker,
                       dependent_ticker,
                       p_size,
                       period,
                       short_spread,
                       long_spread,
                       tp_short,
                       tp_long,
                       tp_return,
                       stop_number,
                       stop_return,
                       min_count,
                       timeframe=5,
                       connected_server='tcp://192.168.100.105:10000'
                       ):
                       
        f_name = '{}x{}_{}.json'.format(independent_ticker, dependent_ticker, token(4))
        x_ticker = independent_ticker
        y_ticker = dependent_ticker
        self.godhandlog = godhandlog_start()
        
        position_key = str
        
        self.godhandlog['info'] = {'x_symbol': x_ticker,
                              'y_symbol': y_ticker,
                              'short_spread':short_spread,
                              'long_spread':long_spread,
                              'position_size':p_size,
                              'stop_return':stop_return,
                              'stop_number':stop_number,
                              'tp_short':tp_short,
                              'tp_long':tp_long,
                              'period':period,
                              'min_count':min_count,
                              'date':[str(datetime.now()), None]}
        
        
        loop_counter = 0
        
        canTrade = True
        position_open = False
        force_close = False
        
        curr_positionkey = ''

        curr_long = 0
        curr_short = 0
        curr_profit = 0
        curr_roi = 0
        curr_expo = 0

        
        print('-'*50)
        
        x_pricelast = mt5_lastdata(x_ticker, timeframe, 0, period, SERVER=connected_server)
        y_pricelast = mt5_lastdata(y_ticker, timeframe, 0, period, SERVER=connected_server)
        
        print('{}'.format(x_pricelast))
        print('{}'.format(y_pricelast))

        
        print('-'*50)
        for i in range(len(y_pricelast)):
            self.godhandlog['price']['y_price'].append(y_pricelast['close'][i])
            self.godhandlog['price']['x_price'].append(x_pricelast['close'][i])
            self.godhandlog['price']['time'].append(str(y_pricelast['close'].index[i]))

        count = 0 #contagem de periodos - inicia

        while(canTrade):

            count = len(self.godhandlog['spread'])
            curr_min = datetime.now().hour*60 + datetime.now().minute

            while(curr_min <= 604):
                curr_min = datetime.now().hour*60 + datetime.now().minute
                print('market close ', str(datetime.now()), curr_min)
                time.sleep(10)

            while(curr_min > 1070):
                curr_min = datetime.now().hour*60 + datetime.now().minute
                print('--after market close--', str(datetime.now()), curr_min)
                time.sleep(10)

            time.sleep(self.dtime())   

            if(not(len(self.godhandlog['price']['time']) >= period)): 
                
                print("loop number: {} |current time: {} | dtime: {}".format(
                    loop_counter, str(datetime.now()), self.dtime()))
            
            if(datetime.now().minute%5 > 0):

                print('#',end='')
                continue
            print('\n')

            self.godhandlog['price']['y_price'].append(mt5_currentprice(y_ticker, connected_server)[1]) #ajustar isso aqui 0=bid e 1=ask
            self.godhandlog['price']['x_price'].append(mt5_currentprice(x_ticker, connected_server)[1])
            self.godhandlog['price']['time'].append(str(datetime.now()))
            
            
            returns = 0
            
            if(len(self.godhandlog['price']['time']) >= period):
                  
                #calculo de spread
                independent_period  = self.m_movel(period, self.godhandlog['price']['x_price'])
                dependent_period    = self.m_movel(period, self.godhandlog['price']['y_price'])
                
                precise_ratio_x, precise_ratio_y , spread_today = self.getspread(x_period=dependent_period, y_period=independent_period)

                self.godhandlog['precise_ratio_x'].append(precise_ratio_x)
                self.godhandlog['precise_ratio_y'].append(precise_ratio_y)
                
                precise_ratio = [precise_ratio_x, precise_ratio_y]
            
                current_x_price = mt5_currentprice(x_ticker, connected_server)
                current_y_price = mt5_currentprice(y_ticker, connected_server)

                ratiolot = self.roundlot2(current_x_price[0], current_y_price[0], p_size)

                curr_expo = np.mean(current_x_price[0]+current_x_price[1])*ratiolot[0] + np.mean(current_x_price[0]+current_x_price[1])*ratiolot[1]

                curr_profit = sum(self.godhandlog['returns'])
                curr_return = curr_profit
                
                try:
                    curr_roi = curr_profit/curr_expo
                except:
                    curr_roi = 0

                
                print('\n#####')    
                print('name_x : {} | name_y : {}'.format(x_ticker, y_ticker))
                print('spread : {}'.format(spread_today))
                print(self.godhandlog['info'])



                force_close = False
            
                if (position_open == False and curr_min < 1005):
                     
                    if(current_x_price[0] == 0):
                        current_x_price[0] = self.godhandlog['price']['x_price'][-2]
                    
                    if(current_y_price[0] == 0):
                        current_y_price[0] = self.godhandlog['price']['y_price'][-2]


                    ratiolot = self.roundlot2(current_x_price[0], current_y_price[0], p_size)

                    if((spread_today >= short_spread)):
                        '''
                        -short_spread -> long x, short y
                        -Aqui que se implementaria uma razão de compra diferente.
                        -curr_long pega os dados diretor do self.shortspread
                        '''

                        

                        #aqui tem problema. Será que preciso 
                        _short_val = current_x_price[0]*ratiolot[0]
                        _long_val = current_y_price[1]*ratiolot[1]

                       
                        print('short_data')
                        short_data = self.short_spread(y_ticker, x_ticker, p_size, ratiolot, connected_server)
                        print(short_data)
                        curr_long = short_data['y_price']*short_data['y_volume']
                        curr_short = short_data['x_price']*short_data['x_volume']
                        curr_positionkey = str(short_data['key'])

                        print('SHORT_SPREAD\ncurr_long : {} | curr_short : {}\ny_volume : {} | x_volume :{}'.format(curr_long, curr_short, short_data['y_volume'], short_data['x_volume']))

                        position_open = True


                        count = 0
                        
                    elif((spread_today <= long_spread)):
                        '''
                        -long_spread -> long y, short x
                        -Aqui que se implementaria uma razão de compra diferente.
                        -curr_long pega os dados diretor do self.shortspread
                        '''
                        _short_val = current_x_price[1]*ratiolot[0]
                        _long_val = current_y_price[0]*ratiolot[1]
                        print('long_data')
                        long_data = self.long_spread(y_ticker, x_ticker, p_size, ratiolot, connected_server)
                        print(long_data)

                        curr_long = long_data['x_price']*long_data['x_volume']
                        curr_short = long_data['y_price']*long_data['y_volume']
                        curr_positionkey = str(long_data['key'])

                        print('SHORT_SPREAD\ncurr_long : {} | curr_short : {}\ny_volume : {} | x_volume :{}'.format(curr_long, curr_short, long_data['y_volume'], long_data['x_volume']))

                        position_open = True
                        count = 0


                self.godhandlog['loop']['returns'].append(returns)
                self.godhandlog['spread'].append(spread_today)
                
                godhandlog_save(self.godhandlog, x_ticker, y_ticker, f_name)
                loop_counter += 1
            

            count += 1
                
                
        self.godhandlog['indicators']['profit'] = sum(self.godhandlog['returns'])
        self.godhandlog['info']['returns'] = self.godhandlog['returns']
        self.godhandlog['info']['date'][1] = str(datetime.now())
               
                    
    
    def short_spread(self, y_symbol, x_symbol, position_size, ratio, server):

            y_ticket, y_price, y_volume = mt5_sell(y_symbol, 0, 0, ratio[1], server)
            x_ticket, x_price, x_volume = mt5_buy(x_symbol, 0, 0, ratio[0], server)

            x_volume, y_volume = self.roundlot2(x_price, y_price, position_size)

            self.godhandlog['positions']['{},{}'.format(str(x_ticket),str(y_ticket))] = godhandlog_open('short_spread',
                                                                                        y_ticket,
                                                                                        float(y_price),
                                                                                        y_volume,
                                                                                        x_ticket,
                                                                                        float(x_price),
                                                                                        x_volume,
                                                                                        'open'
                                                                                        )
            #openpositions.append('{},{}'.format(str(x_ticket), str(y_ticket)))
            print({'key':'Buy : {}\n Sell: {}'.format(str(x_ticket), str(y_ticket)), 
                'x_volume':x_volume,
                'y_volume':y_volume,
                'x_price':x_price,
                'y_price':y_price,
                'type':'long_spread'
                })

            return {'key':'{},{}'.format(str(x_ticket), str(y_ticket)), 
                    'x_price':x_price,
                    'y_price':y_price,
                    'type':'short_spread',
                    'x_volume':x_volume,
                    'y_volume':y_volume}


    def long_spread(self, y_symbol, x_symbol, position_size, ratio, server):

        x_ticket, x_price, x_volume = mt5_sell(x_symbol, 0, 0, ratio[0], server)
        y_ticket, y_price, y_volume = mt5_buy(y_symbol, 0, 0,  ratio[1], server)
        
        x_volume, y_volume = self.roundlot2(x_price, y_price, position_size)


       

        self.godhandlog['positions']['{},{}'.format(str(x_ticket),str(y_ticket))] = godhandlog_open('long_spread',
                                                                                    y_ticket,
                                                                                    float(y_price),
                                                                                    y_volume,
                                                                                    x_ticket,
                                                                                    float(x_price),
                                                                                    x_volume,
                                                                                    'open'
                                                                                    )
        print({'key':'Sell : {}\n Buy: {}'.format(str(x_ticket), str(y_ticket)), 
                'x_volume':x_volume,
                'y_volume':y_volume,
                'x_price':x_price,
                'y_price':y_price,
                'type':'long_spread'
                })

        return {'key':'{},{}'.format(str(x_ticket), str(y_ticket)), 
                'x_price':x_price,
                'y_price':y_price,
                'type':'long_spread',
                'x_volume':x_volume,
                'y_volume':y_volume}

                    
    def m_movel(self, period, data):

        #data_r = bkt_godhand._reverse(data)
        data_r = list(data).copy()
        data_r.reverse()
        data_r = data_r[0:int(period)]

        return np.array(data_r)
           
    def getspread(self, x_period, y_period):
        
        spread = np.array(x_period)/np.array(y_period)
        spread = np.nan_to_num(spread)
        precise_ratio_y = 1
        precise_ratio_x = 1


        #precise_ratio = spread[-1]
        spread_z = (np.array(spread) - spread.mean()) / np.std(spread)
        spread_today = spread_z[-1]
        
  
        
        return precise_ratio_x, precise_ratio_y, spread_today
    
    def dtime(self):
        return ((60 - datetime.now().time().second) )

    def roundlot(self, x_price, y_price, lot=200):
    
        def roundup(x):
            return x if x % 100 == 0 else x + 100 - x % 100    

        x_buy = 1
        y_buy = 1

        try:
            x_ratio = x_price/y_price
            y_ratio = y_price/x_price
        except:
            x_ratio = 0
            y_ratio = 0

        if(x_ratio > 1):
            x_buy = round(y_ratio, 1)*lot
            y_buy = lot
        

        if(y_ratio > 1):
            y_buy = round(x_ratio, 1)*lot
            x_buy = lot
        
            
        return roundup(x_buy), roundup(y_buy)

    def roundlot2(self, x_price, y_price, lot):
        
        if(x_price == 0):
            x_price = 1
        if(y_price == 0):
            y_price = 1

        alpha = lot/(2*x_price)
        beta = lot/(2*y_price)

        x_buy = int(math.ceil(alpha / 100.0)) * 100
        y_buy = int(math.ceil(beta / 100.0)) * 100 

        if(x_buy < 100):
            x_buy = 100
        if(y_buy < 100):
            y_buy = 100

        return x_buy, y_buy



    def stopvalue(self, df_xprice, df_yprice, curr_xprice, curr_yprice, x_volume, y_volume, type, expo,tp=0.03, sl=-0.015):

        
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
