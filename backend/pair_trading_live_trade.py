# -*- coding: utf-8 -*-

'''

Sobre o bug, ele acontece da seguinte forma: O programa abre uma posição numa ação X, depois 
ele abre novamente uma posição na mesma ação X. Por exemplo 
1 - buy 100 X
2 - buy 100 X

agora eu tenho 200 X

ai quando ele vai fechar uma das posiçõa 1 ou 2 ele na verdade fecha a 200 X. E quando isso 
acontece eu armazeno o valor no price, ele pega o do ultimo valor retornado pelo server.



Também pode ser um problema no log do mt5_tools. 
'''

# IMPORTS
##############################################################################
import pandas as pd
import statsmodels.formula.api as smf
import numpy as np
from numpy import log

import json

from datetime import datetime
from mt5_tools import mt5_currentprice
import time
import math

from mt5_tools import mt5_buy
from mt5_tools import mt5_sell
from mt5_tools import mt5_close

from datetime import datetime


def godhandlog_start():
    
    godhandlog = {'price':{'y_price':[], 'x_price':[], 'time':[]},
              'spread':[],
              'profit':[],
              'cumprofit':[],
              'info':{},
              'returns':[],
              'stop_count':int(0),
              'positions':{},
              'indicators':{},
              'max_profit':[],
              'rawlog':{},
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
    df = pd.DataFrame(_dict)
    df.to_json(name)

class god_hand_live():

    def __init__(self, dependent_ticker,
                       independent_ticker,
                       f_name,
                       short_spread,
                       long_spread,
                       position_size,
                       stop_return,
                       stop_number,
                       tp_long,
                       tp_short,
                       tp_return,
                       period):


        #np.arange()
        openpositions = []
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
                              'date':[str(datetime.now()), None)]}
        


        # initializing loop counter
        loop_counter = 0

        print("#"*70)
        print("\n")
        canTrade = True
        
        while (canTrade):

            if(datetime.now().hour > 17):
                canTrade = False
                break
            print("loop number: {} | current time: {} | dtime: {}".format(
                loop_counter, str(datetime.now()), self.dtime()))

            time.sleep(self.dtime())
            #time.sleep(1)


            '''
            possivel problema por utilizar a posição [0] no currentprice, checar isso depois
            '''

        
            godhandlog['price']['y_price'].append(mt5_currentprice(dependent_ticker)[0])
            godhandlog['price']['x_price'].append(mt5_currentprice(independent_ticker)[0])
            godhandlog['price']['time'].append(str(datetime.now()))



            if len(godhandlog['price']['time']) >= period:


                # notifying that len(godhandlog['price']['time']) >= period

                print("-"*70)







                # SPREAD CALC
                ###########################
                independent_period  = self.m_movel(period, godhandlog['price']['x_price'])
                dependent_period    = self.m_movel(period, godhandlog['price']['y_price'])

                spread = independent_period/dependent_period
                precise_ratio = spread[-1]
                spread_z = self.zscore(spread)

                
                ###########################






                # verifying spread, ratio and zscore
                print("independent_period   = {}".format(independent_period))
                print("dependent_period     = {}".format(dependent_period))
                print("spread = {} | period length = {}".format(spread, period))
                print("precise_ratio(spread[-1]) = {}".format(precise_ratio))
                print("zscore(spread) = {}".format(spread_z))
                print("spread_today(zscore(spread)[-1]) = {} | long spread = {} | short spread = {}".format(
                    spread_today, long_spread, short_spread))
                print("-"*70)

                print("\n")


                print("spread_today: {}; time: {}; expo: {}".format(spread_today, str(datetime.now()), self.expo_value(expodict)))


                print("-"*70)
                print("Volumes:")
                print("\n")
                print("precise_ratio = {}".format(precise_ratio))
                print("self.roundup(precise_ratio*position_size, multiplo) = {}".format(self.roundup(precise_ratio*position_size, multiplo)))
                print("-"*70)
                
                
                

                #opening position

