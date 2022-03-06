"""
Created on Wed Nov  4 18:47:01 2020

@author: zigoo
"""

import zmq
import pandas as pd
import datetime
import json

from secrets import token_hex as token

from datetime import datetime

from backend.resampler import resampler
import numpy as np

import concurrent.futures
import collections

from random import randrange
import random

# XP demo 25.72.107.101
# EvolveMarkets 25.36.199.79
#25.21.110.40

standard_server = 'tcp://192.168.100.106:10000'


log_dict = dict()
year, month, day = datetime.now().year, datetime.now().month, datetime.now().day

fname = 'contability_{}{}{}_{}.{}'.format(year, month, day, token(2),'json') 


def openLog(_type, _price, _volume, _symbol):

    ticket_dict = {'symbol':_symbol,
                   'type':_type,
                   'status':'open',
                   'time':[str(datetime.now()), None],
                   'price':[_price, None],
                   'volume':_volume,
                   'lucro':None
                   }


    return ticket_dict

def closeLog(_ticket, _price):


    log_dict[str(_ticket)]['status'] = 'close'
    log_dict[str(_ticket)]['time'][1] = str(datetime.now())
    log_dict[str(_ticket)]['price'][1] = _price

    if log_dict[_ticket]['type'] == 'long':
        log_dict[str(_ticket)]['lucro'] = (float(log_dict[str(_ticket)]['price'][1]) - float(log_dict[str(_ticket)]['price'][0]))
    if log_dict[_ticket]['type'] == 'short':
        log_dict[str(_ticket)]['lucro'] = (float(log_dict[str(_ticket)]['price'][0]) - float(log_dict[str(_ticket)]['price'][1]))

    return True


def savelog(_dict, name=fname):
    df = pd.DataFrame(_dict)
    df.to_json(name)


class mt5_currentprice:

    '''
    ticker :

        ticker da ação que tu quer pegar o bid, ask.

    exemplo:
    mt5_buy('LTCUSD', 0, 0, 5) -> compra 5 ltc
        retorna um codigo por exemplo 4567
    mt5_close('4567')
        fecha a posição.
    '''

    def __new__(self,
                ticker,
                SERVER=standard_server
                ):

        context = zmq.Context()
        reqSocket = context.socket(zmq.REQ)
        connect = reqSocket.connect(SERVER)

        flag = str('RATES|'+ticker)

        try:
            reqSocket.send_string(flag)
            data = reqSocket.recv_string()
        except zmq.Again as e:
            print('waiting MT5...')


        info, bid_, ask_ =  data.strip('\n').split(',')

        #bid é o preco da venda
        #ask é o preco da compra

        ret_ = [float(bid_), float(ask_)]

        return ret_

class mt5_currbook:

    def __new__(self,
                ticker,
                SERVER=standard_server
                ):

        context = zmq.Context()
        reqSocket = context.socket(zmq.REQ)
        connect = reqSocket.connect(SERVER)

        flag = str('BOOK|'+ticker)

        try:
            reqSocket.send_string(flag)
            data = reqSocket.recv_string()
        except zmq.Again as e:
            print('waiting MT5...')

        book = data.split('\n')
        price = book[0]
        book = book[1:-2]
        
        _book_sell = []
        _book_buy = []

        for i in book:
            type, price, volume = i.split(',')
            
            type = int(type)
            price = float(price)
            volume = float(volume)

            if(type == 1):
                _book_sell.append([type, price, volume])
            if(type == 2):
                _book_buy.append([type, price, volume])

        #_book_sell = _book_sell.sort()
        #_book_buy = _book_buy.sort()

        df_book = pd.DataFrame({'type':[], 'price':[], 'volume':[]})
        df_book.append(_book_sell)

        return _book_sell

