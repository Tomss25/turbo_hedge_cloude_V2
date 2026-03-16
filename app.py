"""
Turbo Hedge Calculator - Streamlit Web App
Professional tool for Turbo Short certificate hedging strategy
"""

import streamlit as st
import pandas as pd
import numpy as np
from pathlib import Path
import urllib.error

# Import custom modules
from utils import TurboCalculator, GreeksCalculator, MonteCarloSimulator, StrategyOptimizer
from components import (
    create_time_evolution_chart, create_spot_barrier_chart, create_premium_decay_chart,
    create_scenario_analysis_chart, create_monte_carlo_histogram, create_heatmap_strike_maturity,
    create_sensitivity_chart, create_greeks_chart, generate_scenario_table,
    generate_scenario_summary, create_stress_test_table
)
from utils.optimization import sensitivity_to_spot

# Page configuration
st.set_page_config(
    page_title="Turbo Hedge Calculator",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load custom CSS v2 (Modern Professional Theme)
def load_css():
    css_file = Path(__file__).parent / "assets" / "style_v2.css"
    if css_file.exists():
        with open(css_file) as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
    else:
        # Fallback to original
        css_file_old = Path(__file__).parent / "assets" / "style.css"
        if css_file_old.exists():
            with open(css_file_old) as f:
                st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

load_css()

# ============================================================================
# HEADER - Modern Professional Design
# ============================================================================

st.markdown("""
<div style='text-align: center; padding: 2.5rem 0 1.5rem 0;'>
    <h1 style='font-size: 3.5rem; margin: 0; 
               background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
               -webkit-background-clip: text; 
               -webkit-text-fill-color: transparent;
               background-clip: text;
               font-weight: 800;
               letter-spacing: -0.03em;'>
        📊 Turbo Hedge Calculator
    </h1>
    <p style='color: #718096; font-size: 1.3rem; margin-top: 0.75rem; font-weight: 500; letter-spacing: 0.01em;'>
        Professional Portfolio Hedging with Turbo Short Certificates
    </p>
    <div style='margin-top: 1.5rem; padding: 1rem 2rem; 
                background: linear-gradient(135deg, #f7fafc 0%, #edf2f7 100%);
                border-radius: 12px; 
                border-left: 5px solid #667eea;
                display: inline-block;'>
        <p style='margin: 0; color: #2d3748; font-weight: 600; font-size: 1rem;'>
            ✨ v2.0 - Implied Volatility & Automatic Backtesting
        </p>
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown("<hr style='margin: 2rem 0; border: none; height: 2px; background: linear-gradient(90deg, transparent 0%, #e2e8f0 50%, transparent 100%);'>", unsafe_allow_html=True)

# Initialize session state
if 'calculated' not in st.session_state:
    st.session_state.calculated = False

# ============================================================================
# SIDEBAR - Advanced Metrics (Optional)
# ============================================================================

st.sidebar.header("⚙️ Metriche Aggiuntive")
st.sidebar.markdown("*Parametri opzionali per analisi avanzate*")

with st.sidebar.expander("📈 Beta e Correlazione", expanded=False):
    beta_portafoglio = st.number_input(
        "Beta del Portafoglio",
        min_value=0.0,
        max_value=2.0,
        value=1.0,
        step=0.05,
        help="Sensibilità del portafoglio all'indice. 1.0 = replica perfetta, <1 = meno volatile, >1 = più volatile"
    )

with st.sidebar.expander("💰 Costi di Transazione", expanded=False):
    bid_ask_spread = st.number_input(
        "Bid-Ask Spread (%)",
        min_value=0.0,
        max_value=5.0,
        value=0.0,
        step=0.1,
        help="Spread denaro-lettera sul Turbo"
    )
    
    commissioni = st.number_input(
        "Commissioni (%)",
        min_value=0.0,
        max_value=2.0,
        value=0.0,
        step=0.05,
        help="Commissioni di acquisto/vendita"
    )
    
    tasse = st.number_input(
        "Tasse su Capital Gains (%)",
        min_value=0.0,
        max_value=50.0,
        value=0.0,
        step=1.0,
        help="Tasse sui guadagni (es. 26% in Italia)"
    )

with st.sidebar.expander("📊 Dividend Yield", expanded=False):
    dividend_yield = st.number_input(
        "Dividend Yield Indice (%)",
        min_value=0.0,
        max_value=10.0,
        value=0.0,
        step=0.1,
        help="Rendimento da dividendi dell'indice (annualizzato)"
    )

with st.sidebar.expander("🎲 Volatilità e Greeks", expanded=True):
    st.markdown("**📊 Abilita Greeks per analisi avanzate**")
    st.info("💡 Le Greeks forniscono metriche di sensibilità del Turbo (Delta, Gamma, Vega, Theta, Rho)")
    
    enable_greeks = st.checkbox("Abilita Calcolo Greeks", value=False, key="enable_greeks")
    
    if enable_greeks:
        vol_method = st.radio(
            "Metodo Volatilità",
            options=["Automatica (da Prezzo Turbo)", "Manuale"],
            index=0,
            help="Automatica: calibra vol dal prezzo mercato | Manuale: inserisci tu"
        )
        
        if vol_method == "Automatica (da Prezzo Turbo)":
            st.info("💡 La volatilità verrà calibrata automaticamente dal prezzo di mercato del Turbo")
            volatility = 0.20  # Placeholder, will be updated
            use_implied_vol = True
        else:
            volatility = st.number_input(
                "Volatilità Implicita Annualizzata (%)",
                min_value=5.0,
                max_value=100.0,
                value=20.0,
                step=1.0,
                help="Volatilità implicita annualizzata dell'indice sottostante"
            ) / 100
            
            st.caption(f"📈 Volatilità impostata: {volatility*100:.1f}% annua")
            use_implied_vol = False
    else:
        volatility = 0.20
        use_implied_vol = False

with st.sidebar.expander("🎯 Monte Carlo Simulation", expanded=False):
    enable_monte_carlo = st.checkbox("Abilita Simulazione Monte Carlo", value=False)
    
    if enable_monte_carlo:
        n_simulations = st.select_slider(
            "Numero di Simulazioni",
            options=[1000, 5000, 10000, 25000, 50000],
            value=10000
        )
        
        mc_volatility = st.number_input(
            "Volatilità per Monte Carlo (%)",
            min_value=5.0,
            max_value=100.0,
            value=20.0,
            step=1.0,
            help="Volatilità per le simulazioni"
        ) / 100
    else:
        n_simulations = 10000
        mc_volatility = 0.20

st.sidebar.markdown("---")
st.sidebar.markdown("*Sviluppato per analisi professionale di hedging*")

# ============================================================================
# MAIN PAGE - Original Inputs
# ============================================================================

st.header("📝 Parametri di Input")

col1, col2, col3 = st.columns(3)

with col1:
    st.subheader("🎯 Turbo Short Certificate")
    prezzo_iniziale = st.number_input("Prezzo Iniziale (EUR)", min_value=0.01, max_value=1000.0, value=7.64, step=0.01)
    strike = st.number_input("Strike", min_value=1000.0, max_value=50000.0, value=7505.97, step=0.01)
    cambio = st.number_input("Tasso di Cambio (EUR/USD)", min_value=0.5, max_value=2.0, value=1.15, step=0.01)
    multiplo = st.number_input("Multiplo", min_value=0.001, max_value=1.0, value=0.01, step=0.001, format="%.3f")
    euribor = st.number_input("Euribor 12M", min_value=0.0, max_value=0.20, value=0.02456, step=0.0001, format="%.5f")

with col2:
    st.subheader("📈 Indice di Riferimento")
    valore_iniziale_indice = st.number_input("Valore Iniziale Indice", min_value=1000.0, max_value=50000.0, value=6670.75, step=0.01)
    valore_ipotetico_indice = st.number_input("Valore Ipotetico Indice", min_value=1000.0, max_value=50000.0, value=6000.0, step=0.01)
    
    variazione_pct = (valore_ipotetico_indice / valore_iniziale_indice - 1) * 100
    st.metric("Variazione Scenario", f"{variazione_pct:+.2f}%")
    
    giorni = st.number_input("Giorni a Scadenza", min_value=1, max_value=365, value=60, step=1)

with col3:
    st.subheader("💼 Portafoglio")
    valore_portafoglio = st.number_input("Valore Portafoglio (EUR)", min_value=1000.0, max_value=10000000.0, value=200000.0, step=1000.0)
    
    st.markdown("###")
    if st.button("🚀 Calcola Copertura", type="primary", use_container_width=True):
        st.session_state.calculated = True

# ============================================================================
# CALCULATIONS
# ============================================================================

if st.session_state.calculated:
    
    params = {
        'prezzo_iniziale': prezzo_iniziale,
        'strike': strike,
        'cambio': cambio,
        'multiplo': multiplo,
        'euribor': euribor,
        'valore_iniziale_indice': valore_iniziale_indice,
        'valore_ipotetico_indice': valore_ipotetico_indice,
        'giorni': giorni,
        'valore_portafoglio': valore_portafoglio,
        'beta': beta_portafoglio,
        'dividend_yield': dividend_yield / 100 if dividend_yield > 0 else 0.0,
        'bid_ask_spread': bid_ask_spread,
        'commissioni': commissioni,
        'tasse': tasse,
    }
    
    calculator = TurboCalculator(params)
    results = calculator.calculate_hedge_results()
    
    if enable_greeks and use_implied_vol:
        from utils.implied_vol import calculate_implied_volatility
        
        vol_result = calculate_implied_volatility(
            market_price=prezzo_iniziale,
            spot=valore_iniziale_indice,
            strike=strike,
            days=giorni,
            risk_free_rate=euribor,
            dividend_yield=dividend_yield / 100 if dividend_yield > 0 else 0.0,
            multiplo=multiplo,
            cambio=cambio,
            premio_known=results['premio']
        )
        
        if vol_result['success']:
            volatility = vol_result['vol_implicita']
            with st.sidebar:
                st.success(f"✅ Vol Implicita: **{volatility*100:.1f}%**")
                with st.expander("📊 Dettagli Vol Implicita"):
                    st.write(f"**Metodo:** Reverse Engineering")
                    st.write(f"**Prezzo Mercato:** €{prezzo_iniziale:.2f}")
                    st.write(f"**Fair Value:** €{vol_result['fair_value']:.4f}")
                    st.write(f"**Premio:** €{vol_result['target_premium']:.4f}")
                    st.write(f"**Vol Calibrata:** {volatility*100:.2f}%")
        else:
            st.sidebar.warning(f"⚠️ {vol_result['message']}")
            volatility = 0.20
    
    st.markdown("---")
    
    # ============================================================================
    # RESULTS SECTION
    # ============================================================================
    
    st.header("📊 Risultati della Copertura")
    excel_col1, excel_col2, excel_col3 = st.columns([1, 1, 1.3])
    
    with excel_col1:
        st.markdown("<div style='background-color: #2c5282; padding: 12px; border-radius: 5px; text-align: center; margin-bottom: 15px;'><h4 style='margin: 0; color: white;'>CARATTERISTICHE TURBO SHORT</h4></div>", unsafe_allow_html=True)
        st.markdown(f"""
        <table style='width: 100%; border-collapse: collapse;'>
        <tr style='background-color: #F8F9FA;'><td style='padding: 8px; border: 1px solid #dee2e6;'><strong>Prezzo iniziale</strong></td><td style='padding: 8px; border: 1px solid #dee2e6; text-align: right;'>{prezzo_iniziale:.2f} €</td></tr>
        <tr><td style='padding: 8px; border: 1px solid #dee2e6;'><strong>Fair Value</strong></td><td style='padding: 8px; border: 1px solid #dee2e6; text-align: right; color: #2c5282; font-weight: bold;'>{results["fair_value"]:.4f} €</td></tr>
        <tr style='background-color: #F8F9FA;'><td style='padding: 8px; border: 1px solid #dee2e6;'><strong>Premio</strong></td><td style='padding: 8px; border: 1px solid #dee2e6; text-align: right;'>{results["premio"]:.4f} €</td></tr>
        <tr><td style='padding: 8px; border: 1px solid #dee2e6;'><strong>Strike</strong></td><td style='padding: 8px; border: 1px solid #dee2e6; text-align: right;'>{strike:.2f}</td></tr>
        <tr style='background-color: #F8F9FA;'><td style='padding: 8px; border: 1px solid #dee2e6;'><strong>Tasso di cambio</strong></td><td style='padding: 8px; border: 1px solid #dee2e6; text-align: right;'>{cambio:.2f}</td></tr>
        <tr><td style='padding: 8px; border: 1px solid #dee2e6;'><strong>Multiplo</strong></td><td style='padding: 8px; border: 1px solid #dee2e6; text-align: right;'>{multiplo:.2f}</td></tr>
        <tr style='height: 20px;'><td colspan='2'></td></tr>
        <tr style='background-color: #F8F9FA;'><td style='padding: 8px; border: 1px solid #dee2e6;'><strong>Euribor 12M</strong></td><td style='padding: 8px; border: 1px solid #dee2e6; text-align: right;'>{euribor:.5f}</td></tr>
        </table>
        """, unsafe_allow_html=True)
    
    with excel_col2:
        st.markdown("<div style='background-color: #2c5282; padding: 12px; border-radius: 5px; text-align: center; margin-bottom: 15px;'><h4 style='margin: 0; color: white;'>INDICE DA COPRIRE</h4></div>", unsafe_allow_html=True)
        st.markdown(f"""
        <table style='width: 100%; border-collapse: collapse;'>
        <tr style='background-color: #F8F9FA;'><td style='padding: 8px; border: 1px solid #dee2e6;'><strong>Valore Iniziale</strong></td><td style='padding: 8px; border: 1px solid #dee2e6; text-align: right;'>{valore_iniziale_indice:.2f}</td></tr>
        <tr><td style='padding: 8px; border: 1px solid #dee2e6;'><strong>Valore Ipotetico</strong></td><td style='padding: 8px; border: 1px solid #dee2e6; text-align: right; color: #c62828; font-weight: bold;'>{valore_ipotetico_indice:.0f}</td></tr>
        <tr style='background-color: #F8F9FA;'><td style='padding: 8px; border: 1px solid #dee2e6;'><strong>Giorni</strong></td><td style='padding: 8px; border: 1px solid #dee2e6; text-align: right;'>{giorni:.0f}</td></tr>
        <tr style='height: 20px;'><td colspan='2'></td></tr>
        <tr><td style='padding: 8px; border: 1px solid #dee2e6;'><strong>Prezzo Turbo Short</strong></td><td style='padding: 8px; border: 1px solid #dee2e6; text-align: right; color: #2c5282; font-weight: bold;'>{results["prezzo_turbo_futuro"]:.4f} €</td></tr>
        <tr style='background-color: #F8F9FA;'><td style='padding: 8px; border: 1px solid #dee2e6;'><strong>Barriera Turbo Short</strong></td><td style='padding: 8px; border: 1px solid #dee2e6; text-align: right;'>{results["barrier_future"]:.2f}</td></tr>
        <tr><td style='padding: 8px; border: 1px solid #dee2e6;'><strong>Leva Turbo Short</strong></td><td style='padding: 8px; border: 1px solid #dee2e6; text-align: right;'>{results["leverage"]:.2f}</td></tr>
        </table>
        """, unsafe_allow_html=True)
    
    with excel_col3:
        st.markdown("<div style='background-color: #2c5282; padding: 12px; border-radius: 5px; text-align: center; margin-bottom: 15px;'><h4 style='margin: 0; color: white;'>PORTAFOGLIO DA COPRIRE</h4></div>", unsafe_allow_html=True)
        st.markdown(f"<div style='text-align: right; font-size: 24px; font-weight: bold; color: #2c5282; margin-bottom: 20px; padding: 10px; background-color: #F8F9FA; border-radius: 5px;'>{valore_portafoglio:,.2f} €</div>", unsafe_allow_html=True)
        st.markdown(f"""
        <table style='width: 100%; border-collapse: collapse; margin-top: 10px;'>
        <tr style='background-color: #F8F9FA;'><td style='padding: 8px; border: 1px solid #dee2e6;'><strong>N. Turbo Short</strong></td><td style='padding: 8px; border: 1px solid #dee2e6; text-align: right;'>{results["n_turbo"]:.2f}</td><td rowspan='2' style='padding: 8px; border: 1px solid #dee2e6; text-align: center; vertical-align: middle; background-color: #E3F2FD; font-weight: bold;'>TOTALE CON<br/>COPERTURA</td></tr>
        <tr><td style='padding: 8px; border: 1px solid #dee2e6;'><strong>Capitale</strong></td><td style='padding: 8px; border: 1px solid #dee2e6; text-align: right;'>{results["capitale_turbo"]:,.2f} €</td></tr>
        <tr style='background-color: #FFF3E0;'><td colspan='2' style='padding: 8px; border: 1px solid #dee2e6; text-align: right; font-weight: bold;'></td><td style='padding: 8px; border: 1px solid #dee2e6; text-align: right; color: #E65100; font-weight: bold; font-size: 16px;'>{results["capitale_totale"]:,.2f} €</td></tr>
        </table>
        """, unsafe_allow_html=True)
        
        st.markdown("<div style='background-color: #E3F2FD; padding: 10px; border-radius: 5px; text-align: center; margin-top: 20px; margin-bottom: 10px;'><strong style='color: #0D47A1;'>VALORE PORTAFOGLIO SIMULATO</strong></div>", unsafe_allow_html=True)
        
        valore_ptf_futuro = results['valore_portafoglio_futuro']
        valore_turbo_futuro = results['valore_turbo_futuro']
        valore_totale = results['valore_totale_futuro']
        performance_totale = results['performance_totale'] * 100
        perf_bg = '#E8F5E9' if performance_totale >= 0 else '#FFEBEE'
        perf_color = '#2E7D32' if performance_totale >= 0 else '#C62828'
        perf_sign = '+' if performance_totale >= 0 else ''
        
        st.markdown(f"""
        <table style='width: 100%; border-collapse: collapse;'>
        <tr style='background-color: #F8F9FA;'><td style='padding: 8px; border: 1px solid #dee2e6;'></td><td style='padding: 8px; border: 1px solid #dee2e6; text-align: right; font-weight: bold;'>VALORE COPERTURA</td></tr>
        <tr><td style='padding: 8px; border: 1px solid #dee2e6;'><strong>Portafoglio</strong></td><td style='padding: 8px; border: 1px solid #dee2e6; text-align: right;'>{valore_ptf_futuro:,.2f} €</td></tr>
        <tr style='background-color: #F8F9FA;'><td style='padding: 8px; border: 1px solid #dee2e6;'><strong>Turbo (netto)</strong></td><td style='padding: 8px; border: 1px solid #dee2e6; text-align: right; color: #2E7D32; font-weight: bold;'>{valore_turbo_futuro:,.2f} €</td></tr>
        <tr style='height: 10px;'><td colspan='2'></td></tr>
        <tr style='background-color: #E3F2FD;'><td style='padding: 8px; border: 1px solid #dee2e6;'><strong>TOTALE</strong></td><td style='padding: 8px; border: 1px solid #dee2e6; text-align: right; font-weight: bold; font-size: 16px;'>{valore_totale:,.2f} €</td></tr>
        </table>
        """, unsafe_allow_html=True)
        
        st.markdown(f"""
        <div style='background-color: {perf_bg}; padding: 20px; border-radius: 5px; text-align: center; border: 3px solid {perf_color}; margin-top: 15px;'>
        <div style='font-size: 42px; font-weight: bold; color: {perf_color}; line-height: 1;'>{perf_sign}{performance_totale:.2f}%</div>
        <div style='color: #666; font-size: 12px; margin-top: 8px; font-weight: 600;'>PERFORMANCE COPERTA</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("###")
    
    kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns(4)
    with kpi_col1: st.metric("🎯 Hedge Ratio", f"{results['hedge_ratio'] * 100:.1f}%", "Efficacia copertura")
    with kpi_col2: st.metric("🛡️ Distanza Barriera", f"{results['distanza_barriera_pct']:+.2f}%", f"K.O. a {results['barrier_future']:,.0f}")
    with kpi_col3: st.metric("📉 Variazione Indice", f"{results['variazione_indice_pct']:.2f}%", f"Ptf: {results['variazione_portafoglio_pct']:.2f}% (β={beta_portafoglio})", delta_color="normal" if results['variazione_indice_pct'] >= 0 else "inverse")
    with kpi_col4: st.metric("💰 P&L Netto", f"€{results['pl_netto']:,.0f}", f"{performance_totale:+.2f}%", delta_color="normal" if results['pl_netto'] >= 0 else "inverse")
    
    # ============================================================================
    # CHARTS AND VISUALIZATIONS
    # ============================================================================
    st.markdown("---")
    st.header("📈 Analisi Grafiche")
    
    with st.expander("⏱️ Evoluzione Temporale", expanded=True):
        giorni_array, time_results = calculator.calculate_time_evolution(n_points=30)
        chart_col1, chart_col2 = st.columns([2, 1])
        with chart_col1: st.plotly_chart(create_time_evolution_chart(giorni_array, time_results, results['capitale_totale']), use_container_width=True)
        with chart_col2: st.plotly_chart(create_premium_decay_chart(giorni_array, time_results), use_container_width=True)
        st.plotly_chart(create_spot_barrier_chart(giorni_array, time_results), use_container_width=True)
    
    # GREEKS & MONTE CARLO (Optional)
    if enable_greeks:
        st.markdown("---")
        st.header("🎲 Analisi Greeks - Metriche di Sensibilità")
        greeks_params = { 'spot': valore_iniziale_indice, 'strike': strike, 'barrier': results['barrier_future'], 'time_to_maturity': giorni / 365.0, 'volatility': volatility, 'risk_free_rate': euribor, 'dividend_yield': dividend_yield / 100 if dividend_yield > 0 else 0.0, 'multiplo': multiplo, 'cambio': cambio }
        greeks = GreeksCalculator(greeks_params).calculate_all_greeks()
        greek_col1, greek_col2, greek_col3 = st.columns(3)
        with greek_col1: st.metric("Delta", f"{greeks['delta']:.4f}"); st.metric("Gamma", f"{greeks['gamma']:.6f}")
        with greek_col2: st.metric("Vega", f"{greeks['vega']:.4f}"); st.metric("Theta", f"{greeks['theta']:.4f} €/g")
        with greek_col3: st.metric("Rho", f"{greeks['rho']:.4f}"); st.metric("Prob. K.O.", f"{greeks['knockout_prob']*100:.2f}%")
        st.plotly_chart(create_greeks_chart(greeks), use_container_width=True)

    if enable_monte_carlo:
        st.markdown("---")
        st.header("🎲 Simulazione Monte Carlo")
        with st.spinner(f"Esecuzione di {n_simulations:,} simulazioni..."):
            mc_simulator = MonteCarloSimulator(calculator, mc_volatility, n_simulations)
            mc_results = mc_simulator.calculate_outcomes()
        mc_col1, mc_col2, mc_col3, mc_col4 = st.columns(4)
        with mc_col1: st.metric("Perf. Media", f"{mc_results['mean_performance']:.2f}%")
        with mc_col2: st.metric("VaR 95%", f"{mc_results['var_95']:.2f}%")
        with mc_col3: st.metric("CVaR 95%", f"{mc_results['cvar_95']:.2f}%")
        with mc_col4: st.metric("Tasso K.O.", f"{mc_results['knockout_rate']:.2f}%")
        st.plotly_chart(create_monte_carlo_histogram(mc_results['performance'], mc_results['mean_performance'], mc_results['percentile_5'], mc_results['percentile_95']), use_container_width=True)

else:
    st.info("👆 Inserisci i parametri e premi 'Calcola Copertura' per iniziare l'analisi.")

# ============================================================================
# AUTOMATIC BACKTESTING (NOW FIXED & BRUTALLY HONEST)
# ============================================================================

st.markdown("---")
st.header("🔍 Backtesting Automatico")

# THE REALITY CHECK WARNING
st.warning("""
⚠️ **ATTENZIONE:** Il backtest utilizza storici basati su prezzi di chiusura (Daily/Weekly). **Questo sottostima drasticamente il rischio reale di Knock-Out.** Se l'indice tocca la barriera durante il giorno ma chiude sotto la barriera, questo modello non lo rileva e segna il giorno come "sicuro". 
**Non usare questi risultati** per allocare capitale reale senza aver verificato la dinamica tick-by-tick o i massimi intraday reali.
""")

st.markdown("""
<div class="info-box">
<strong>Testa la strategia su dati storici reali</strong><br>
Simula come la copertura avrebbe performato negli ultimi anni. Il programma scarica automaticamente i dati da Yahoo Finance.
</div>
""", unsafe_allow_html=True)

with st.expander("📊 Configura e Esegui Backtest", expanded=False):
    
    st.subheader("1️⃣ Selezione Asset")
    bt_col1, bt_col2 = st.columns(2)
    with bt_col1:
        portfolio_preset = st.selectbox("Preset Comuni Portafoglio", options=["SPY - S&P 500 ETF", "QQQ - Nasdaq 100 ETF", "FTSEMIB.MI - FTSE MIB", "Custom (inserisci ticker)"])
        portfolio_ticker = st.text_input("Ticker Custom Portafoglio", value="SPY").upper() if "Custom" in portfolio_preset else portfolio_preset.split(" - ")[0]
        st.caption(f"📊 Ticker: **{portfolio_ticker}**")
    
    with bt_col2:
        index_preset = st.selectbox("Preset Comuni Indice", options=["^GSPC - S&P 500", "^NDX - Nasdaq 100", "^GDAXI - DAX", "Custom (inserisci ticker)"])
        index_ticker = st.text_input("Ticker Custom Indice", value="^GSPC").upper() if "Custom" in index_preset else index_preset.split(" - ")[0]
        st.caption(f"📈 Ticker: **{index_ticker}**")
    
    st.markdown("---")
    st.subheader("2️⃣ Periodo Temporale")
    period_col1, period_col2 = st.columns(2)
    with period_col1:
        period_preset = st.selectbox("Periodo", options=["3 anni (raccomandato)", "5 anni", "2 anni", "1 anno"])
        years = int(period_preset.split()[0])
        end_date = pd.Timestamp.now()
        start_date_ui = end_date - pd.DateOffset(years=years)
    
    with period_col2:
        frequency = st.selectbox("Frequenza Dati", options=["Daily (raccomandato)", "Weekly"])
        yf_interval = "1d" if "Daily" in frequency else "1wk"
    
    st.info(f"📅 Analisi effettiva: **{start_date_ui.strftime('%Y-%m-%d')}** → **{end_date.strftime('%Y-%m-%d')}**")
    
    st.markdown("---")
    st.subheader("3️⃣ Parametri Strategia Hedge")
    strat_col1, strat_col2, strat_col3 = st.columns(3)
    with strat_col1: hedge_trigger_dd = st.slider("Attiva Hedge a Drawdown", -20.0, -1.0, -5.0, 0.5)
    with strat_col2: strike_offset_pct = st.slider("Strike Offset %", 5, 20, 10, 1)
    with strat_col3: turbo_maturity_days = st.slider("Scadenza Turbo (giorni)", 30, 365, 90, 30)
    
    with st.expander("⚙️ Parametri Avanzati"):
        adv_col1, adv_col2 = st.columns(2)
        with adv_col1: rebalance_freq = st.number_input("Ribilanciamento ogni N giorni", 1, 90, 30)
        with adv_col2: hedge_size_pct = st.slider("Dimensione Hedge (%)", 5, 30, 10, 1)

    st.markdown("---")
    if st.button("🚀 Esegui Backtest Automatico", type="primary", use_container_width=True):
        st.markdown("### 📥 Elaborazione e Data Cleaning")
        
        try:
            from utils.backtest import download_historical_data, run_full_backtest
            
            # THE FIX: Fetch extra days to calculate rolling beta properly without NaNs padding
            start_date_fetch = start_date_ui - pd.DateOffset(days=90) # Buffer to calculate the 60-day rolling beta
            
            with st.spinner(f"Download {portfolio_ticker} e {index_ticker} (con pre-buffer per Beta)..."):
                df_backtest_raw = download_historical_data(
                    portfolio_ticker=portfolio_ticker,
                    index_ticker=index_ticker,
                    start_date=start_date_fetch.strftime('%Y-%m-%d'),
                    end_date=end_date.strftime('%Y-%m-%d'),
                    interval=yf_interval
                )
            
            if len(df_backtest_raw) == 0:
                st.error("❌ Nessun dato trovato. Verifica i ticker.")
                st.stop()
            
            # Beta calculation on the extended dataset
            if len(df_backtest_raw) > 60:
                df_backtest_raw['Ret_Portfolio'] = df_backtest_raw['Portfolio_Value'].pct_change()
                df_backtest_raw['Ret_Index'] = df_backtest_raw['Index_Close'].pct_change()
                cov = df_backtest_raw['Ret_Portfolio'].rolling(60).cov(df_backtest_raw['Ret_Index'])
                var = df_backtest_raw['Ret_Index'].rolling(60).var()
                df_backtest_raw['Beta_Rolling'] = cov / var
            else:
                df_backtest_raw['Beta_Rolling'] = beta_portafoglio
            
            # THE FIX: Slice the dataframe to match the UI start date exactly. No dirty 'fillna' step.
            df_backtest = df_backtest_raw[df_backtest_raw['Date'] >= start_date_ui.strftime('%Y-%m-%d')].copy()
            df_backtest['Beta_Rolling'] = df_backtest['Beta_Rolling'].fillna(beta_portafoglio) # Only a fallback for extremely short datasets
            
            # Scale to portfolio value
            scale_factor = valore_portafoglio / df_backtest['Portfolio_Value'].iloc[0]
            df_backtest['Portfolio_Value'] = df_backtest['Portfolio_Value'] * scale_factor
            
            st.success(f"✅ Pre-processamento completato. Avvio simulazione pulita dal {start_date_ui.strftime('%Y-%m-%d')}.")
            
            st.markdown("### 🎯 Esecuzione Backtest")
            
            # THE FIX: hardcoded decay_exponent to 1.5 as per Methodology Document
            decay_exponent_fixed = 1.5
            
            backtest_params = {
                'strike_offset': strike_offset_pct / 100,
                'maturity_days': turbo_maturity_days,
                'hedge_trigger_dd': hedge_trigger_dd,
                'rebalance_freq': rebalance_freq,
                'hedge_size_pct': hedge_size_pct / 100,
                'prezzo_turbo_input': prezzo_iniziale if 'prezzo_iniziale' in locals() else 7.64,
                'multiplo': multiplo if 'multiplo' in locals() else 0.01,
                'cambio': cambio if 'cambio' in locals() else 1.15,
                'euribor': euribor if 'euribor' in locals() else 0.02456,
                'dividend_yield': dividend_yield / 100 if 'dividend_yield' in locals() and dividend_yield > 0 else 0.0,
                'bid_ask_spread': bid_ask_spread if 'bid_ask_spread' in locals() else 0.0,
                'commissioni': commissioni if 'commissioni' in locals() else 0.0,
                'tasse': tasse if 'tasse' in locals() else 0.0,
                'decay_exponent': decay_exponent_fixed, # FIXED 
                'beta': beta_portafoglio if 'beta_portafoglio' in locals() else 1.0,
            }
            
            with st.spinner("Simulazione in corso..."):
                results_bt = run_full_backtest(df_backtest, backtest_params)
            
            st.success("✅ Backtest completato matematicamente.")
            
            # [The rest of the visual charting code remains identical since it's just plotting results]
            st.markdown("---")
            st.markdown("## 📊 Risultati Backtest")
            metrics = results_bt['metrics']
            
            metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)
            with metric_col1: st.metric("Return Totale Hedged", f"{metrics['total_return_hedged']:.1f}%", delta=f"{metrics['total_return_hedged'] - metrics['total_return_unhedged']:+.1f}% vs Unhedged")
            with metric_col2: st.metric("Sharpe Ratio", f"{metrics['sharpe_hedged']:.2f}", delta=f"{metrics['sharpe_hedged'] - metrics['sharpe_unhedged']:+.2f}")
            with metric_col3: st.metric("Max Drawdown", f"{metrics['maxdd_hedged']:.1f}%", delta=f"{metrics['maxdd_hedged'] - metrics['maxdd_unhedged']:.1f}%", delta_color="inverse")
            with metric_col4: st.metric("Hedge Attivo", f"{metrics['hedge_active_pct']:.0f}%", "del periodo")

            df_results = results_bt['daily_results']
            import plotly.graph_objects as go
            
            fig_equity = go.Figure()
            fig_equity.add_trace(go.Scatter(x=df_results['Date'], y=df_results['Portfolio_Unhedged'], name='Senza Copertura', line=dict(color='#c62828', width=2)))
            fig_equity.add_trace(go.Scatter(x=df_results['Date'], y=df_results['Portfolio_Hedged'], name='Con Copertura Turbo', line=dict(color='#2c5282', width=3)))
            fig_equity.update_layout(title="Equity Curve: Hedged vs Unhedged", xaxis_title="Data", yaxis_title="Valore Portafoglio (€)", hovermode='x unified', height=500)
            st.plotly_chart(fig_equity, use_container_width=True)

        except urllib.error.URLError as e:
            st.error(f"❌ Errore di rete con Yahoo Finance. Riprova più tardi. Dettaglio: {str(e)}")
        except KeyError as e:
            st.error(f"❌ Errore di struttura dati: Manca una colonna attesa nel calcolo. Hai modificato utils/backtest.py? Dettaglio: {str(e)}")
        except Exception as e:
            st.error(f"❌ Errore logico critico nel motore di backtest. Smetti di ignorare i bug strutturali. Dettaglio: {str(e)}")
            import traceback
            st.code(traceback.format_exc())

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; font-size: 0.9em;'>
    <strong>Turbo Hedge Calculator</strong> | Versione 1.0<br>
    Tool professionale per analisi di copertura con Certificati Turbo Short<br>
    ⚠️ <em>Questo tool è fornito a scopo educativo. Non costituisce consulenza finanziaria.</em>
</div>
""", unsafe_allow_html=True)
