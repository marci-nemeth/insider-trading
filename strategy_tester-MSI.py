from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
import os
import os.path
from pandas.core.arrays.categorical import Categorical
from insider_methods import *
import pandas as pd
import backtrader as bt
import itertools
from collections import Counter
import pandas_datareader.data as web
import datetime as dt
import time
import threading
import plotly.graph_objects as go
from plotly import tools
import plotly.offline as py
import plotly.express as px

global short_period
short_period = 5


class pandasDataFeed(bt.feeds.PandasData):

    params = (
        ('fromdate', dt.datetime(2020, 1, 1)),
        ('todate', dt.datetime.now()),
        ('dtformat', '%Y-%m-%d'),
        ('datetime', None),
        ('high', 'High'),
        ('low', 'Low'),
        ('open', 'Open'),
        ('close', 'Close'),
        ('volume', 'Volume')
    )


def get_ticker_historic(ticker, offline=True):
    if offline == True:
        try:
            df = pd.read_csv(f"data//stock_data//{ticker}.csv",
                             parse_dates=True,
                             index_col=0)
            return df
        except Exception as e:
            print(str(e))
            try:
                start = dt.datetime(2017, 8, 1)
                end = dt.datetime(2021, 8, 1)
                df = web.DataReader(ticker, "yahoo", start, end)
                df.to_csv(f"data//stock_data//{ticker}.csv")
                print(f"Fetched data from yfinance for {ticker}")
                time.sleep(0.3)
                return df

            except Exception as e:
                print("Couldnt get data from yfinance:"+str(e))
                pass


class TestStrategy(bt.Strategy):
    """
    Boilerplate Backtrader class to run the simulation.
    Called with Cerebro to test strategies

    :inherit: backtrader.Strategy
    :param ticker: String, the stock ticker
    :param mcap: Float, market cap of the company
    """

    def log(self, txt, dt=None):
        dt = dt or self.datas[0].datetime.date(0)
        #print('%s, %s' % (dt.isoformat(), txt))

    def __init__(self):
        self.dataclose = self.datas[0].close
        self.short_close = []
        self.sell_d, self.buy_d = gridsearch(ticker, mcap)
        self.order = None
        self.short_period = 1
        self.tradeid = itertools.cycle([0, 1, 2])

    def next(self):
        dat = self.datas[0].datetime.date(0)

        if not self.position:
            for s_date in self.sell_d:
                if dt.datetime.strptime(s_date.split(" ")[0], '%Y-%m-%d').strftime('%Y-%m-%d') == dat.strftime('%Y-%m-%d'):
                    self.curtradeid = next(self.tradeid)
                    self.order = self.sell(
                        tradeid=self.curtradeid)
                    self.log(f"SELL CREATE {self.dataclose[0]:2f}")
            for b_date in self.buy_d:
                if dt.datetime.strptime(b_date.split(" ")[0], '%Y-%m-%d').strftime('%Y-%m-%d') == dat.strftime('%Y-%m-%d'):
                    self.curtradeid = next(self.tradeid)
                    self.order = self.buy(
                        tradeid=self.curtradeid)
                    self.log(f"BUY CREATE {self.dataclose[0]:2f}")
        else:
            if len(self) >= (self.bar_executed+self.short_period):
                self.log(f'CLOSE CREATE {self.dataclose[0]:2f}')
                self.order = self.close(tradeid=self.curtradeid)

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            return

        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(f'BUY EXECUTED, {order.executed.price:.2f}')
            elif order.issell():
                self.log(f'SELL EXECUTED, {order.executed.price:.2f}')
            self.bar_executed = len(self)

        elif order.status in [order.Canceled,
                              order.Margin, order.Rejected]:
            self.log('Order Canceled/Margin/Rejected')

        self.order = None


def categorize_by_mcap(df=pd.read_csv("data//nasdaq_tickers.csv")):
    """
    Categorizes tickers based on market cap into 6 categories
    :param df: A DataFrame containing tickers and markcap values
    :return none: No return, displays the value count though.
    Only needs to be called once
    """
    markcap_points = {
        "mega": [200, 999_999],
        "big": [10, 19999],
        "mid": [2, 9.999],
        "small": [0.3, 1.999],
        "micro": [0.05, 0.2999],
        "nano": [0, 0.0499]
    }

    def markcap_pointer(mc):
        for cat in markcap_points.keys():

            if float(mc/1_000_000_000) > markcap_points[cat][0] and float(mc/1_000_000_000) < markcap_points[cat][1]:
                return cat

    df["markcap_cat"] = df["Market Cap"].map(markcap_pointer)
    print(df["markcap_cat"].value_counts())


def test_ticker(file, current_dir):
    """
    Tests strategy with class TestStrategy.
    :param file: String, ticker of the company
    :param current_dir: String, the directory name, which is also the markcap category
    :return profit_loss: Float, percentage return on tested strategy
    """
    global ticker
    global mcap
    mcap = current_dir
    ticker = file
    data_feed = get_ticker_historic(ticker)
    cerebro = bt.Cerebro()
    cerebro.addstrategy(TestStrategy)

    if not data_feed is None:
        if "Adj Close" in data_feed.columns:
            try:
                data_feed = data_feed.drop(["Adj Close"])
            except:
                pass

        data = pandasDataFeed(dataname=data_feed)
        cerebro.adddata(data)
        cerebro.broker.setcash(1000.0)
        cerebro.broker.setcommission(commission=0.0)
        start_val = cerebro.broker.getvalue()
        cerebro.run()
        end_val = cerebro.broker.getvalue()
        cerebro.plot()
        profit_loss = (end_val-start_val)/start_val * 100
        print(f"Profit/loss: {profit_loss}")
        return profit_loss


if __name__ == '__main__':
    test_ticker("AMZN", "mega")
    for current_dir in os.listdir("by_mcap"):
        pass
        print(current_dir+"\n\n\n")
        d = len(os.listdir("by_mcap//"+current_dir))
        df = pd.read_csv("data//nasdaq_tickers.csv")
        df_to_save = df[["Symbol", "Market Cap", "Industry"]]
        symbol_list = [f[:-4]
                       for f in os.listdir(f"by_mcap//{current_dir}")]
        df_to_save = df_to_save[df["Symbol"].isin(symbol_list)]
        print(df_to_save.reset_index())

        df_to_save["pl5"] = df_to_save["Symbol"].apply(
            lambda x: test_ticker(x, current_dir),)
        df_to_save.to_csv(f"{current_dir}_meta_pl.csv")