class mt5_lastdata:

    def __new__(self, symbol, timeframe, startpos, count, forex = False, SERVER ='tcp://192.168.100.105:10000'): 

        context = zmq.Context()
        reqSocket = context.socket(zmq.REQ)

        connect = reqSocket.connect(SERVER)

        symbol__ = dict({'date':[],
                         'open':[],
                         'low':[],
                         'high':[],
                         'close':[],
                         'tickvolume':[],
                         'realvolume':[]})

        flag = str('LAST|'+str(symbol)+'|'+str(timeframe)+'|'+str(startpos)+'|'+str(count))
        
        try:
            reqSocket.send_string(flag)
            data = reqSocket.recv_string()
        except zmq.Again as e:
            print('waiting MT5...')

        
        data = str(data).split('|')
        data.reverse()
        
        del data[-1]
        

        ret = {'date':[], 'open':[], 'low':[], 'high':[], 'close':[], 'tickvolume':[], 'realvolume':[], 'info':str(symbol)}
        for i in data:
            _i = i.split(',')
            ret['date'].append(_i[0])
            ret['open'].append(float(_i[1]))
            ret['low'].append(float(_i[2]))
            ret['high'].append(float(_i[3]))
            ret['close'].append(float(_i[4]))
            ret['tickvolume'].append(float(_i[5]))
            ret['realvolume'].append(float(_i[6]))
       
        ret = pd.DataFrame(ret)[::-1]
        ret.index = ret['date']
        ret = ret.drop(columns=['date'])
        ret = resampler(ret, timeframe, data='last')[::-1]
  
        return ret



class mt5_historicaldata_s:

    '''

    start_datetime :
        ex:'2020.10.01' : pega dados a partir de 2020.10.01 excluindo
                          2020.10.01
    idem para end_datetime

    server : O ip do servidor que ta ligado no MT5

    csv_list : Arquivo contendo os tickers que você quer pegar os dados historicos

    '''

    def __new__(self,
                timeframe,
                start_datetime,
                end_datetime,
                csv_list,
                interpol = False,
                print_ticker = False,
                bolsa='IBOV',
                reframe=False,
                SERVER = standard_server
                ):

        
        context = zmq.Context()
        reqSocket = context.socket(zmq.REQ)
        connect = reqSocket.connect(SERVER)

        if(type(csv_list) == type(list())):
            ticker_list = csv_list
        else:
            ticker_list = list()
            file = open(csv_list, 'r')

            for i in file.readlines():

                ticker_list.append(i.strip('\n'))
                file.close()

        symbol__ = dict({'date':[],
                         'open':[],
                         'low':[],
                         'high':[],
                         'close':[],
                         'volume1':[],
                         'volume2':[]})

        symbol_data = dict()


        for t in ticker_list:
            
            if(print_ticker):
                print(t)

            symbol_data[t]={'date':[],
                            'open':[],
                            'low':[],
                            'high':[],
                            'close':[],
                            'tickvolume':[],
                            'realvolume':[]}
            



            flag = str("DATA|"+str(t)+"|"+str(timeframe)+"|"+str(start_datetime)+" [00:00:00]|"+str(end_datetime)+" [00:00:00]")

            try:
                reqSocket.send_string(flag)
                data = reqSocket.recv_string()
            except zmq.Again as e:
                print("waiting MT5...")

            data = str(data).split('|')
            data.reverse()
            del data[-1]

            for i in data:

                symbol_data[t]['date'].append(i.split(',')[0])
                symbol_data[t]['open'].append(float(i.split(',')[1]))
                symbol_data[t]['low'].append(float(i.split(',')[2]))
                symbol_data[t]['high'].append(float(i.split(',')[3]))
                symbol_data[t]['close'].append(float(i.split(',')[4]))
                symbol_data[t]['tickvolume'].append(float(i.split(',')[5]))
                symbol_data[t]['realvolume'].append(float(i.split(',')[6]))
            if(reframe==True):
                symbol_data[t] = resampler(pd.DataFrame(symbol_data[t]).copy(), timeframe, exchange=bolsa)


            if(interpol == True):
                
                o, l, h, c = symbol_data[t].mean()[:4]

                symbol_data[t]['open'] = symbol_data[t]['open'].replace(0,o).copy()
                symbol_data[t]['close'] = symbol_data[t]['close'].replace(0,l).copy()
                symbol_data[t]['high'] = symbol_data[t]['high'].replace(0,h).copy()
                symbol_data[t]['low'] = symbol_data[t]['low'].replace(0,c).copy()

        
        return symbol_data

