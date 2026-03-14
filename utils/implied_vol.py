"""
Implied Volatility Calculator for Turbo Certificates
Reverse-engineers volatility from market price
NO SCIPY VERSION - Uses custom optimization
"""

import numpy as np
from typing import Dict, Optional


def calculate_implied_volatility(
    market_price: float,
    spot: float,
    strike: float,
    days: int,
    risk_free_rate: float,
    dividend_yield: float,
    multiplo: float,
    cambio: float,
    premio_known: Optional[float] = None
) -> Dict:
    """
    Calculate implied volatility from Turbo market price
    
    Uses custom bisection optimization (no scipy dependency).
    
    Args:
        market_price: Observed market price of Turbo
        spot: Current index value
        strike: Turbo strike
        days: Days to maturity
        risk_free_rate: Risk-free rate (Euribor)
        dividend_yield: Dividend yield (annualized)
        multiplo: Certificate multiplo
        cambio: EUR/USD exchange rate
        premio_known: Optional - if fair value known separately
    
    Returns:
        Dict with:
            - vol_implicita: Implied volatility
            - fair_value: Estimated fair value
            - target_premium: Premium to match
            - success: Whether calibration succeeded
            - message: Status message
    """
    
    # Calculate Fair Value
    T = days / 360.0
    adjusted_strike = strike * np.exp(-dividend_yield * T)
    fair_value = max((adjusted_strike - spot) * multiplo / cambio, 0)
    
    # Calculate target premium
    if premio_known is not None:
        target_premium = premio_known
    else:
        target_premium = max(market_price - fair_value, 0)
    
    # If premium is zero or negative, vol doesn't make sense
    if target_premium <= 0.001:
        return {
            'vol_implicita': 0.0,
            'fair_value': fair_value,
            'target_premium': target_premium,
            'fitting_error': 0.0,
            'success': False,
            'message': 'Premio ≤ 0, certificato at/below fair value. Vol implicita non calcolabile.'
        }
    
    def estimate_premium_from_vol(vol: float) -> float:
        """
        Estimate theoretical premium given volatility
        Simplified model: Premium ≈ f(vol, time)
        """
        try:
            if vol <= 0:
                return 0
            
            # Simplified premium estimation
            # Premium increases with vol and time remaining
            T_years = days / 365.0
            
            # Base premium component (time value)
            time_component = target_premium * (T_years / 0.25)  # Normalized to 3 months
            
            # Volatility component (increases with vol)
            vol_component = vol * np.sqrt(T_years) * spot * multiplo / cambio * 0.01
            
            # Combined estimate
            estimated_premium = time_component * 0.3 + vol_component * 0.7
            
            return estimated_premium
            
        except Exception:
            return 0
    
    def objective_function(vol: float) -> float:
        """Error between estimated and target premium"""
        estimated = estimate_premium_from_vol(vol)
        return estimated - target_premium
    
    # Custom bisection search (no scipy needed)
    def bisection_search(f, a, b, tol=1e-4, max_iter=50):
        """
        Find root of function f in interval [a, b]
        """
        fa = f(a)
        fb = f(b)
        
        # If same sign, no root in interval - try to find best approximation
        if fa * fb > 0:
            # Try multiple starting points
            best_vol = 0.20  # Default
            best_error = abs(f(best_vol))
            
            for test_vol in np.linspace(a, b, 20):
                error = abs(f(test_vol))
                if error < best_error:
                    best_error = error
                    best_vol = test_vol
            
            return best_vol, best_error
        
        # Standard bisection
        for _ in range(max_iter):
            c = (a + b) / 2
            fc = f(c)
            
            if abs(fc) < tol or (b - a) / 2 < tol:
                return c, abs(fc)
            
            if fa * fc < 0:
                b = c
                fb = fc
            else:
                a = c
                fa = fc
        
        return (a + b) / 2, abs(f((a + b) / 2))
    
    # Search for vol in reasonable range [5%, 100%]
    try:
        vol_implied, final_error = bisection_search(
            objective_function,
            a=0.05,  # 5% vol
            b=1.0,   # 100% vol
            tol=1e-4,
            max_iter=50
        )
        
        # Validate result
        if vol_implied < 0.05 or vol_implied > 1.0:
            vol_implied = 0.20  # Fallback to 20%
            success = False
            message = 'Vol fuori range ragionevole. Usando default 20%.'
        else:
            success = True
            message = f'Vol implicita calibrata: {vol_implied*100:.1f}%'
        
        return {
            'vol_implicita': vol_implied,
            'fair_value': fair_value,
            'target_premium': target_premium,
            'fitting_error': final_error,
            'success': success,
            'message': message
        }
        
    except Exception as e:
        # Fallback to default
        return {
            'vol_implicita': 0.20,  # Default 20%
            'fair_value': fair_value,
            'target_premium': target_premium,
            'fitting_error': 0.0,
            'success': False,
            'message': f'Calibrazione fallita: {str(e)}. Usando vol default 20%.'
        }


def validate_implied_vol(vol: float, market_price: float, theoretical_price: float) -> Dict:
    """
    Validate quality of implied vol calibration
    
    Args:
        vol: Calibrated volatility
        market_price: Observed market price
        theoretical_price: Model price with calibrated vol
    
    Returns:
        Dict with validation metrics
    """
    error_abs = abs(theoretical_price - market_price)
    error_pct = error_abs / market_price * 100 if market_price > 0 else 0
    
    # Quality assessment
    if error_pct < 1.0:
        quality = "Eccellente"
    elif error_pct < 3.0:
        quality = "Buono"
    elif error_pct < 5.0:
        quality = "Accettabile"
    else:
        quality = "Scarso"
    
    return {
        'error_abs': error_abs,
        'error_pct': error_pct,
        'quality': quality,
        'within_1pct': error_pct < 1.0,
        'within_3pct': error_pct < 3.0,
    }
