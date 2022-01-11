from pypfopt import EfficientFrontier
from pypfopt import risk_models
from pypfopt import expected_returns
from pypfopt import objective_functions
from pypfopt.discrete_allocation import DiscreteAllocation, get_latest_prices
from datetime import date, datetime
import json
from urllib.request import urlopen
import pandas as pd
from config import FMP_KEY


def customETF():
    qqqResponse = urlopen(
        f'https://financialmodelingprep.com/api/v3/etf-holder/QQQ?apikey={FMP_KEY}')
    spyResponse = urlopen(
        f'https://financialmodelingprep.com/api/v3/etf-holder/SPY?apikey={FMP_KEY}')
    qqqData = qqqResponse.read().decode("utf-8")
    spyData = spyResponse.read().decode("utf-8")
    qqqJsonRes = json.loads(qqqData)
    spyJsonRes = json.loads(spyData)
    customEtfSet = set()
    if qqqJsonRes and spyJsonRes:
        # Get rank 25-55 top allocations in SPY & QQQ = ~60 stocks
        for i in range(25, 55):
            customEtfSet.add(qqqJsonRes[i]["asset"])
        for i in range(25, 55):
            customEtfSet.add(spyJsonRes[i]["asset"])
    return list(customEtfSet)

# Uses prior 3 years of data
def get_historical_data(tickers, start='2018-01-03', end=date.today()):
    """
    tickers = ["MSFT", "AMZN", "KO", "MA", "COST", 
           "LUV", "XOM", "PFE", "JPM", "UNH", 
           "ACN", "DIS", "GILD", "F", "TSLA"] 
    Parameters:
    to : YYYY-MM-DD
    from : YYYY-MM-DD
    timeseries : Number (return last x days)
    serietype : line | bar
    """
    if (len(tickers) == 1):
        response = urlopen(
            f"https://financialmodelingprep.com/api/v3/historical-price-full/{str(tickers[0])}?from={start}&to={end}&apikey={FMP_KEY}")
        data = response.read().decode("utf-8")
        jsonRes = json.loads(data)
        df = pd.json_normalize(jsonRes, 'historical')
        df.set_index('date', inplace=True)
        prices = df[::-1]
        return prices["adjClose"].dropna(how='all')
    else:
        _DFS = {}
        for ticker in tickers:
            response = urlopen(
                f"https://financialmodelingprep.com/api/v3/historical-price-full/{str(ticker)}?from={start}&to={end}&apikey={FMP_KEY}")
            data = response.read().decode("utf-8")
            jsonRes = json.loads(data)
            _DFS[ticker] = pd.json_normalize(jsonRes, 'historical')
        df = pd.concat(_DFS.values(), axis=1,
                       keys=_DFS.keys())
        df.columns = df.columns.swaplevel(0, 1)
        df.sort_index(level=0, axis=1, inplace=True)
        df.set_index(('date', tickers[0]), inplace=True)
        df.index.rename('Date', inplace=True)
        prices = df[::-1]
        return prices["adjClose"].dropna(how='all')
    

def discreet_allocation(df, weights, investment):
    latest_prices = get_latest_prices(df)

    da = DiscreteAllocation(weights, latest_prices, total_portfolio_value=investment)
    allocation, _ = da.greedy_portfolio()
    return allocation


def sharpe_ratio(df, investment):
    # Calculate expected returns and sample covariance
    mu = expected_returns.capm_return(df)
    S = risk_models.exp_cov(df, span=180) # Default exponential weighting 180

    # Optimize for maximal Sharpe ratio
    ef = EfficientFrontier(mu, S)
    # ef.add_objective(objective_functions.L2_reg, gamma=1)
    ef.max_sharpe()
    cleaned_weights = ef.clean_weights()
    details = ef.portfolio_performance()

    # Get discreet_allocation
    allocation = discreet_allocation(df, cleaned_weights, investment)
    data = {
        "start_date": '{year}{date:-%m-%d}'.format(year=datetime.now().year-4, date=datetime.now()),
        "end_date": '{date:%Y-%m-%d}'.format(date=datetime.now()),
        "weights": dict(cleaned_weights),
        "expected_annual_return": details[0] * 100,
        "annual_volitility": details[1] * 100,
        "sharpe_ratio": details[2],
        "allocation": allocation
    }
    return data

def optimized_for_volatility(df, investment, max_volatility):
    mu = expected_returns.capm_return(df)
    S = risk_models.CovarianceShrinkage(df).ledoit_wolf()
    ef = EfficientFrontier(mu, S)
    # ef.add_objective(objective_functions.L2_reg, gamma=0.1)  # gamma is the tuning parameter
    ef.efficient_risk(target_volatility=max_volatility)
    cleaned_weights = ef.clean_weights()
    details = ef.portfolio_performance()

    # Get discreet_allocation
    allocation = discreet_allocation(df, cleaned_weights, investment)
    data = {
        "start_date": '{year}{date:-%m-%d}'.format(year=datetime.now().year-4, date=datetime.now()),
        "end_date": '{date:%Y-%m-%d}'.format(date=datetime.now()),
        "weights": dict(cleaned_weights),
        "expected_annual_return": details[0] * 100,
        "annual_volitility": details[1] * 100,
        "sharpe_ratio": details[2],
        "allocation": allocation
    }
    return data

def min_volatility(df, investment):
    mu = expected_returns.capm_return(df)
    S = risk_models.CovarianceShrinkage(df).ledoit_wolf()
    ef = EfficientFrontier(mu, S)
    # ef.add_objective(objective_functions.L2_reg, gamma=0.1)  # gamma is the tuning parameter
    ef.min_volatility()
    cleaned_weights = ef.clean_weights()
    details = ef.portfolio_performance()

    # Get discreet_allocation
    allocation = discreet_allocation(df, cleaned_weights, investment)
    data = {
        "start_date": '{year}{date:-%m-%d}'.format(year=datetime.now().year-4, date=datetime.now()),
        "end_date": '{date:%Y-%m-%d}'.format(date=datetime.now()),
        "weights": dict(cleaned_weights),
        "expected_annual_return": details[0] * 100,
        "annual_volitility": details[1] * 100,
        "sharpe_ratio": details[2],
        "allocation": allocation
    }
    return data

def optimized_for_return(df, investment, target_return):
    mu = expected_returns.capm_return(df)
    semicov = risk_models.semicovariance(df, benchmark=0)
    ef = EfficientFrontier(mu, semicov)
    ef.efficient_return(target_return=target_return)
    cleaned_weights = ef.clean_weights()
    details = ef.portfolio_performance()

     # Get discreet_allocation
    allocation = discreet_allocation(df, cleaned_weights, investment)
    data = {
        "start_date": '{year}{date:-%m-%d}'.format(year=datetime.now().year-4, date=datetime.now()),
        "end_date": '{date:%Y-%m-%d}'.format(date=datetime.now()),
        "weights": dict(cleaned_weights),
        "expected_annual_return": details[0] * 100,
        "annual_volitility": details[1] * 100,
        "sharpe_ratio": details[2],
        "allocation": allocation
    }
    return data