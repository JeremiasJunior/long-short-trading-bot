import numpy as np
import pandas as pd

import os
import datetime

import backend.bkt as bkt
from analisys.bkt_analisys import runbkt

from statsmodels.tsa.stattools import coint

from skopt import dummy_minimize, forest_minimize
from scipy.optimize import differential_evolution



class forestbkt:

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
        '''
        space = [(period[0], period[1]),
                (s_spread[0], s_spread[1]),
                (l_spread[0], l_spread[1]),
                (tp_s[0], tp_s[1]),
                (tp_l[0], tp_l[1]),
                (stop_n[0], stop_n[1]),
                (stop_r[0], stop_r[1])]
        '''

        def simplebkt(  symbol_x,
                        symbol_y,
                        name_x,
                        name_y,
                        _period,
                        s_spread,
                        l_spread,
                        tp_s,
                        tp_l,
                        stop_n,
                        c_min,
                        treino=False):

            #fname = '{}x{}x{}{}{}.json'.format(name_x, name_y, datetime.datetime.now().hour, datetime.datetime.now().minute, datetime.datetime.now().second)

            dic = runbkt(symbol_x, symbol_y, name_x, name_y, _period,s_spread, l_spread, tp_s, tp_l, stop_n, c_min, pos_size, t=treino)
            if(opt_param == 'profit'):
                return dic['profit']
            if(opt_param == 'std_returns'):
                return dic['std_returns']
            if(opt_param == 'ppp'):
                return dic['ppp']
            if(opt_param == 'roiloss'):
                return -(0.02 - dic['roi']) #dps testar com valores absolutos


        def treino(args):
            _p, shortspread, longspread, takeprofitshort, takeprofitlong, stopnumber, cmin = args
            r = simplebkt(df_treino[name_x], df_treino[name_y], name_x, name_y, _p, shortspread, longspread, takeprofitshort, takeprofitlong , stopnumber, cmin, treino=True)
            return -r

        forest = forest_minimize(treino, space, random_state=1, verbose=0, n_calls=n)
        parametros = forest['x']
        opt_period, opt_shortspread, opt_longspread, opt_tpshort, opt_tplong, opt_stopnumber, opt_cmin = parametros
        #opt_period, opt_shortspread, opt_longspread, opt_stopshort, opt_stoplong, opt_stopreturn,opt_tpshort, opt_tplong = parametros


        result_treino = runbkt(df_treino[name_x], df_treino[name_y], name_x, name_y,
                                opt_period, opt_shortspread, opt_longspread, opt_tpshort, opt_tplong, opt_stopnumber, opt_cmin,pos_size)

        date = [0, 1]


        result_test = {}
        if(toTest):
            result_test = runbkt(df_test[name_x], df_test[name_y], name_x, name_y,
                                    opt_period, opt_shortspread, opt_longspread, opt_tpshort, opt_tplong, opt_stopnumber, opt_cmin, pos_size)

        return {'treino': result_treino, 'test':result_test, 'parametros':parametros, 'opt':forest}
