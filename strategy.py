import init

from analisys.bkt_analisys import *
from analisys.data_analisys import *
from analisys.graph_analisys import *
from analisys.optmizer_analisys import *


import pandas as pd
import seaborn as sns
import random
import os

from backend.resampler import *
from backend.mt5_tools import *

from statsmodels.tsa.stattools import adfuller
from analisys.graph_analisys import moving_avg

import plotly.graph_objects as go
from plotly.subplots import make_subplots

import time
import plotly.io as pio
pio.orca.config.use_xvfb = True

from datetime import datetime

import concurrent.futures
import collections
import multiprocessing

pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)
pd.set_option('display.width', None)
pd.set_option('display.max_colwidth', None)
sns.set()
pd.options.display.float_format = '{:.1f}'.format
code = token(2)

#fourteenbis(start_date='2018.01.01', end_date='2020.12.31', d_train=7, d_test=1, param='profit', dataframe=5, p_size=300, sample_size=5, n_opt=45, lags=25, stop_n = [5,50], stop_r = [-30, -10], period = [5, 100], s_spread=[1.0, 6.0], l_spread = [-6.0, -1.0], tp_s=[-3.5, 3.5], tp_l=[-3.5, 3.5], tp_r=[80,200], csv_l='symbols_ibovf.csv')

