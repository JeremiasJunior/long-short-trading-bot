import numpy as np
import pandas as pd

import os
import datetime

import backend.bkt as bkt
from analisys.bkt_analisys import runbkt

from statsmodels.tsa.stattools import coint

from skopt import dummy_minimize, forest_minimize
from scipy.optimize import differential_evolution



'''
space = [(period[0], period[1]),
        (s_spread[0], s_spread[1]),
        (l_spread[0], l_spread[1]),
        (tp_s[0], tp_s[1]),
        (tp_l[0], tp_l[1]),
        (stop_n[0], stop_n[1]),
        (stop_r[0], stop_r[1])]
'''

class dummybkt:

    def __new__(self,
                name_x,
                name_y,
                df_treino,
                df_test,
                space,
                opt_param = 'profit',
                n = 20,
                pos_size = 100,
                toTest = True,
                ):


        def simplebkt(  symbol_x,
                        symbol_y,
                        name_x,
                        name_y,
                        _period,
                        s_spread,
                        l_spread,
                        tp_s,
                        tp_l,
                        stop_n):

            #fname = '{}x{}x{}{}{}.json'.format(name_x, name_y, datetime.datetime.now().hour, datetime.datetime.now().minute, datetime.datetime.now().second)

            dic = runbkt(symbol_x, symbol_y, name_x, name_y, _period,s_spread, l_spread, tp_s, tp_l, stop_n, pos_size)
            if(opt_param == 'profit'):
                return dic['profit']
            if(opt_param == 'ppp'):
                return dic['profit_per_position']
            if(opt_param == 'sr'):
                return dic['sucess_ratio']
            if(opt_param == 'pl'):
                return dic['average_profit_loss']
            if(opt_param == 'avg_roi'):
                return dic['roi']*abs(dic['profit'])
            if(opt_param == 'roiloss'):
                return -(0.002 - dic['roi'])
            


        def treino(args):

            _p, shortspread, longspread, takeprofitshort, takeprofitlong, takeprofitreturn, stopnumber, stopreturn = args
            r = simplebkt(df_treino[name_x], df_treino[name_y], name_x, name_y, _p, shortspread, longspread, takeprofitshort, takeprofitlong, takeprofitreturn, stopnumber, stopreturn)
            return -r

        dummy = dummy_minimize(treino, space, random_state=1, verbose=0, n_calls=n)

        
        parametros = dummy['x']
        opt_period, opt_shortspread, opt_longspread, opt_tpshort, opt_tplong, opt_tpreturn, opt_stopnumber, opt_stopreturn = parametros
        #opt_period, opt_shortspread, opt_longspread, opt_stopshort, opt_stoplong, opt_stopreturn,opt_tpshort, opt_tplong = parametros


        result_treino = runbkt(df_treino[name_x], df_treino[name_y], name_x, name_y,
                                opt_period, opt_shortspread, opt_longspread, opt_tpshort, opt_tplong, opt_tpreturn, opt_stopnumber, opt_stopreturn, pos_size)

        date = [0, 1]


        result_test = {}
        if(toTest):
            result_test = runbkt(df_test[name_x], df_test[name_y], name_x, name_y,
                                    opt_period, opt_shortspread, opt_longspread, opt_tpshort, opt_tplong, opt_tpreturn, opt_stopnumber, opt_stopreturn, pos_size)

        return {'treino': result_treino, 'test':result_test, 'parametros':parametros, 'opt':dummy}



####################

'''
class geneticbkt:

    def __new__(self,
                name_x,
                name_y,
                df_treino,
                df_test,
                space,
                opt_param = 'profit',
                n = 20,
                pos_size = 100,
                toTest = True,
                ):
        space = [(period[0], period[1]),
                (s_spread[0], s_spread[1]),
                (l_spread[0], l_spread[1]),
                (tp_s[0], tp_s[1]),
                (tp_l[0], tp_l[1]),
                (stop_n[0], stop_n[1]),
                (stop_r[0], stop_r[1])]

        def simplebkt(  symbol_x,
                        symbol_y,
                        name_x,
                        name_y,
                        _period,
                        s_spread,
                        l_spread,
                        tp_s,
                        tp_l,
                        tp_r,
                        stop_n,
                        stop_r,
                        pos_size,
                        opt_param):

            #fname = '{}x{}x{}{}{}.json'.format(name_x, name_y, datetime.datetime.now().hour, datetime.datetime.now().minute, datetime.datetime.now().second)

            dic = runbkt(symbol_x, symbol_y, name_x, name_y, _period, s_spread, l_spread, tp_s, tp_l, tp_r, stop_n, stop_r, pos_size)
            if(opt_param == 'profit'):
                return dic['profit']
            if(opt_param == 'ppp'):
                return dic['profit_per_position']
            if(opt_param == 'sr'):
                return dic['sucess_ratio']
            if(opt_param == 'pl'):
                return dic['average_profit_loss']
            if(opt_param == 'roi'):
                return dic['roi']
            if(opt_param == 'roiloss'):
                return -(0.02 - dic['roi'])


        def treino(x, name_x, name_y, df_treino, opt_param, pos_size):

            _p, shortspread, longspread, takeprofitshort, takeprofitlong, takeprofitreturn, stopnumber, stopreturn = x

            r = simplebkt(df_treino[name_x], df_treino[name_y], name_x, name_y, _p, shortspread, longspread, takeprofitshort, 
                                                                takeprofitreturn, takeprofitlong, stopnumber, stopreturn, pos_size, opt_param)

            return -r

        genetic = differential_evolution(treino, space, args=[name_x, name_y, df_treino, opt_param, pos_size], disp=True, maxiter=n)
        parametros = genetic['x']
        opt_period, opt_shortspread, opt_longspread, opt_tpshort, opt_tplong, opt_tpreturn, opt_stopnumber, opt_stopreturn = parametros


        result_treino = runbkt(df_treino[name_x], df_treino[name_y], name_x, name_y,
                                opt_period, opt_shortspread, opt_longspread, opt_tpshort, opt_tpreturn, opt_tplong, opt_stopnumber, opt_stopreturn, pos_size)

        date = [0, 1]


        result_test = {}
        if(toTest):
            result_test = runbkt(df_test[name_x], df_test[name_y], name_x, name_y,
                                    opt_period, opt_shortspread, opt_longspread, opt_tpshort, opt_tpreturn, opt_tplong, opt_stopnumber, opt_stopreturn, pos_size)

        return {'treino': result_treino, 'test':result_test, 'parametros':parametros, 'opt':genetic}
'''