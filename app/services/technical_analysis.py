import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

class TechnicalAnalysis:
    @staticmethod
    def calculate_indicators(df, ema_period=14, sma_period=50):
        df['EMA'] = df['Close'].ewm(span=ema_period).mean()
        df['SMA'] = df['Close'].rolling(window=sma_period).mean()
        return df

    @staticmethod
    def create_chart(df, symbol, ema_period=14, sma_period=50):
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                           vertical_spacing=0.03, 
                           subplot_titles=(f'{symbol} Price', 'Volume'),
                           row_heights=[0.7, 0.3])

        # Candlestick
        fig.add_trace(go.Candlestick(x=df.index,
                                    open=df['Open'],
                                    high=df['High'],
                                    low=df['Low'],
                                    close=df['Close'],
                                    name='OHLC'),
                     row=1, col=1)

        # EMA
        fig.add_trace(go.Scatter(x=df.index, 
                                y=df['EMA'],
                                name=f'EMA{ema_period}',
                                line=dict(color='orange')),
                     row=1, col=1)

        # SMA
        fig.add_trace(go.Scatter(x=df.index, 
                                y=df['SMA'],
                                name=f'SMA{sma_period}',
                                line=dict(color='blue')),
                     row=1, col=1)

        # Volume
        fig.add_trace(go.Bar(x=df.index,
                            y=df['Volume'],
                            name='Volume'),
                     row=2, col=1)

        fig.update_layout(
            title=f'{symbol} Technical Analysis (EMA{ema_period}/SMA{sma_period})',
            yaxis_title='Price',
            yaxis2_title='Volume',
            xaxis_rangeslider_visible=False,
            height=800
        )

        return fig.to_json() 