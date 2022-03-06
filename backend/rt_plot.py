import dash
from dash.dependencies import Output, Input
import dash_core_components as dcc
import dash_html_components as html
import plotly
import random
import plotly.graph_objs as go
from plotly.subplots import make_subplots
from collections import deque
import json
from numpy import mean
import numpy as np

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash(__name__)
global fig

class rt_plot:

    def __new__(self, 
                dict_name,
                interval_time,
                period,
                symbol_x,
                symbol_y,
                HOST):

        

        app.layout = html.Div([
                        html.Div([
                            html.Div([
                                dcc.Graph(
                                    id='live-graph',
                                    animate=False),
                                dcc.Interval(
                                    id='update-graph',
                                    interval=1000,
				    n_intervals=-1)
                                    ])
                                ])
                            ], style={'backgroundColor':'white'})



        @app.callback([Output('live-graph' , 'figure')], [Input('update-graph', 'n_intervals')])

        def update_graph(input_data):

            #data    
            godhandlog = json.load(open(dict_name, 'r'))

            price_x = godhandlog['price']['x_price'][int(period)-1:]
            price_y = godhandlog['price']['y_price'][int(period)-1:]
            spread = godhandlog['spread']
            profit = godhandlog['profit']
            cumprofit = godhandlog['cumprofit']
            time = godhandlog['price']['time'][int(period)-1:]

            info = godhandlog['info']



            fig = make_subplots(rows=3, cols=1,
                                specs= [[{'secondary_y':True}], [{'secondary_y':True}],
                                       [{'secondary_y':True}]],
                                subplot_titles=('symbols','profit','spread'))

                            
            fig.data = []

            _x = [i for i in range(len(price_x))]


            fig.add_trace(go.Scatter(
                x=time,
                y=price_x,
                name=str(symbol_x),
                mode='lines',
                yaxis='y',
                xaxis='x'
            ), row=1, col=1, secondary_y=False)

            fig.add_trace(go.Scatter(
                x=time,
                y=price_y,
                name=str(symbol_y),
                mode='lines',
                yaxis='y2',
                xaxis='x2'
            ), row=1, col=1, secondary_y=True)
            
            _spread = [i for i in range(len(spread))]
            fig.add_trace(go.Scatter(
                x=time,
                y=spread,
                name='spread',
                mode='lines',
                yaxis='y3',
                xaxis='x3',
                line_color='white',
                line_width=0.5
            ), row=3, col=1, secondary_y=False)
            
            '''
            _expo = [i for i in range(len(expo))]
            fig.add_trace(go.Bar(
                x=_expo,
                y=expo,
                name='expo',
                #mode='lines',
                #yaxis='y5',
                #xaxis='x5'
            ), row=1, col=2)
            '''
            _profit = [i for i in range(len(profit))]
            fig.add_trace(go.Bar(
                x=_profit,
                y=profit,
                name='profit',
                marker_color='white'
            ), row=2, col=1, secondary_y=True)

            _cumprofit = [i for i in range(len(cumprofit))]
            fig.add_trace(go.Scatter(
                x=_cumprofit,
                y=cumprofit,
                name='cumprofit',
                mode='lines',
                xaxis='x5',
                yaxis='y5',
                line_color='green',
                fill='tozeroy'
            ), row=2, col=1, secondary_y=False)
            
            spread_cumsum = np.cumsum(spread)
            _spread_cumsum = [i for i in range(len(spread_cumsum))]
            fig.add_trace(go.Scatter(
                x=time,
                y=spread_cumsum,
                name='cumspread',
                mode='lines',
                #yaxis='y3',
                #xaxis='x3',
                line_color='purple',
                fill='tozeroy',
                line_width=0.3
            ), row=3, col=1, secondary_y=True)
            

            
            fig.update_layout(
                xaxis=dict(showticklabels=False, showgrid=False),
                xaxis2=dict(showticklabels=False, showgrid=False),
                xaxis3=dict(showticklabels=True, showgrid=False),
                


                #plot dos preços
                yaxis=dict(showgrid=False,title='', side='left', range=[(mean(price_x) - (mean(price_x)/float(70))), mean(price_x) + (mean(price_x)/float(20))], tickfont=dict(color='lightskyblue')),
                yaxis2=dict(showgrid=False,title='', side='right',anchor='y', range=[(mean(price_y) - (mean(price_y)/float(70))), mean(price_y) + (mean(price_y)/float(20))],overlaying='y', tickfont=dict(color='orange')),

                
                yaxis4 = dict(showgrid=False, side='left', range=[min(profit, default=0), max(profit, default=0)], tickfont=dict(color='gray')),
                yaxis3 = dict(showgrid=False,side='right', range=[min(cumprofit, default=0), max(cumprofit, default=0)], tickfont=dict(color='green')),


                #spread
                yaxis5 = dict(showgrid=False,range=[min(spread, default=0), max(spread, default=0)]),
                yaxis6 = dict(showgrid=False,side='right', anchor='y5',range=[min(spread_cumsum, default=0), max(spread_cumsum, default=0)], tickfont=dict(color='pink')),
                
  

            )
            
            fig.update_layout(showlegend=True, title=dict_name,template='plotly_dark')
            fig.update_layout()

            return [{'data': fig.data,'layout' :fig.layout}]


        return app.run_server(host=HOST)
