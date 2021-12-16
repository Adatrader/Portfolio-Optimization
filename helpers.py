import yfinance as yf
from pypfopt import EfficientFrontier
from pypfopt import risk_models
from pypfopt import expected_returns
from pypfopt import objective_functions
from pypfopt.discrete_allocation import DiscreteAllocation, get_latest_prices
import datetime


def get_historical_data(tickers):
    """
    tickers = ["MSFT", "AMZN", "KO", "MA", "COST", 
           "LUV", "XOM", "PFE", "JPM", "UNH", 
           "ACN", "DIS", "GILD", "F", "TSLA"] 
           """
    today = '{date:%Y-%m-%d}'.format(date=datetime.datetime.now())
    ohlc = yf.download(tickers, start="2017-01-01", end=today)
    prices = ohlc["Adj Close"].dropna(how="all")
    return prices


def discreet_allocation(df, weights, investment):
    latest_prices = get_latest_prices(df)

    da = DiscreteAllocation(weights, latest_prices, total_portfolio_value=investment)
    allocation, leftover = da.greedy_portfolio()
    return allocation


def sharpe_ratio(df, investment):
    # Calculate expected returns and sample covariance
    mu = expected_returns.capm_return(df)
    S = risk_models.exp_cov(df)

    # Optimize for maximal Sharpe ratio
    ef = EfficientFrontier(mu, S)
    # ef.add_objective(objective_functions.L2_reg, gamma=1)
    ef.max_sharpe()
    cleaned_weights = ef.clean_weights()
    details = ef.portfolio_performance()

    # Get discreet_allocation
    allocation = discreet_allocation(df, cleaned_weights, investment)
    data = {
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
    ef.add_objective(objective_functions.L2_reg, gamma=0.1)  # gamme is the tuning parameter
    ef.efficient_risk(target_volatility=max_volatility)
    cleaned_weights = ef.clean_weights()
    details = ef.portfolio_performance()

    # Get discreet_allocation
    allocation = discreet_allocation(df, cleaned_weights, investment)
    data = {
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
    ef.add_objective(objective_functions.L2_reg, gamma=0.1)  # gamme is the tuning parameter
    ef.min_volatility()
    cleaned_weights = ef.clean_weights()
    details = ef.portfolio_performance()

    # Get discreet_allocation
    allocation = discreet_allocation(df, cleaned_weights, investment)
    data = {
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
        "weights": dict(cleaned_weights),
        "expected_annual_return": details[0] * 100,
        "annual_volitility": details[1] * 100,
        "sharpe_ratio": details[2],
        "allocation": allocation
    }
    return data