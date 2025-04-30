import datetime as dt
import pandas as pd
import numpy as np
import plotly.express as px
import scipy.optimize as sc


def _stock_performance(close):
    """Calculates expected mean returns and covariance matrix of stock returns.

    Args:
        close (pd.DataFrame): DataFrame of stock closing prices.

    Returns:
        tuple: (np.array of mean returns, np.array of covariance matrix)

    Raises:
        ValueError: If the input DataFrame is empty or has insufficient data.
        TypeError: If `close` is not a pandas DataFrame.
    """

    # Validate input type
    if not isinstance(close, pd.DataFrame):
        raise TypeError("close must be a pandas DataFrame.")

    # Check if DataFrame is empty
    if close.empty:
        raise ValueError("close DataFrame cannot be empty.")

    # Ensure there are at least two rows for percentage change calculation
    if close.shape[0] < 2:
        raise ValueError("close DataFrame must have at least two rows to calculate returns.")

    # Calculate daily returns
    returns = close.pct_change().dropna()

    # Ensure returns are still valid
    if returns.empty:
        raise ValueError("Returns calculation resulted in an empty DataFrame. Check input data.")

    # Compute mean returns and covariance matrix
    mean_returns = returns.mean().to_numpy()
    cov = returns.cov().to_numpy()

    return mean_returns, cov



def portfolio_performance(W, mean_returns, cov, n):
    """Portfolio performance: Computes the weighted average of stock returns.

    Args:
        W (list or np.array): Portfolio weights.
        mean_returns (list or np.array): Mean return vector.
        cov (np.array): Covariance matrix.
        n (int): Holding period.

    Returns:
        tuple: (portfolio_returns, portfolio_risk)

    Raises:
        ValueError: If input dimensions are inconsistent or invalid.
        TypeError: If inputs are not of the expected types.
    """

    # Convert lists to numpy arrays if necessary
    W = np.asarray(W, dtype=float)
    mean_returns = np.asarray(mean_returns, dtype=float)

    # Check types
    if not isinstance(cov, np.ndarray):
        raise TypeError("cov must be a numpy array.")
    if not isinstance(n, int) or n <= 0:
        raise ValueError("n must be a positive integer.")
    if isinstance(cov, pd.DataFrame):  
        cov = cov.to_numpy()


    # Check dimensions
    if W.ndim != 1:
        raise ValueError("W must be a one-dimensional array.")
    if mean_returns.ndim != 1:
        raise ValueError("mean_returns must be a one-dimensional array.")
    if cov.ndim != 2:
        raise ValueError("cov must be a two-dimensional matrix.")
    if W.shape[0] != mean_returns.shape[0]:
        raise ValueError("W and mean_returns must have the same length.")
    if cov.shape[0] != cov.shape[1]:
        raise ValueError("cov must be a square matrix.")
    if cov.shape[0] != W.shape[0]:
        raise ValueError("Dimension mismatch: W, mean_returns, and cov must align.")

    # Compute portfolio returns and risk
    portfolio_returns = np.dot(W, mean_returns) * n
    portfolio_risk = np.sqrt(W.T @ cov @ W) * np.sqrt(n)

    return portfolio_returns, portfolio_risk


############################
def _negative_sharpe_ratio(W, mean_returns, cov, risk_free_rate,n):
    portfolio_return, portfolio_risk = portfolio_performance(W, mean_returns, cov, n)
    neg_sharpe_ratio = -(portfolio_return - risk_free_rate)/portfolio_risk
    return neg_sharpe_ratio

def _optimize_portfolio(mean_returns, cov, upper_bound, risk_free_rate,n):
    """
    returns
    -------
    sharpe_ratio, optimal_weights
    """
    #assign random weights
    np.random.seed(1)
    W = np.random.random(len(mean_returns))
    W = [weight/ np.sum(W) for weight in W]

    #add bounds
    bound = (0,upper_bound)
    bounds = tuple(bound for w in range(len(W)))

    #constraint
    def constraint(W):
        return np.sum(W) - 1


    constraint_set = [{'type': 'eq', 'fun': constraint}]
    #minimize negative SharpeRatio
    result = sc.minimize(_negative_sharpe_ratio,
                        W,
                        args=(mean_returns, cov, risk_free_rate,n),
                        method='SLSQP',
                        bounds= bounds,
                        constraints=constraint_set)
    neg_sharpe_ratio, optimal_weights = result['fun'], result['x'].round(4)
    return -neg_sharpe_ratio, optimal_weights

