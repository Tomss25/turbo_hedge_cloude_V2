"""
Backtesting Engine for Turbo Hedge Strategy
Simulates historical performance with automatic data download
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from utils.calculations import TurboCalculator


def run_full_backtest(
    df_historical: pd.DataFrame,
    params: Dict
) -> Dict:
    """
    Execute full backtest of Turbo hedge strategy
    
    Args:
        df_historical: DataFrame with columns:
            - Date: datetime
            - Portfolio_Value: float
            - Index_Close: float
            - Beta_Rolling: float (optional)
        params: Strategy and Turbo parameters dict
    
    Returns:
        Dict with:
            - daily_results: DataFrame with daily P&L
            - metrics: Performance metrics
            - operations: List of hedge operations
            - total_trades: Number of trades executed
    """
    
    # Extract parameters
    hedge_trigger_dd = params['hedge_trigger_dd']
    strike_offset = params['strike_offset']
    maturity_days = params['maturity_days']
    rebalance_freq = params['rebalance_freq']
    hedge_size_pct = params['hedge_size_pct']
    
    # Initialize state variables
    results = []
    operations = []
    hedge_active = False
    hedge_position = None
    days_in_position = 0
    total_trades = 0
    
    # Loop through each day
    for idx in range(len(df_historical)):
        row = df_historical.iloc[idx]
        date = row['Date']
        portfolio_value = row['Portfolio_Value']
        index_value = row['Index_Close']
        beta = row.get('Beta_Rolling', params.get('beta', 1.0))
        
        # ========================================
        # CALCULATE DRAWDOWN
        # ========================================
        
        peak_value = df_historical.loc[:idx, 'Portfolio_Value'].max()
        current_dd = (portfolio_value - peak_value) / peak_value * 100 if peak_value > 0 else 0
        
        # ========================================
        # HEDGE OPENING LOGIC
        # ========================================
        
        if not hedge_active and current_dd <= hedge_trigger_dd:
            # OPEN HEDGE
            
            strike = index_value * (1 + strike_offset)
            
            # Setup Turbo parameters
            turbo_params = {
                'prezzo_iniziale': params['prezzo_turbo_input'],
                'strike': strike,
                'cambio': params['cambio'],
                'multiplo': params['multiplo'],
                'euribor': params['euribor'],
                'valore_iniziale_indice': index_value,
                'valore_ipotetico_indice': index_value * 0.95,  # -5% scenario
                'giorni': maturity_days,
                'valore_portafoglio': portfolio_value,
                'beta': beta,
                'dividend_yield': params['dividend_yield'],
                'bid_ask_spread': params['bid_ask_spread'],
                'commissioni': params['commissioni'],
                'tasse': params['tasse'],
                'decay_exponent': params.get('decay_exponent', 1.5),
            }
            
            calc = TurboCalculator(turbo_params)
            hedge_result = calc.calculate_hedge_results()
            
            # Size hedge position
            capital_allocated = portfolio_value * hedge_size_pct
            n_turbo = capital_allocated / params['prezzo_turbo_input'] if params['prezzo_turbo_input'] > 0 else 0
            
            hedge_position = {
                'entry_date': date,
                'entry_index': index_value,
                'entry_portfolio': portfolio_value,
                'entry_dd': current_dd,
                'strike': strike,
                'barrier': hedge_result['barrier_future'],
                'maturity_date': date + pd.Timedelta(days=maturity_days),
                'n_turbo': n_turbo,
                'entry_price_turbo': params['prezzo_turbo_input'],
                'capital_invested': capital_allocated,
                'initial_calculator': calc,
            }
            
            hedge_active = True
            days_in_position = 0
            total_trades += 1
            
            operations.append({
                'Date': date,
                'Action': 'OPEN',
                'Index': index_value,
                'Strike': strike,
                'Barrier': hedge_result['barrier_future'],
                'N_Turbo': n_turbo,
                'Capital': capital_allocated,
                'DD_%': current_dd,
            })
        
        # ========================================
        # EVALUATE ACTIVE POSITION
        # ========================================
        
        if hedge_active:
            days_in_position += 1
            
            # Check knock-out
            if index_value <= hedge_position['barrier']:
                # KNOCKED OUT!
                turbo_value = 0
                turbo_pl = -hedge_position['capital_invested']
                hedge_active = False
                close_reason = "Knock-Out"
                
                operations.append({
                    'Date': date,
                    'Action': 'CLOSE_KO',
                    'Index': index_value,
                    'Days_Held': days_in_position,
                    'Exit_Value': 0,
                    'PL': turbo_pl,
                    'PL_%': turbo_pl / hedge_position['capital_invested'] * 100,
                })
            
            # Check maturity
            elif date >= hedge_position['maturity_date']:
                # MATURED
                calc = hedge_position['initial_calculator']
                final_price = calc.calculate_fair_value(index_value)
                turbo_value = final_price * hedge_position['n_turbo']
                
                # Apply exit costs
                exit_costs = turbo_value * (params['bid_ask_spread'] + params['commissioni']) / 100
                turbo_value_net = turbo_value - exit_costs
                
                turbo_pl = turbo_value_net - hedge_position['capital_invested']
                hedge_active = False
                close_reason = "Maturity"
                
                operations.append({
                    'Date': date,
                    'Action': 'CLOSE_MATURITY',
                    'Index': index_value,
                    'Days_Held': days_in_position,
                    'Exit_Value': turbo_value_net,
                    'PL': turbo_pl,
                    'PL_%': turbo_pl / hedge_position['capital_invested'] * 100,
                })
            
            # Check rebalancing
            elif days_in_position >= rebalance_freq:
                # REBALANCE
                days_remaining = max((hedge_position['maturity_date'] - date).days, 1)
                
                # Calculate current Turbo value
                turbo_params_current = {
                    **turbo_params,
                    'valore_iniziale_indice': index_value,
                    'giorni': days_remaining,
                    'valore_portafoglio': portfolio_value,
                    'beta': beta,
                }
                
                calc_current = TurboCalculator(turbo_params_current)
                current_price = calc_current.calculate_fair_value(index_value)
                turbo_value = current_price * hedge_position['n_turbo']
                
                # Apply exit costs
                exit_costs = turbo_value * (params['bid_ask_spread'] + params['commissioni']) / 100
                turbo_value_net = turbo_value - exit_costs
                
                turbo_pl = turbo_value_net - hedge_position['capital_invested']
                
                operations.append({
                    'Date': date,
                    'Action': 'CLOSE_REBALANCE',
                    'Index': index_value,
                    'Days_Held': days_in_position,
                    'Exit_Value': turbo_value_net,
                    'PL': turbo_pl,
                    'PL_%': turbo_pl / hedge_position['capital_invested'] * 100,
                })
                
                hedge_active = False  # Will reopen if DD still high
                close_reason = "Rebalance"
            
            # Check drawdown recovery
            elif current_dd > -2.0:  # Recovered to -2%
                # CLOSE DUE TO RECOVERY
                days_remaining = max((hedge_position['maturity_date'] - date).days, 1)
                
                turbo_params_current = {
                    **turbo_params,
                    'valore_iniziale_indice': index_value,
                    'giorni': days_remaining,
                }
                
                calc_current = TurboCalculator(turbo_params_current)
                current_price = calc_current.calculate_fair_value(index_value)
                turbo_value = current_price * hedge_position['n_turbo']
                
                # Apply exit costs
                exit_costs = turbo_value * (params['bid_ask_spread'] + params['commissioni']) / 100
                turbo_value_net = turbo_value - exit_costs
                
                turbo_pl = turbo_value_net - hedge_position['capital_invested']
                
                operations.append({
                    'Date': date,
                    'Action': 'CLOSE_RECOVERY',
                    'Index': index_value,
                    'Days_Held': days_in_position,
                    'Exit_Value': turbo_value_net,
                    'PL': turbo_pl,
                    'PL_%': turbo_pl / hedge_position['capital_invested'] * 100,
                })
                
                hedge_active = False
                close_reason = "DD Recovery"
            
            else:
                # CONTINUE HOLDING - Mark to Market
                days_remaining = max((hedge_position['maturity_date'] - date).days, 1)
                
                turbo_params_mtm = {
                    **turbo_params,
                    'valore_iniziale_indice': index_value,
                    'giorni': days_remaining,
                }
                
                calc_mtm = TurboCalculator(turbo_params_mtm)
                mtm_price = calc_mtm.calculate_fair_value(index_value)
                turbo_value = mtm_price * hedge_position['n_turbo']
                turbo_pl = turbo_value - hedge_position['capital_invested']  # Unrealized
                close_reason = None
        
        else:
            # No active hedge
            turbo_value = 0
            turbo_pl = 0
            close_reason = None
        
        # ========================================
        # RECORD DAILY RESULT
        # ========================================
        
        results.append({
            'Date': date,
            'Portfolio_Unhedged': portfolio_value,
            'Portfolio_Hedged': portfolio_value + turbo_pl,
            'Index_Value': index_value,
            'Drawdown_%': current_dd,
            'Hedge_Active': hedge_active,
            'Turbo_Value': turbo_value,
            'Turbo_PL': turbo_pl,
            'Days_In_Position': days_in_position if hedge_active else 0,
            'Close_Reason': close_reason if close_reason else '',
            'Beta': beta,
        })
    
    # ========================================
    # CALCULATE FINAL METRICS
    # ========================================
    
    df_results = pd.DataFrame(results)
    metrics = calculate_performance_metrics(df_results)
    
    return {
        'daily_results': df_results,
        'metrics': metrics,
        'operations': pd.DataFrame(operations) if operations else pd.DataFrame(),
        'total_trades': total_trades,
        'params': params,
    }


def calculate_performance_metrics(df: pd.DataFrame) -> Dict:
    """
    Calculate standard performance metrics
    
    Args:
        df: DataFrame with daily results
    
    Returns:
        Dict with performance metrics
    """
    # Returns
    df['Return_Unhedged'] = df['Portfolio_Unhedged'].pct_change()
    df['Return_Hedged'] = df['Portfolio_Hedged'].pct_change()
    
    # Total returns
    total_return_unhedged = (df['Portfolio_Unhedged'].iloc[-1] / df['Portfolio_Unhedged'].iloc[0] - 1) * 100
    total_return_hedged = (df['Portfolio_Hedged'].iloc[-1] / df['Portfolio_Hedged'].iloc[0] - 1) * 100
    
    # Annualized returns
    years = len(df) / 252
    ann_return_unhedged = ((1 + total_return_unhedged/100) ** (1/years) - 1) * 100 if years > 0 else 0
    ann_return_hedged = ((1 + total_return_hedged/100) ** (1/years) - 1) * 100 if years > 0 else 0
    
    # Volatility (annualized)
    vol_unhedged = df['Return_Unhedged'].std() * np.sqrt(252) * 100
    vol_hedged = df['Return_Hedged'].std() * np.sqrt(252) * 100
    
    # Sharpe Ratio (assume rf=0 for simplicity)
    sharpe_unhedged = ann_return_unhedged / vol_unhedged if vol_unhedged > 0 else 0
    sharpe_hedged = ann_return_hedged / vol_hedged if vol_hedged > 0 else 0
    
    # Max Drawdown
    def calc_max_dd(series):
        cum = (1 + series.fillna(0)).cumprod()
        running_max = cum.expanding().max()
        dd = (cum - running_max) / running_max
        return dd.min() * 100
    
    maxdd_unhedged = calc_max_dd(df['Return_Unhedged'])
    maxdd_hedged = calc_max_dd(df['Return_Hedged'])
    
    # Downside deviation
    downside_unhedged = df[df['Return_Unhedged'] < 0]['Return_Unhedged'].std() * np.sqrt(252) * 100
    downside_hedged = df[df['Return_Hedged'] < 0]['Return_Hedged'].std() * np.sqrt(252) * 100
    
    # Sortino Ratio
    sortino_unhedged = ann_return_unhedged / downside_unhedged if downside_unhedged > 0 else 0
    sortino_hedged = ann_return_hedged / downside_hedged if downside_hedged > 0 else 0
    
    # Win rate
    winning_days_unhedged = (df['Return_Unhedged'] > 0).sum()
    winning_days_hedged = (df['Return_Hedged'] > 0).sum()
    total_days = len(df)
    
    win_rate_unhedged = winning_days_unhedged / total_days * 100 if total_days > 0 else 0
    win_rate_hedged = winning_days_hedged / total_days * 100 if total_days > 0 else 0
    
    # Hedge statistics
    hedge_active_days = df['Hedge_Active'].sum()
    hedge_active_pct = hedge_active_days / total_days * 100 if total_days > 0 else 0
    
    avg_turbo_pl = df[df['Turbo_PL'] != 0]['Turbo_PL'].mean() if (df['Turbo_PL'] != 0).any() else 0
    total_turbo_pl = df['Turbo_PL'].iloc[-1] if len(df) > 0 else 0
    
    # Calmar Ratio (return / max drawdown)
    calmar_unhedged = abs(ann_return_unhedged / maxdd_unhedged) if maxdd_unhedged != 0 else 0
    calmar_hedged = abs(ann_return_hedged / maxdd_hedged) if maxdd_hedged != 0 else 0
    
    return {
        'total_return_unhedged': total_return_unhedged,
        'total_return_hedged': total_return_hedged,
        'ann_return_unhedged': ann_return_unhedged,
        'ann_return_hedged': ann_return_hedged,
        'vol_unhedged': vol_unhedged,
        'vol_hedged': vol_hedged,
        'sharpe_unhedged': sharpe_unhedged,
        'sharpe_hedged': sharpe_hedged,
        'sortino_unhedged': sortino_unhedged,
        'sortino_hedged': sortino_hedged,
        'maxdd_unhedged': maxdd_unhedged,
        'maxdd_hedged': maxdd_hedged,
        'calmar_unhedged': calmar_unhedged,
        'calmar_hedged': calmar_hedged,
        'win_rate_unhedged': win_rate_unhedged,
        'win_rate_hedged': win_rate_hedged,
        'hedge_active_pct': hedge_active_pct,
        'avg_turbo_pl': avg_turbo_pl,
        'total_turbo_pl': total_turbo_pl,
    }


def download_historical_data(
    portfolio_ticker: str,
    index_ticker: str,
    start_date: str,
    end_date: str,
    interval: str = "1d"
) -> pd.DataFrame:
    """
    Download historical data from Yahoo Finance
    
    Args:
        portfolio_ticker: Ticker for portfolio proxy (e.g., 'SPY')
        index_ticker: Ticker for index (e.g., '^GSPC')
        start_date: Start date 'YYYY-MM-DD'
        end_date: End date 'YYYY-MM-DD'
        interval: Data frequency ('1d', '1wk', '1mo')
    
    Returns:
        DataFrame with Date, Portfolio_Value, Index_Close
    """
    import yfinance as yf
    
    # Download portfolio
    df_portfolio = yf.download(
        portfolio_ticker,
        start=start_date,
        end=end_date,
        interval=interval,
        progress=False
    )
    
    # Download index
    df_index = yf.download(
        index_ticker,
        start=start_date,
        end=end_date,
        interval=interval,
        progress=False
    )
    
    # Extract Close prices
    df_portfolio = df_portfolio[['Close']].rename(columns={'Close': 'Portfolio_Value'})
    df_index = df_index[['Close']].rename(columns={'Close': 'Index_Close'})
    
    # Merge
    df = df_portfolio.join(df_index, how='inner')
    df = df.dropna()
    df.reset_index(inplace=True)
    
    return df
