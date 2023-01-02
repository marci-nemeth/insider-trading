import pandas as pd
import os


def fetch_insider_data(ticker, path):
    try:
        insider = pd.DataFrame()

        insider1 = pd.read_html(
            f'http://openinsider.com/screener?s={ticker}&o=&pl=&ph=&ll=&lh=&fd=1461&fdr=&td=0&tdr=&fdlyl=&fdlyh=&daysago=&xp=1&xs=1&vl=&vh=&ocl=&och=&sic1=-1&sicl=100&sich=9999&grp=0&nfl=&nfh=&nil=&nih=&nol=&noh=&v2l=&v2h=&oc2l=&oc2h=&sortcol=0&cnt=1000&page=1')
        insider1 = insider1[-3]
        insider1['company'] = ticker
        insider = pd.concat([insider, insider1])
        insider.to_csv(path+ticker+".csv")
    except Exception as e:
        print(str(e))
        pass


def fetch_sp500():
    df = pd.read_html(
        'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies')[0]
    return df


def populate_data():
    for symbol in fetch_sp500()["Symbol"]:
        try:
            fetch_insider_data(symbol)
        except Exception as e:
            print(str(e))
            pass


def gridsearch(ticker, mcap):
    """ Return dictionary of {date:signal }"""
    try:
        df = pd.read_csv(f"by_mcap//{mcap}//{ticker}.csv", index_col=0)
        df.columns = ['x', 'filing_date', 'trade_date', 'ticker', 'insider_name', 'title',
                      'trade_type', 'price', 'qty', 'owned', 'd_own', 'value', '1d', '1w',
                      '1m', '6m', 'company']

        sell_dates = df.loc[df["trade_type"].str.contains(
            "Sale")]["filing_date"]
        buy_dates = df.loc[df["trade_type"].str.contains(
            "Purchase")]["filing_date"]
        return list(sell_dates), list(buy_dates)

    except Exception as e:
        print("Error : "+str(e))
        pass
    return [], []


def backtest_strat(sell_dates, buy_dates):
    for s_date in sell_dates:
        print(f"SELL: {s_date}")
    for b_date in buy_dates:
        print(f"BUY: {b_date}")


def get_strategy(ticker):
    try:
        sell_dates, buy_dates = gridsearch(ticker)
        return sell_dates, buy_dates
    except Exception as e:
        print(str(e))
        pass