def _minimum_risk_portfolio(mean_returns, cov, upper_bound, risk_free_rate,n):
    """
    returns
    -------
    sharpe_ratio, optimal_weights"""
     #assign random weights
    np.random.seed(1)
    W = np.random.random(len(mean_returns))
    W = [weight/ np.sum(W) for weight in W]

    #add bounds
    bound = (0,upper_bound)
    bounds = tuple(bound for w in range(len(W)))

    #constraint 
    def constraint(W):
        return np.sum(W) - 1
    constraint_set = [{'type': 'eq', 'fun': constraint}]
    
    def portfolio_variance(W,cov,n):
        return (np.sqrt(W.T @ cov @ W) * np.sqrt(n))

    result = sc.minimize(portfolio_variance,
                        W,
                        args = (cov,n),
                        bounds = bounds,
                        constraints = constraint_set,
                        method = 'SLSQP')

    min_risk, optimal_weights = result['fun'], result['x'].round(4)
    return min_risk, optimal_weights


def optimize(type, close, n, risk_free_rate:float,  upper_bound:float):
    """optimize portoflio weights based on the selected objective function (Sharpe or MinRisk). Note MinRisk minimizes the standard deviation of Portfolio

    Args:
        close (pd.DataFrame): DataFrame of asset closing prices.
        type (str): Optimization type ('Sharpe' or 'MinRisk').
        upper_bound (float): Upper bound for weights.
        risk_free_rate (float): Risk-free rate for Sharpe ratio calculation.
        n (int): Holding period.

    Returns:
        pd.DataFrame: DataFrame with tickers and their optimal weights.

    Raises:
        ValueError: If input parameters are invalid or inconsistent.
        TypeError: If inputs are not of the expected types.
    """

    # Validate inputs
    if not isinstance(close, pd.DataFrame):
        raise TypeError("close must be a pandas DataFrame.")
    if not isinstance(type, str) or type not in ['Sharpe', 'MinRisk']:
        raise ValueError("type must be either 'Sharpe' or 'MinRisk'.")
    if not isinstance(upper_bound, (int, float)) or upper_bound <= 0:
        raise ValueError("upper_bound must be a positive number.")
    if not isinstance(risk_free_rate, (int, float)):
        raise TypeError("risk_free_rate must be a numeric value.")
    if not isinstance(n, int) or n <= 0:
        raise ValueError("n must be a positive integer.")

    # Compute mean returns and covariance matrix
    try:
        mean_returns, cov = _stock_performance(close)
    except Exception as e:
        raise RuntimeError(f"Error in _stock_performance: {e}")

    # Select optimization method
    try:
        if type == 'Sharpe':
            metric, optimal_weights = _optimize_portfolio(mean_returns, cov, upper_bound, risk_free_rate, n)
        elif type == "MinRisk":  # type == 'MinRisk'
            metric, optimal_weights = _minimum_risk_portfolio(mean_returns, cov, upper_bound, risk_free_rate, n)
    except Exception as e:
        raise RuntimeError(f"Error in portfolio optimization: {e}")

    # Ensure optimal_weights is valid
    optimal_weights = np.asarray(optimal_weights, dtype=float)
    if optimal_weights.ndim != 1 or optimal_weights.shape[0] != mean_returns.shape[0]:
        raise ValueError("optimal_weights must be a one-dimensional array matching the number of assets.")

    # Compute portfolio performance
    try:
        portfolio_returns, portfolio_risk = portfolio_performance(optimal_weights, mean_returns, cov, n)
    except Exception as e:
        raise RuntimeError(f"Error in portfolio_performance: {e}")

    # Create DataFrame for weights
    df = pd.DataFrame({"ticker": close.columns.to_list(), "weight": optimal_weights})

    # Filter out assets with zero weight
    # best_weights = df["weight"].reset_index(drop=True)

    return df



