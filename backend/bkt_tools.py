'''
No fim o backtest tem um problema fundamental pois ele não utiliza os valores de bid e ask. isso tem ser implementado
posteriormente
  fourteenbis(start_date='2018.02.25', end_date='2018.04.01', d_train=4, d_test=1, param='profit', dataframe=5, p_size=100, sample_size=5, n_opt=20, lags=28, csv_l='symbols_ibovf.csv')

'''

import pandas as pd
import datetime
from secrets import token_hex as token

def openLog( _type, _price, _volume, _symbol, _i, _column):

    ticket_dict = {'symbol':_symbol,
                'type':_type,
                'status':'open',
                'time':[str(datetime.datetime.now()), None],
                'price':[_price, None],
                'volume':_volume,
                'lucro':None,
                'i':_i,
                'column':_column}

    return ticket_dict

def savelog( _dict):

    df = pd.DataFrame(_dict)
    df.to_json(name)

class bkt_tools:

    def __init__(self, log_dict):
        
        self.log_dict = log_dict



    def closeLog(self, _ticket, _price):

        self.log_dict['rawlog'][str(_ticket)]['status'] = 'close'
        self.log_dict['rawlog'][str(_ticket)]['time'][1] = str(datetime.datetime.now())
        self.log_dict['rawlog'][str(_ticket)]['price'][1] = _price

        if self.log_dict['rawlog'][_ticket]['type'] == 'long':
            self.log_dict['rawlog'][str(_ticket)]['lucro'] = (float(self.log_dict['rawlog'][str(_ticket)]['price'][1]) - float(self.log_dict['rawlog'][str(_ticket)]['price'][0]))*self.log_dict['rawlog'][str(_ticket)]['volume']
        if self.log_dict['rawlog'][_ticket]['type'] == 'short':
            self.log_dict['rawlog'][str(_ticket)]['lucro'] = (float(self.log_dict['rawlog'][str(_ticket)]['price'][0]) - float(self.log_dict['rawlog'][str(_ticket)]['price'][1]))*self.log_dict['rawlog'][str(_ticket)]['volume']
        return True

    def savelog(self, _dict):

        df = pd.DataFrame(_dict)
        df.to_json(name)

    def bkt_getprice(self, symbol, column, i):
        try:
            currprice = symbol[column][i]
        except:
            currprice = 0

        return [currprice, currprice]

    def bkt_buy(self, symbol, sl, tp, vol):
        #symbol = {'data_frame':,'column':, 'i':, 'name':}

        ticket__ = token(4)
        i__ = symbol['i']
        column__ = symbol['column']
        price__ = symbol['data_frame'][column__][i__]

        ret__ = [ticket__, symbol['data_frame'][column__][i__], vol]

        self.log_dict['rawlog'][ticket__] = openLog('long', price__, vol, symbol['name'], i__, column__)
        #savelog(log_dict)
        return ret__

    def bkt_sell(self, symbol, sl, tp, vol):

        ticket__ = token(4)
        i__ = symbol['i']
        column__ = symbol['column']
        price__ = symbol['data_frame'][column__][i__]

        ret__ = [ticket__, symbol['data_frame'][column__][i__], vol]

        self.log_dict['rawlog'][ticket__] = openLog('short', price__, vol, symbol['name'], i__, column__)
        #savelog(log_dict)
        return ret__

    def bkt_close(self, ticket__, df, i__):
        #symbol = {'ticket', 'data_frame', 'i', 'column'}
        
        #i__ = log_dict[ticket__]['i']
       
        status__ = 1
        column__ = self.log_dict['rawlog'][ticket__]['column']
        volume = self.log_dict['rawlog'][ticket__]['volume']
        
        price__ = df[column__][i__]

        ret__ = [status__, price__, volume]

        close_flag = self.closeLog(ticket__, price__)
        #savelog(log_dict)
        return ret__