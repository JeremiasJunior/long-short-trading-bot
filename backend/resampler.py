import os
import matplotlib.pyplot as plt
import pandas as pd
import time
import datetime
import numpy as np

def strtomin(hour):
        h, m = hour.split(':')
        h = int(h)
        m = int(m)
        
        total_m = 60*h + m
        
        return total_m

class resampler:

    '''
    dfname :
        nome do arquivo que você quer importar por exemplo 'AZUL4.csv'
    
        dia inteiro
        0 -> 1439
        

        10:00 as 18:00
        600 -> 1080
    '''
    
    
    def __new__(self, dfname, n, exchange = 'IBOV', data = 'hist', save = False, start_d = None, end_d = None):
        
        if(exchange == 'IBOV'):
            minute_start=610
            minute_end=1010
            start = '10:15'
            end = '16:45'
            if(data == 'last'):

                start = dfname.index[0].split(' ')[1]
                minute_start= strtomin(start)
                minute_end =strtomin(end)
                
        elif(exchange == 'NAS'):
            minute_start = 1000
            minute_end = 1360
            start = '16:40'
            end = '22:40'
        elif(exchange == 'forex'):
            minute_start = 0
            minute_end = 1439
            start='00:00'
            end='23:59'
            
            if(data == 'last'):
                start = dfname.index[0].split(' ')[1]
                minute_start= strtomin(start)
                minute_end =strtomin(end)
                
        elif(exchange == 'commodity'):
            minute_start = 180
            minute_end = 1270
            start='03:00'
            end='21:10'
            
            if(data == 'last'):
                start = dfname.index[0].split(' ')[1]
                minute_start= strtomin(start)
                minute_end =strtomin(end)
        
        
        if(data == 'last'):
            start = dfname.index[0].split(' ')[1]
            minute_start= strtomin(start)
            minute_end =strtomin(end)
        
        
            
            
        

        raw_dt = dfname.copy()
        dt = raw_dt
        try:    
            dt[['date', 'hour']] = dt.date.str.split(' ', expand=True)
        except:
            return dfname
            
        dt = list(dt.groupby(['date']))
        new_dt = pd.DataFrame()

        real_index = 0
        
        for dt_i in dt:
            row_template = ''
            minute_total = 0
            
            '''
            forex [max = 1439, min = 0]
            xp [ max=1080, min=600]

            '''

            max__ = minute_end
            min__ = minute_start
            for i in dt_i[1]['hour'].to_list():
                
                h__, m__ = i.split(':')
                temp__ = int(h__)*60 + int(m__)
                if temp__ > max__ or temp__ < min__:

                    dt_i = list(dt_i)
                    i__ = dt_i[1]['hour'].to_list().index(i)
                    i_ = dt_i[1]['hour'].index.to_list()[i__]
                    dt_i[1] = dt_i[1].drop(i_)
                    dt_i = tuple(dt_i)
                    
                    
            init = (' ').join([start])
            end = (' ').join([end]) 
            current_day = dt_i[0]            
            data = []
            data.insert(0, {'date': current_day,
                            'hour': init,
                            'open': np.nan,
                            'low' : np.nan,
                            'high':np.nan,
                            'close':np.nan,
                            'volume1':0.0,
                            'volume2':0.0
                            })


            dt_i = pd.concat([pd.DataFrame(data), dt_i[1]], ignore_index=True)
            dt_i = dt_i.append({'date': current_day,
                            'hour': end,
                            'open': np.nan,
                            'low' : np.nan,
                            'high':np.nan,
                            'close':np.nan,
                            'volume1':0.0,
                            'volume2':0.0
                            }, ignore_index = True)

            dt_i['date'] = dt_i['date' ].str.cat(dt_i[['hour']],sep = ' ')      
            dt_i['date'] = pd.to_datetime(dt_i['date'])
            
            if(n == 1):
                dt_i = dt_i.resample('T', on='date').sum()
            elif(n == 16408):
                key = '1D'
                #dt_i = dt_i[::-1]
                return dt_i
            elif(n ==5): 
                key = '5T'
                dt_i = dt_i.resample(key, on='date').sum()
            elif(n == 10): 
                key = '10T'
                dt_i = dt_i.resample(key, on='date').sum()
            elif(n == 15): 
                key = '15T'
                dt_i = dt_i.resample(key, on='date').sum()
            elif(n == 60): 
                key = '60T'
                dt_i = dt_i.resample(key, on='date').sum()

            new_dt = (pd.DataFrame.append(new_dt, dt_i, ignore_index = False))
           
        if(save):
            new_dt.to_csv(dfname)
    
    
        return new_dt