# short spreading ----------------------------------------------------------------------------------------------------------
                if (spread_today > short_spread) and (len(openpositions) < 1):

                    print("ENTERED SHORT SPREAD!")

                    '''
                    operação de short spread entra com short no ativo Y e com long no ativo X
                    _long_val vai armazenar o valor na posição long e _short_val vai armezenar
                    o valor no short

                    '''

                    _short_val = mt5_currentprice(dependent_ticker)[0]*position_size
                    _long_val = mt5_currentprice(independent_ticker)[1]*self.roundup(precise_ratio*position_size, multiplo)

                    short_data = self.short_spread(dependent_ticker, independent_ticker, position_size, precise_ratio, multiplo)
                    openpositions.append(str(short_data['key']))


#----------------------------------------------------------------------------------------------------------------------------


# long spreading-------------------------------------------------------------------------------------------------------------
                if (spread_today < long_spread) and (len(openpositions) < 1):

                    print("ENTERED LONG SPREAD!")

                    '''
                    operação de long spread entra com long no ativo Y e com short no ativo X
                    _long_val vai armazenar o valor na posição long e _short_val vai armezenar
                    o valor no short
                    '''

                    _long_val = mt5_currentprice(dependent_ticker)[0]*position_size
                    _short_val = mt5_currentprice(independent_ticker)[1]*self.roundup(precise_ratio*position_size, multiplo)

                    long_data = self.long_spread(dependent_ticker, independent_ticker, position_size, precise_ratio, multiplo)
                    openpositions.append(str(long_data['key']))


#----------------------------------------------------------------------------------------------------------------------------


                print("-"*70)
                print('\n')




                # closing positions
                print("CLOSING POSITIONS!")

                lucro = 0

                for i in openpositions:


                    #long spread
                    if(godhandlog[i]['type'] == 'long_spread'):

                        if (spread_today > (-stop_gain)) or (spread_today < (-stop_loss)):

                            #fecha posição
                            _a, _b, _c, _d = self.close_position(i)
                            lucro = _d


                            print("Long Spread: {} | spread_today = {} | stop gain = {} | stop loss = {} | lucro = {}".format(
                                i, spread_today, -stop_gain, -stop_loss, _d))

                            openpositions.remove(i)
                            if(_a == 0 or _b == 0):
                                print('LONG SPREAD ERROR [{},{}]'.format( _a,_b))


                    #short_spread
                    if(godhandlog[i]['type'] == 'short_spread'):

                        if (spread_today < (stop_gain)) or (spread_today > (stop_loss)):

                            #fecha posição
                            _a, _b, _c, _d = self.close_position(i)
                            lucro = _d

                            print("Short Spread: {} | spread_today = {} | stop gain = {} | stop loss = {} | lucro = {}".format(
                                i, spread_today, stop_gain, stop_loss, _d))

                            openpositions.remove(i)
                            if(_a == 0 or _b == 0):
                                print('SHORT SPREAD ERROR [{},{}]'.format( _a,_b))


                godhandlog['seriesprofit'].append(lucro)
                godhandlog['spread'].append(spread_today)
                godhandlog['cumprofit'].append(sum(godhandlog['profit']))



            _f = open(f_name, 'w')
            _f = json.dump(godhandlog, _f)

            #run(dash_plot(godhandlog))

            #colocar o plot aqui

##############################################################################




# UTILITIES FUNCS
##############################################################################
    def m_movel(self, period, data):

        data_r = self._reverse(data)
        data_r = data_r[0:period]

        return np.array(data_r)

    def dtime(self):
        return (60 - datetime.now().time().second)

    def _reverse(self, lst):
        lst.reverse()
        return lst

    # z-score function:
    def zscore(self, series):
        return (series - series.mean()) / np.std(series)

    def roundup(self, x, m):
        return int(math.ceil(x / m)) * m

    def expo_value(self, dic):

        val = dic.values()
        total = sum(val)

        return total
    

##############################################################################




