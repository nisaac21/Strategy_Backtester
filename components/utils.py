import pandas as pd
import numpy as np
from datetime import datetime
import sqlite3
from components.const import DATABASE_PATH

conn = sqlite3.connect(DATABASE_PATH)


def _overall_return(equity_timeseries: pd.DataFrame, starting_capital: int):
    """Return the overall return generated by the strategy"""
    return (equity_timeseries['Equity'].iloc[-1] / starting_capital) - 1


def _cagr(equity_timeseries: pd.DataFrame, starting_capital: int) -> float:
    """Returns the """
    start_date = datetime.strptime(
        str(equity_timeseries['Date'].iloc[0]), '%Y%m%d')
    end_date = datetime.strptime(
        str(equity_timeseries['Date'].iloc[-1]), '%Y%m%d')
    time_difference = end_date - start_date

    periods = time_difference.days / 365.25  # Accounting for leap years

    return (equity_timeseries['Equity'].iloc[-1] / starting_capital) ** (1 / periods) - 1


def _std(equity_timeseries: pd.DataFrame) -> float:
    """Returns the standard deviation of the timeseries"""
    returns = equity_timeseries['Equity'].pct_change()

    return returns.std()


def _downside_deviation(equity_timeseries: pd.DataFrame, minimum_threshold: int = 0) -> float:
    """Returns the downside deviation (measure of downside risk that focuses on returns that fall 
    below a minimum threshold or minimum acceptable return) of equity timeseries """
    returns = equity_timeseries['Equity'].pct_change()
    downside_returns = returns[returns < minimum_threshold]

    squared_deviations = (downside_returns - minimum_threshold) ** 2

    return np.sqrt(squared_deviations.mean())


def _sharpe_ratio(equity_timeseries: pd.DataFrame) -> float:
    """Returns annualized sharpe ratio for a daily time series dataframe"""

    portfolio_data = equity_timeseries.copy()

    portfolio_data['Date'] = pd.to_datetime(
        portfolio_data['Date'], format='%Y%m%d')
    portfolio_data['Daily_Return'] = portfolio_data['Equity'].pct_change()

    risk_free_rates = pd.read_sql('SELECT * FROM TB3MS', con=conn)
    risk_free_rates['Date'] = pd.to_datetime(risk_free_rates['Date'])

    merged_data = pd.merge(
        portfolio_data, risk_free_rates, on='Date', how='left')
    merged_data.loc[0, 'Rate'] = risk_free_rates.loc[0, 'Rate']
    merged_data = merged_data.ffill()
    # convert the rates into daily
    merged_data['Daily_Rate'] = (
        1 + (merged_data['Rate'] / 100) / 365) ** (1/91) - 1

    merged_data['Excess_Return'] = portfolio_data['Daily_Return'] - \
        merged_data['Daily_Rate']

    # annualizing sharpe ratio
    return (merged_data['Excess_Return'].mean() / merged_data['Excess_Return'].std()) * (252 ** 0.5)


def _max_drawdown(equity_timeseries: pd.DataFrame) -> float:
    """Returns the worst drawdown in the equity timeseries"""

    rolling_max = equity_timeseries['Equity'].cummax()

    drawdown = (equity_timeseries['Equity'] -
                rolling_max) / rolling_max

    return drawdown.min()


def _extreme_month_return(equity_timeseries: pd.DataFrame) -> dict:
    """Calculates the extreme month returns (best and worst)"""
    data = equity_timeseries.copy()
    data['Date'] = pd.to_datetime(data['Date'], format='%Y%m%d')
    data.set_index('Date', inplace=True)

    # Calculate the monthly percentage change based on closing prices
    monthly_returns = data['Equity'].resample('M').last().pct_change()

    return {'best': monthly_returns.max(), 'worst': monthly_returns.min()}


def _profitable_months(equity_timeseries: pd.DataFrame) -> float:
    data = equity_timeseries.copy()  # Replace with your file path
    data['Date'] = pd.to_datetime(data['Date'], format='%Y%m%d')
    data.set_index('Date', inplace=True)

    # Calculate the monthly percentage change based on closing prices
    monthly_returns = data['Equity'].resample('M').last().pct_change()

    # Count the number of profitable months (positive percentage change)
    profitable_months = (monthly_returns > 0).sum()

    # Calculate the total number of months
    total_months = len(monthly_returns)

    # Calculate the percentage of profitable months
    return (profitable_months / total_months)


def _get_statistics(equity_timeseries: pd.DataFrame, starting_capital: int) -> dict:
    """Returns relevant statistics"""

    extreme_month_returns = _extreme_month_return(equity_timeseries)

    return {
        'Overall Return': f"{round(_overall_return(equity_timeseries, starting_capital) * 100, 2):,} %",
        'CAGR': f"{round(_cagr(equity_timeseries, starting_capital)*100, 2)} %",
        'Standard Deviation': f"{round(_std(equity_timeseries) * 100, 2)} %",
        'Downside Deviation': f"{round(_downside_deviation(equity_timeseries) * 100, 2)}%",
        'Sharpe Ratio': round(_sharpe_ratio(equity_timeseries), 2),
        'Max Drawdown': f"{round(_max_drawdown(equity_timeseries) * 100, 2)}%",
        'Worst Month Return': f"{round(extreme_month_returns['worst'] * 100, 2)} %",
        'Best Month Return': f"{round(extreme_month_returns['best'] * 100, 2)} %",
        'Profitable Months': f"{round(_profitable_months(equity_timeseries) * 100, 2)} %"
    }


def _strategy_table_convention(look_back, lottery_window, rebalance, firms_held):
    return f'equity_lw{lottery_window}_lb{look_back}_reb{rebalance}_fh{firms_held}'