class mt5_historicaldata:

    '''

    start_datetime :
        ex:'2020.10.01' : pega dados a partir de 2020.10.01 excluindo
                          2020.10.01
    idem para end_datetime

    server : O ip do servidor que ta ligado no MT5

    csv_list : Arquivo contendo os tickers que você quer pegar os dados historicos

    '''

    def __new__(self,
                timeframe,
                start_datetime,
                end_datetime,
                interpol = False,
                print_ticker = False,
                reframe=True,
                csv_list = 'symbols.csv',
                bolsa='IBOV',
                SERVER = 'tcp://192.168.100.106:10000'
                ):

        servers = ['tcp://192.168.100.106:10000']
        
        ticker_list = list()
        file = open(csv_list, 'r')

        for i in file.readlines():
            ticker_list.append(i.strip('\n'))
            file.close()

        symbol_data = dict()
        context = zmq.Context()


        def getdata(t, tf, sd, ed):

            symbol = dict({'date':[],
                            'open':[],
                            'low':[],
                            'high':[],
                            'close':[],
                            'tickvolume':[],
                            'realvolume':[]})

            flag = str("DATA|"+str(t)+"|"+str(tf)+"|"+str(sd)+" [00:00:00]|"+str(ed)+" [00:00:00]")

            
            n = randrange(len(servers))
            srv = servers[n]

            reqSocket = context.socket(zmq.REQ)

            connect = reqSocket.connect(srv)
            
            try:
                reqSocket.send_string(flag)
                data = reqSocket.recv_string()
            except zmq.Again as e:
                print('waiting mt5')
            
            data = str(data).split('|')
            data.reverse()
            del data[-1]

            for i in data:
                if(print_ticker == True):
                    print(i)
                    
                symbol['date'].append(i.split(',')[0])
                symbol['open'].append(float(i.split(',')[1]))
                symbol['low'].append(float(i.split(',')[2]))
                symbol['high'].append(float(i.split(',')[3]))
                symbol['close'].append(float(i.split(',')[4]))
                symbol['tickvolume'].append(float(i.split(',')[5]))
                symbol['realvolume'].append(float(i.split(',')[6]))
            
            if(reframe == True):
                symbol = resampler(pd.DataFrame(symbol).copy(), timeframe, exchange=bolsa)
            else:
                symbol = pd.DataFrame(symbol).copy().iloc[::-1]


            if(interpol == True):
                
                o, l, h, c = symbol.mean()[:4]

                symbol['open'] = symbol['open'].replace(0,o).copy()
                symbol['close'] = symbol['close'].replace(0,l).copy()
                symbol['high'] = symbol['high'].replace(0,h).copy()
                symbol['low'] = symbol['low'].replace(0,c).copy()


            return symbol, t


        with concurrent.futures.ThreadPoolExecutor(16) as executor:
            ticker = ticker_list
            serv = servers
            run = [executor.submit(getdata, t, timeframe, start_datetime, end_datetime) for t in ticker]

            for f in concurrent.futures.as_completed(run):
                symbol_data[f.result()[1]] = f.result()[0]

        
            return symbol_data