# VERY IMPORTANT FUNCS
##############################################################################
    def short_spread(self, y_symbol, x_symbol, position_size, ratio, multiplo):

        y_ticket, y_price, y_volume = mt5_sell(y_symbol, 0, 0, position_size)
        x_ticket, x_price, x_volume = mt5_buy(x_symbol, 0, 0, self.roundup(ratio*position_size, multiplo))

        godhandlog['{},{}'.format(str(x_ticket),str(y_ticket))] = godhandlog_open('short_spread',
                                                                                  y_ticket,
                                                                                  float(y_price),
                                                                                  y_volume,
                                                                                  x_ticket,
                                                                                  float(x_price),
                                                                                  x_volume,
                                                                                  'open'
                                                                                  )
        #openpositions.append('{},{}'.format(str(x_ticket), str(y_ticket)))

        return {'key':'{},{}'.format(str(x_ticket), str(y_ticket)), 
                'x_price':x_price,
                'y_price':y_price,
                'x_volume':x_volume,
                'y_volume':y_volume}

    def long_spread(self, y_symbol, x_symbol, position_size, ratio, multiplo):

        y_ticket, y_price, y_volume = mt5_buy(y_symbol, 0, 0, position_size)
        x_ticket, x_price, x_volume = mt5_sell(x_symbol, 0, 0, self.roundup(ratio*position_size, multiplo))

        godhandlog['{},{}'.format(str(x_ticket),str(y_ticket))] = godhandlog_open('long_spread',
                                                                                  y_ticket,
                                                                                  float(y_price),
                                                                                  y_volume,
                                                                                  x_ticket,
                                                                                  float(x_price),
                                                                                  x_volume,
                                                                                  'open'
                                                                                  )

        #openpositions.append('{},{}'.format(str(x_ticket), str(y_ticket)))

        return {'key':'{},{}'.format(str(x_ticket), str(y_ticket)), 
                'x_price':x_price,
                'y_price':y_price,
                'x_volume':x_volume,
                'y_volume':y_volume}


    def close_position(self, position_ticket):

        x_ticket, y_ticket = position_ticket.split(',')

        x_close_data = mt5_close(x_ticket).copy()
        y_close_data = mt5_close(y_ticket).copy()


        _expo = 0
        _lucro = 0

        y_volume = y_close_data[2]
        x_volume = x_close_data[2]

        godhandlog[position_ticket]['status'] = 'null'
        godhandlog[position_ticket]['time'][1] = str(datetime.now())
        #volume ?

        godhandlog[position_ticket]['y_price'][1] = y_close_data[1]
        godhandlog[position_ticket]['x_price'][1] = x_close_data[1]

        if godhandlog[position_ticket]['type'] == 'long_spread':

            x_lucro = (godhandlog[position_ticket]['x_price'][0] - godhandlog[position_ticket]['x_price'][1])*x_volume
            y_lucro = (godhandlog[position_ticket]['y_price'][1] - godhandlog[position_ticket]['y_price'][0])*y_volume
            

            _lucro = x_lucro+y_lucro
            
            godhandlog[position_ticket]['lucro'] = _lucro

            godhandlog['profit'].append(_lucro)



        if godhandlog[position_ticket]['type'] == 'short_spread':

            x_lucro = (godhandlog[position_ticket]['x_price'][1] - godhandlog[position_ticket]['x_price'][0])*x_volume
            y_lucro = (godhandlog[position_ticket]['y_price'][0] - godhandlog[position_ticket]['y_price'][1])*y_volume
            
            _lucro = x_lucro+y_lucro

            godhandlog[position_ticket]['lucro'] = _lucro
            godhandlog['profit'].append(_lucro)



        if x_close_data[0] == 1 and y_close_data[0] == 1:

            godhandlog[position_ticket]['status'] = 'close'



        #openpositions.remove('{},{}'.format(str(x_ticket), str(y_ticket)))
        return [x_close_data[0], y_close_data[0], _expo, _lucro]
##############################################################################