class fourteenbis:
    
    def get_days(start_date, end_date, d_train, d_test, benchmark):

        ibov = mt5_singlehistoricaldata(benchmark, 16408, start_date, end_date)
        ibov_date = list(ibov['date'])
        ibov_date.reverse()

        date_iteration = []

        for d in range(len(ibov_date))[:-(d_train+d_test)]:
            
            train_startdate = ibov_date[d].split(' ')[0]
            train_enddate = ibov_date[d+d_train].split(' ')[0]
            test_startdate = ibov_date[d+d_train].split(' ')[0]
            test_enddate = ibov_date[d+d_test+d_train].split(' ')[0]
            
            date_iteration.append(tuple([train_startdate, train_enddate,
                                        test_startdate, test_enddate]))

        real_startdate = date_iteration[0][2]
        real_enddate = date_iteration[-1][-1]

        return date_iteration, ibov_date, real_startdate, real_enddate

    def cointpair_selection(hist, dataframe, lags):

        co_list = []
        

        co = h_coint(hist, dataframe, n_lags=lags)
        co = pd.DataFrame(co)
        co = co.sort_values(by=['pvalue'])
        co = co.reset_index(drop=True)

        new_co = pd.DataFrame({'pvalue':pd.Series([]), 'stdx':pd.Series([]), 
                                    'stdy':pd.Series([]), 'x':pd.Series([]), 'y':pd.Series([])})


        if(len(co) == 0):
            return new_co

        co_len = [i for i in range(len(co))]
        
        for j in co_len:

            x,y = list(co['x'])[j], list(co['y'])[j]

            if not((x in list(new_co['x'])) or (x in list(new_co['y'])) 
                or (y in list(new_co['x'])) or (y in list(new_co['y']))):
                    
                new_co = new_co.append(co.iloc()[j])

            new_co = new_co.reset_index(drop=True)
    


        return co

    '''
    def cointpair_selection(hist, dataframe, lags, df_testdata):

        co = h_coint(hist, dataframe, n_lags=lags)
        co = pd.DataFrame(co)
        co = co.sort_values(by=['pvalue'])
        co = co.reset_index(drop=True)

        new_co = pd.DataFrame({'pvalue':pd.Series([]), 'stdx':pd.Series([]), 
                                    'stdy':pd.Series([]), 'x':pd.Series([]), 'y':pd.Series([])})



        if(len(co) == 0):
            return new_co
        
        co_len = [i for i in range(len(co))]

        for j in co_len:

            x,y = list(co['x'])[j], list(co['y'])[j]

            if not((x in list(new_co['x'])) or (x in list(new_co['y'])) or 
                        (y in list(new_co['x'])) or (y in list(new_co['y']))):
                
                new_co = new_co.append(co.iloc()[j])
        
        new_co = new_co.reset_index(drop=True)
        
        print(new_co)
        
        
        return new_co
        '''
    


    def loop_work(sample,  
                        hist, 
                            hist_test, 
                                n_opt, 
                                    p_size,
                                        param, 
                                            space_param,
                                                optmizer,
                                                    ):
        
        
        x, y = sample['x'], sample['y']

        if(optmizer == 'dummy'):
            result_opttrain = dummybkt(x, y, hist, hist_test, n=n_opt, opt_param=param, pos_size=p_size, space=space_param)
        if(optmizer == 'forest'):
            result_opttrain = forestbkt(x, y, hist, hist_test, n=n_opt, opt_param=param, pos_size=p_size, space=space_param)

        bkt_info = str(result_opttrain['test']['info'])
        bkt_positionslist = result_opttrain['test']['positions_list']
    
        bkt_xname = result_opttrain['test']['info']['x_symbol']
        bkt_yname = result_opttrain['test']['info']['y_symbol']
        bkt_sspread = result_opttrain['test']['info']['short_spread']
        bkt_lspread = result_opttrain['test']['info']['long_spread']
        bkt_psize = result_opttrain['test']['info']['position_size']
        bkt_stopnumb = result_opttrain['test']['info']['stop_number']
        bkt_tpshort = result_opttrain['test']['info']['tp_short']
        bkt_tplong = result_opttrain['test']['info']['tp_long']
        bkt_period = result_opttrain['test']['info']['period']
        bkt_mincount = result_opttrain['test']['info']['min_count']
        bkt_returnstd = result_opttrain['test']['info']['std_returns']
        bkt_profitstd = result_opttrain['test']['info']['std_profit']
        try:
            bkt_expo = result_opttrain['test']['expo'][0]
        except:
            bkt_expo = result_opttrain['test']['expo']

        bkt_roi = result_opttrain['test']['roi']



        

        loopdata_list = []

        for i in range(len(bkt_positionslist)):
            print(i)

            if(len(bkt_positionslist) == 0):
                
                loopdata_list.append({'type': None,
                        'date_open':0,
                        'date_close': 0,
                        'x_name':bkt_xname,
                        'y_name':bkt_yname,
                        'x_type':0,
                        'y_type':0,
                        'y_openprice':0,
                        'y_closeprice':0,
                        'x_openprice':0,
                        'x_closeprice':0,
                        'x_volume':0,
                        'y_volume':0,
                        'expo':0,
                        'status':None,
                        'return':0,
                        'roi':0,
                        's_spread':bkt_sspread,
                        'l_spread':bkt_lspread,
                        'tp_short':bkt_tpshort,
                        'tp_long':bkt_tplong,
                        's_number':bkt_stopnumb,
                        'period':bkt_period,
                        'count':bkt_mincount,
                        'min_count':bkt_mincount,
                        'roi':0,
                        #'ATRx':None,
                        #'ATRy':None,
                        'std_returns':None,
                        'std_profit':None


                    
                        })

                
            
                
            if(len(bkt_positionslist) > 0):

                loopdata_list.append({'type':bkt_positionslist[i]['type'],
                    'date_open': datetime.strptime(str(bkt_positionslist[i]['df_date'][0]),'%Y-%m-%d %H:%M:%S'),
                    'date_close': datetime.strptime(str(bkt_positionslist[i]['df_date'][1]),'%Y-%m-%d %H:%M:%S'),                        
                    'x_name':bkt_xname,
                    'y_name':bkt_yname,
                    'x_type':bkt_positionslist[i]['x_type'],
                    'y_type':bkt_positionslist[i]['y_type'],
                    'y_openprice':bkt_positionslist[i]['df_yprice'][0],
                    'y_closeprice':bkt_positionslist[i]['df_yprice'][1],
                    'x_openprice':bkt_positionslist[i]['df_xprice'][0],
                    'x_closeprice':bkt_positionslist[i]['df_xprice'][1],
                    'x_volume':bkt_positionslist[i]['x_volume'],
                    'y_volume':bkt_positionslist[i]['y_volume'],
                    'expo':bkt_expo,
                    'return':bkt_positionslist[i]['profit'],
                    'roi':bkt_roi,
                    'status':bkt_positionslist[i]['status'],
                    's_spread':bkt_sspread,
                    'l_spread':bkt_lspread,
                    'tp_short':bkt_tpshort,
                    'tp_long':bkt_tplong,
                    's_number':bkt_stopnumb,
                    'period':bkt_period,
                    'count':bkt_mincount,
                    'min_count':bkt_mincount,
                    #'ATRx':result_opttrain['test']['ATR'][0],
                    #'ATRy':result_opttrain['test']['ATR'][1],
                    'std_returns':bkt_returnstd,
                    'std_profit':bkt_profitstd

                    })



        return loopdata_list, result_opttrain['parametros']
        

        

    def __new__(self, start_date, 
                        end_date,
                         d_train,
                          d_test,
                           param,
                            dataframe,
                             p_size,
                              sample_size,
                               n_opt, lags,
                                stop_n,
                                  period,
                                   s_spread,
                                    l_spread,
                                     tp_s,
                                      tp_l,
                                       c_min,
                                        optimizer,
                                        csv_l,
                                          benchmark,
                                           exchange,
                                            msg='',
                                             server = 'tcp://192.168.0.28:10000'):

        start = time.perf_counter()

        space_param = [(period[0], period[1]),
                (s_spread[0], s_spread[1]),
                (l_spread[0], l_spread[1]),
                (tp_s[0], tp_s[1]),
                (tp_l[0], tp_l[1]),
                (stop_n[0], stop_n[1]),
                (c_min[0], c_min[1])]

        df_testdata = pd.DataFrame()
        date_iteration, ibov_date, real_startdate, real_enddate = self.get_days(start_date, end_date, d_train, d_test, benchmark)

        df_loopdata = pd.DataFrame()
        #loop de execução do programa

        d_count = 1
        #code = token(2)

        for d in date_iteration:

            print('--')
            train_startdate, train_enddate, test_startdate, test_enddate = d

            #pega dados do metatrader
            hist = mt5_historicaldata(dataframe, train_startdate, train_enddate, csv_list=csv_l, interpol=True)
            hist_test = mt5_historicaldata(dataframe, test_startdate, test_enddate, csv_list=csv_l, interpol=True)

            


            print(d)
            hist_keys = list(hist.keys())
            histtest_keys = list(hist_test.keys())
            print('{}/{}'.format(d_count, len(date_iteration)))

            
            #valida dados do metatrader
            if(len(histtest_keys) == 0 or len(hist_keys) == 0):
                
                df_testdata = df_testdata.append({'date':test_startdate,'RoI':0, 'PPP':0, 'EXPO':0, 'n':0}, ignore_index=True)
                d_count = d_count+1
                continue
                
            for i in hist_keys:
                if(hist[i].empty):
                    hist.pop(i)
            
            for i in histtest_keys:
                if(hist_test[i].empty):
                    hist_test.pop(i)
      
            if(not (len(hist) == len(hist_test)) or (len(hist) == 0 or len(hist_test) == 0)):
                
                df_testdata = df_testdata.append({'date':test_startdate,'RoI':0, 'PPP':0, 'EXPO':0, 'n':0}, ignore_index=True)
                d_count = d_count+1
                continue
                    
            print('-hist: {}/{}'.format(len(hist), len(hist_test)))

            #verifica cointegracao
            co = self.cointpair_selection(hist, dataframe, lags)
            
            if(len(co) == 0):
                df_testdata = df_testdata.append({'date':test_startdate,'RoI':0, 'PPP':0, 'EXPO':0, 'n':0}, ignore_index=True)
                d_count = d_count+1
                continue
            
            #seleciona pares aleatoriamente
            if(len(co) < sample_size):
                res = random.sample(range(len(co)), len(co))   
            else:
                res = random.sample(range(len(co)), sample_size)

            sample = pd.DataFrame(co.iloc()[res])
            sample_x = np.array(sample['x'])
            sample_y = np.array(sample['y'])

            bkt_counter = 1
            dcode = token(2)

            #roda os testes com os pares
            
            print('-coint: {}\n--'.format(len(co)))

            with concurrent.futures.ProcessPoolExecutor(16) as executor:

                run = [executor.submit(self.loop_work, s, hist, hist_test, n_opt, p_size, param, space_param, optimizer) for s in sample.iloc()]
                
                for f in concurrent.futures.as_completed(run):
                    
                    loopdata, parametros = f.result()
                    
                    df_loopdata = df_loopdata.append(loopdata, ignore_index=True)
                    partial_data = '{}.csv'.format(code)
                    df_loopdata.to_csv(partial_data)
                    
                    
                    
                
            d_count = d_count + 1 
        
        lname='{}{}{}_l{}{}{}{}{}{}{}{}_{}x{}_{}.xls'.format(optimizer,space_param,code, dataframe, sample_size, n_opt, lags, param, p_size, d_train,d_test,start_date, end_date,msg)
        df_loopdata.to_excel(lname)
        print(lname)
        finish = time.perf_counter()

        print("\n############\ntime: {}s\n############\n".format(round(finish-start, 2)))


        