class mt5_singlehistoricaldata:

    '''

    start_datetime :
        ex:'2020.10.01' : pega dados a partir de 2020.10.01 excluindo
                          2020.10.01
    idem para end_datetime

    server : O ip do servidor que ta ligado no MT5

    csv_list : Arquivo contendo os tickers que você quer pegar os dados historicos

    '''

    def __new__(self,
                ticker,
                timeframe,
                start_datetime,
                end_datetime,
                raw= False,
                interpol = False,
                forex= False,
                bolsa='IBOV',
                SERVER = standard_server,
                ):

        context = zmq.Context()
        reqSocket = context.socket(zmq.REQ)
        connect = reqSocket.connect(SERVER)

        ticker_list = list()
        ticker_list.append(ticker)

        symbol__ = dict({'date':[],
                         'open':[],
                         'low':[],
                         'high':[],
                         'close':[],
                         'volume1':[],
                         'volume2':[]})

        symbol_data = dict()


        for t in ticker_list:

            #print(t)

            symbol_data[t]={'date':[],
                            'open':[],
                            'low':[],
                            'high':[],
                            'close':[],
                            'tickvolume':[],
                            'realvolume':[]}
            



            flag = str("DATA|"+str(t)+"|"+str(timeframe)+"|"+str(start_datetime)+" [00:00:00]|"+str(end_datetime)+" [00:00:00]")

            try:
                reqSocket.send_string(flag)
                data = reqSocket.recv_string()
            except zmq.Again as e:
                print("waiting MT5...")

            data = str(data).split('|')
            data.reverse()
            del data[-1]

            for i in data:

                symbol_data[t]['date'].append(i.split(',')[0])
                symbol_data[t]['open'].append(float(i.split(',')[1]))
                symbol_data[t]['low'].append(float(i.split(',')[2]))
                symbol_data[t]['high'].append(float(i.split(',')[3]))
                symbol_data[t]['close'].append(float(i.split(',')[4]))
                symbol_data[t]['tickvolume'].append(float(i.split(',')[5]))
                symbol_data[t]['realvolume'].append(float(i.split(',')[6]))
            
            if(timeframe == 16408):
                raw = True
                

                symbol_data[t]['date'][::-1]
                symbol_data[t]['open'][::-1]
                symbol_data[t]['low'][::-1]
                symbol_data[t]['high'][::-1]
                symbol_data[t]['close'][::-1]
                symbol_data[t]['tickvolume'][::-1]
                symbol_data[t]['realvolume'][::-1]

            if raw == False: 
                symbol_data[t] = resampler(pd.DataFrame(symbol_data[t]).copy(), timeframe, exchange=bolsa)


            if(interpol == True):
                
                o, l, h, c = symbol_data[t].mean()[:4]
                
                symbol_data[t]['open'] = symbol_data[t]['open'].replace(0,o).copy()
                symbol_data[t]['close'] = symbol_data[t]['close'].replace(0,l).copy()
                symbol_data[t]['high'] = symbol_data[t]['high'].replace(0,h).copy()
                symbol_data[t]['low'] = symbol_data[t]['low'].replace(0,c).copy()
                

            
        return symbol_data[ticker]



class mt5_options:

    '''

    start_datetime :
        ex:'2020.10.01' : pega dados a partir de 2020.10.01 excluindo
                          2020.10.01
    idem para end_datetime

    server : O ip do servidor que ta ligado no MT5

    csv_list : Arquivo contendo os tickers que você quer pegar os dados historicos

    '''

    def __new__(self,
                ticker,
                interpol = False,
                forex= False,
                bolsa='IBOV',
                SERVER = standard_server,
                ):

        context = zmq.Context()
        reqSocket = context.socket(zmq.REQ)
        connect = reqSocket.connect(SERVER)

        ticker_list = list()
        ticker_list.append(ticker)

        symbol__ = dict({'date':[],
                         'open':[],
                         'low':[],
                         'high':[],
                         'close':[],
                         'volume1':[],
                         'volume2':[]})

        symbol_data = list()


        for t in ticker_list:

            flag = str("OPTIONS|"+str(t))

            try:
                reqSocket.send_string(flag)
                data = reqSocket.recv_string()
            except zmq.Again as e:
                print("waiting MT5...")
            
           
            #data = str(data).split('|')
            #data.reverse()
            #del data[-1]
            
            symbol_data.append(data)
            
        return symbol_data

class mt5_buy:

    def __new__(self, symbol, sl, tp, vol,SERVER=standard_server):

        #TRADE|TYPE|SYMBOL|STOPLOSS|STOPGAIN|VOLUME
        flag = str('OPEN|'+'1'+'|'+str(symbol)+'|'+str(sl)+'|'+str(tp)+'|'+str(vol))
        context = zmq.Context()
        reqSocket = context.socket(zmq.REQ)
        connect = reqSocket.connect(SERVER)

        try:
            reqSocket.send_string(flag)
            msg = reqSocket.recv_string()
        except zmq.Again as e:
            print('Waiting for Push MT5...')

        ticket__, price__, bid__, ask__, volume__ = msg.split(',')
        ret__ = [int(ticket__), float(bid__), float(volume__)]
        log_dict[str(ticket__)] = openLog('long', float(bid__), float(volume__), symbol)
        savelog(log_dict)

        return ret__




class mt5_sell:

    def __new__(self, symbol, sl, tp, vol, SERVER=standard_server):

        #TRADE|TYPE|SYMBOL|STOPLOSS|STOPGAIN|VOLUME
        flag = str('OPEN|'+'-1'+'|'+str(symbol)+'|'+str(sl)+'|'+str(tp)+'|'+str(vol))

        context = zmq.Context()
        reqSocket = context.socket(zmq.REQ)
        connect = reqSocket.connect(SERVER)
        #print(connect)

        try:
            reqSocket.send_string(flag)
            msg = reqSocket.recv_string()
        except zmq.Again as e:
            print('Waiting for Push MT5...')

        ticket__, price__, bid__, ask__, volume__ = msg.split(',')
        ret__ = [int(ticket__), float(ask__), float(volume__)]
        log_dict[str(ticket__)] = openLog('short', float(ask__), float(volume__), symbol)
        savelog(log_dict)
        print('sell : ', ret__)
        return ret__

class mt5_buybook:

    def __new__(self, symbol, price,sl, tp, vol,SERVER=standard_server):

        #TRADE|TYPE|SYMBOL|PRICE|STOPLOSS|STOPGAIN|VOLUME
        flag = str('PENDING|'+'1'+'|'+str(symbol)+'|'+str(price)+'|'+str(sl)+'|'+str(tp)+'|'+str(vol))
        context = zmq.Context()
        reqSocket = context.socket(zmq.REQ)
        connect = reqSocket.connect(SERVER)

        try:
            reqSocket.send_string(flag)
            msg = reqSocket.recv_string()
        except zmq.Again as e:
            print('Waiting for Push MT5...')

        ticket__, price__, bid__, ask__, volume__ = msg.split(',')
        ret__ = [int(ticket__), float(bid__), float(volume__)]
        log_dict[str(ticket__)] = openLog('long', float(bid__), float(volume__), symbol)
        savelog(log_dict)
        print('buy : ', ret__)

        return ret__

class mt5_sellbook:

    def __new__(self, symbol, price, sl, tp, vol, SERVER=standard_server):

        #TRADE|TYPE|SYMBOL|STOPLOSS|STOPGAIN|VOLUME
        flag = str('PENDING|'+'-1'+'|'+str(symbol)+'|'+str(price)+'|'+str(sl)+'|'+str(tp)+'|'+str(vol))

        context = zmq.Context()
        reqSocket = context.socket(zmq.REQ)
        connect = reqSocket.connect(SERVER)
        #print(connect)

        try:
            reqSocket.send_string(flag)
            msg = reqSocket.recv_string()
        except zmq.Again as e:
            print('Waiting for Push MT5...')

        ticket__, price__, bid__, ask__, volume__ = msg.split(',')
        ret__ = [int(ticket__), float(ask__), float(volume__)]
        log_dict[str(ticket__)] = openLog('short', float(ask__), float(volume__), symbol)
        savelog(log_dict)
        return ret__

class mt5_close:

    def __new__(self, ticket, SERVER=standard_server):

        #CLOSE|TICKET
        flag = str('CLOSE|'+str(ticket))

        context = zmq.Context()
        reqSocket = context.socket(zmq.REQ)
        connect = reqSocket.connect(SERVER)

        try:
            reqSocket.send_string(flag)
            msg = reqSocket.recv_string()
        except zmq.Again as e:
            print('Waiting for Push MT5...')

        status__, price__  ,bid__, ask__, volume__= msg.split(',')
        ret__ = [int(status__), float(price__), float(volume__), float(ask__), float(bid__)]
        close_flag = closeLog(str(ticket), float(price__))
        savelog(log_dict)
        return ret__