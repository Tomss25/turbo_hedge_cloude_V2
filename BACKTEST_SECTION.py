    st.markdown("---")
    st.header("🔍 Backtesting Automatico")
    
    st.markdown("""
    <div class="info-box">
    <strong>Testa la strategia su dati storici reali</strong><br>
    Simula come la copertura avrebbe performato negli ultimi anni.
    Il programma scarica automaticamente i dati da Yahoo Finance.
    </div>
    """, unsafe_allow_html=True)
    
    with st.expander("📊 Configura e Esegui Backtest", expanded=False):
        
        # ========================================
        # ASSET SELECTION
        # ========================================
        
        st.subheader("1️⃣ Selezione Asset")
        
        bt_col1, bt_col2 = st.columns(2)
        
        with bt_col1:
            st.markdown("**Portafoglio (Proxy)**")
            
            portfolio_preset = st.selectbox(
                "Preset Comuni",
                options=[
                    "Custom (inserisci ticker)",
                    "SPY - S&P 500 ETF",
                    "QQQ - Nasdaq 100 ETF",
                    "FTSEMIB.MI - FTSE MIB",
                    "EWG - Germania ETF",
                    "VTI - Total Market US",
                ],
                help="Seleziona preset o inserisci ticker personalizzato"
            )
            
            if portfolio_preset == "Custom (inserisci ticker)":
                portfolio_ticker = st.text_input(
                    "Ticker Portafoglio",
                    value="SPY",
                    help="Esempio: SPY, QQQ, AAPL"
                ).upper()
            else:
                portfolio_ticker = portfolio_preset.split(" - ")[0]
            
            st.caption(f"📊 Ticker: **{portfolio_ticker}**")
        
        with bt_col2:
            st.markdown("**Indice (Turbo Sottostante)**")
            
            index_preset = st.selectbox(
                "Preset Comuni",
                options=[
                    "Custom (inserisci ticker)",
                    "^GSPC - S&P 500",
                    "^NDX - Nasdaq 100",
                    "^GDAXI - DAX",
                    "FTSEMIB.MI - FTSE MIB",
                ],
                help="Indice su cui si basa il Turbo"
            )
            
            if index_preset == "Custom (inserisci ticker)":
                index_ticker = st.text_input(
                    "Ticker Indice",
                    value="^GSPC",
                    help="Esempio: ^GSPC, ^NDX, ^GDAXI"
                ).upper()
            else:
                index_ticker = index_preset.split(" - ")[0]
            
            st.caption(f"📈 Ticker: **{index_ticker}**")
        
        # ========================================
        # TIME PERIOD
        # ========================================
        
        st.markdown("---")
        st.subheader("2️⃣ Periodo Temporale")
        
        period_col1, period_col2 = st.columns(2)
        
        with period_col1:
            period_preset = st.selectbox(
                "Periodo",
                options=[
                    "3 anni (raccomandato)",
                    "5 anni",
                    "2 anni",
                    "1 anno",
                ],
                index=0
            )
            
            years = int(period_preset.split()[0])
            end_date = pd.Timestamp.now()
            start_date = end_date - pd.DateOffset(years=years)
        
        with period_col2:
            frequency = st.selectbox(
                "Frequenza Dati",
                options=["Daily (raccomandato)", "Weekly"],
                index=0,
                help="Daily = più preciso"
            )
            
            yf_interval = "1d" if "Daily" in frequency else "1wk"
        
        st.info(f"📅 Periodo: **{start_date.strftime('%Y-%m-%d')}** → **{end_date.strftime('%Y-%m-%d')}** ({(end_date-start_date).days} giorni)")
        
        # ========================================
        # STRATEGY PARAMETERS
        # ========================================
        
        st.markdown("---")
        st.subheader("3️⃣ Parametri Strategia Hedge")
        
        strat_col1, strat_col2, strat_col3 = st.columns(3)
        
        with strat_col1:
            hedge_trigger_dd = st.slider(
                "Attiva Hedge a Drawdown",
                min_value=-20.0,
                max_value=-1.0,
                value=-5.0,
                step=0.5,
                help="Apre copertura quando portafoglio scende X% dal picco"
            )
        
        with strat_col2:
            strike_offset_pct = st.slider(
                "Strike Offset %",
                min_value=5,
                max_value=20,
                value=10,
                step=1,
                help="Strike = Spot × (1 + offset%)"
            )
        
        with strat_col3:
            turbo_maturity_days = st.slider(
                "Scadenza Turbo (giorni)",
                min_value=30,
                max_value=365,
                value=90,
                step=30,
                help="Giorni a scadenza del certificato Turbo"
            )
        
        # Advanced parameters
        with st.expander("⚙️ Parametri Avanzati"):
            adv_col1, adv_col2 = st.columns(2)
            
            with adv_col1:
                rebalance_freq = st.number_input(
                    "Ribilanciamento ogni N giorni",
                    min_value=1,
                    max_value=90,
                    value=30,
                    help="Ogni quanti giorni chiude e riapre"
                )
            
            with adv_col2:
                hedge_size_pct = st.slider(
                    "Dimensione Hedge (%)",
                    min_value=5,
                    max_value=30,
                    value=10,
                    step=1,
                    help="% portafoglio allocata ai Turbo"
                )
        
        # ========================================
        # EXECUTION
        # ========================================
        
        st.markdown("---")
        
        if st.button("🚀 Esegui Backtest Automatico", type="primary", use_container_width=True):
            
            # Download data
            st.markdown("### 📥 Download Dati da Yahoo Finance")
            
            try:
                from utils.backtest import download_historical_data
                
                with st.spinner(f"Download {portfolio_ticker} e {index_ticker}..."):
                    df_backtest = download_historical_data(
                        portfolio_ticker=portfolio_ticker,
                        index_ticker=index_ticker,
                        start_date=start_date.strftime('%Y-%m-%d'),
                        end_date=end_date.strftime('%Y-%m-%d'),
                        interval=yf_interval
                    )
                
                if len(df_backtest) == 0:
                    st.error("❌ Nessun dato trovato. Verifica ticker.")
                    st.stop()
                
                st.success(f"✅ {len(df_backtest)} giorni di dati scaricati")
                
                # Scale to portfolio value
                scale_factor = valore_portafoglio / df_backtest['Portfolio_Value'].iloc[0]
                df_backtest['Portfolio_Value'] = df_backtest['Portfolio_Value'] * scale_factor
                
                # Calculate rolling beta if enough data
                if len(df_backtest) > 60:
                    df_backtest['Ret_Portfolio'] = df_backtest['Portfolio_Value'].pct_change()
                    df_backtest['Ret_Index'] = df_backtest['Index_Close'].pct_change()
                    
                    cov = df_backtest['Ret_Portfolio'].rolling(60).cov(df_backtest['Ret_Index'])
                    var = df_backtest['Ret_Index'].rolling(60).var()
                    df_backtest['Beta_Rolling'] = cov / var
                    df_backtest['Beta_Rolling'].fillna(beta_portafoglio, inplace=True)
                else:
                    df_backtest['Beta_Rolling'] = beta_portafoglio
                
                # Preview
                with st.expander("👁️ Preview Dataset"):
                    st.dataframe(df_backtest.head(10), use_container_width=True)
                
                # Run backtest
                st.markdown("### 🎯 Esecuzione Backtest")
                
                backtest_params = {
                    'strike_offset': strike_offset_pct / 100,
                    'maturity_days': turbo_maturity_days,
                    'hedge_trigger_dd': hedge_trigger_dd,
                    'rebalance_freq': rebalance_freq,
                    'hedge_size_pct': hedge_size_pct / 100,
                    'prezzo_turbo_input': prezzo_iniziale,
                    'multiplo': multiplo,
                    'cambio': cambio,
                    'euribor': euribor,
                    'dividend_yield': dividend_yield / 100 if dividend_yield > 0 else 0.0,
                    'bid_ask_spread': bid_ask_spread,
                    'commissioni': commissioni,
                    'tasse': tasse,
                    'decay_exponent': decay_exponent,
                    'beta': beta_portafoglio,
                }
                
                from utils.backtest import run_full_backtest
                
                with st.spinner("Simulazione in corso..."):
                    results_bt = run_full_backtest(df_backtest, backtest_params)
                
                st.success("✅ Backtest completato!")
                
                # ========================================
                # RESULTS - METRICS
                # ========================================
                
                st.markdown("---")
                st.markdown("## 📊 Risultati Backtest")
                
                metrics = results_bt['metrics']
                
                # Main metrics
                metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)
                
                with metric_col1:
                    st.metric(
                        "Return Totale Hedged",
                        f"{metrics['total_return_hedged']:.1f}%",
                        delta=f"{metrics['total_return_hedged'] - metrics['total_return_unhedged']:+.1f}% vs Unhedged"
                    )
                
                with metric_col2:
                    st.metric(
                        "Sharpe Ratio",
                        f"{metrics['sharpe_hedged']:.2f}",
                        delta=f"{metrics['sharpe_hedged'] - metrics['sharpe_unhedged']:+.2f}"
                    )
                
                with metric_col3:
                    st.metric(
                        "Max Drawdown",
                        f"{metrics['maxdd_hedged']:.1f}%",
                        delta=f"{metrics['maxdd_hedged'] - metrics['maxdd_unhedged']:.1f}%",
                        delta_color="inverse"
                    )
                
                with metric_col4:
                    st.metric(
                        "Hedge Attivo",
                        f"{metrics['hedge_active_pct']:.0f}%",
                        "del periodo"
                    )
                
                # Additional metrics table
                with st.expander("📊 Metriche Dettagliate"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("**Senza Copertura:**")
                        metrics_unhedged = {
                            'Total Return': f"{metrics['total_return_unhedged']:.2f}%",
                            'Ann. Return': f"{metrics['ann_return_unhedged']:.2f}%",
                            'Volatilità': f"{metrics['vol_unhedged']:.2f}%",
                            'Sharpe': f"{metrics['sharpe_unhedged']:.2f}",
                            'Sortino': f"{metrics['sortino_unhedged']:.2f}",
                            'Max DD': f"{metrics['maxdd_unhedged']:.2f}%",
                            'Calmar': f"{metrics['calmar_unhedged']:.2f}",
                            'Win Rate': f"{metrics['win_rate_unhedged']:.1f}%",
                        }
                        st.dataframe(pd.DataFrame(list(metrics_unhedged.items()), columns=['Metrica', 'Valore']), hide_index=True)
                    
                    with col2:
                        st.markdown("**Con Copertura:**")
                        metrics_hedged = {
                            'Total Return': f"{metrics['total_return_hedged']:.2f}%",
                            'Ann. Return': f"{metrics['ann_return_hedged']:.2f}%",
                            'Volatilità': f"{metrics['vol_hedged']:.2f}%",
                            'Sharpe': f"{metrics['sharpe_hedged']:.2f}",
                            'Sortino': f"{metrics['sortino_hedged']:.2f}",
                            'Max DD': f"{metrics['maxdd_hedged']:.2f}%",
                            'Calmar': f"{metrics['calmar_hedged']:.2f}",
                            'Win Rate': f"{metrics['win_rate_hedged']:.1f}%",
                        }
                        st.dataframe(pd.DataFrame(list(metrics_hedged.items()), columns=['Metrica', 'Valore']), hide_index=True)
                
                # ========================================
                # CHARTS
                # ========================================
                
                st.markdown("---")
                st.subheader("📈 Grafici Performance")
                
                df_results = results_bt['daily_results']
                
                # Equity curve
                import plotly.graph_objects as go
                
                fig_equity = go.Figure()
                
                fig_equity.add_trace(go.Scatter(
                    x=df_results['Date'],
                    y=df_results['Portfolio_Unhedged'],
                    name='Senza Copertura',
                    line=dict(color='#c62828', width=2)
                ))
                
                fig_equity.add_trace(go.Scatter(
                    x=df_results['Date'],
                    y=df_results['Portfolio_Hedged'],
                    name='Con Copertura Turbo',
                    line=dict(color='#2c5282', width=3)
                ))
                
                # Highlight hedge periods
                hedge_periods = df_results[df_results['Hedge_Active']]
                if len(hedge_periods) > 0:
                    fig_equity.add_trace(go.Scatter(
                        x=hedge_periods['Date'],
                        y=hedge_periods['Portfolio_Hedged'],
                        mode='markers',
                        name='Hedge Attivo',
                        marker=dict(color='#4caf50', size=3)
                    ))
                
                fig_equity.update_layout(
                    title="Equity Curve: Hedged vs Unhedged",
                    xaxis_title="Data",
                    yaxis_title="Valore Portafoglio (€)",
                    hovermode='x unified',
                    height=500
                )
                
                st.plotly_chart(fig_equity, use_container_width=True)
                
                # Drawdown comparison
                unhedged_peak = df_results['Portfolio_Unhedged'].expanding().max()
                unhedged_dd = (df_results['Portfolio_Unhedged'] - unhedged_peak) / unhedged_peak * 100
                
                hedged_peak = df_results['Portfolio_Hedged'].expanding().max()
                hedged_dd = (df_results['Portfolio_Hedged'] - hedged_peak) / hedged_peak * 100
                
                fig_dd = go.Figure()
                
                fig_dd.add_trace(go.Scatter(
                    x=df_results['Date'],
                    y=unhedged_dd,
                    name='DD Senza Copertura',
                    fill='tozeroy',
                    line=dict(color='#c62828'),
                    fillcolor='rgba(198,40,40,0.3)'
                ))
                
                fig_dd.add_trace(go.Scatter(
                    x=df_results['Date'],
                    y=hedged_dd,
                    name='DD Con Copertura',
                    fill='tozeroy',
                    line=dict(color='#2c5282', width=2),
                    fillcolor='rgba(44,82,130,0.3)'
                ))
                
                fig_dd.update_layout(
                    title="Drawdown Comparison",
                    xaxis_title="Data",
                    yaxis_title="Drawdown (%)",
                    hovermode='x unified',
                    height=400
                )
                
                st.plotly_chart(fig_dd, use_container_width=True)
                
                # ========================================
                # OPERATIONS TABLE
                # ========================================
                
                if len(results_bt['operations']) > 0:
                    st.markdown("---")
                    st.subheader("📋 Operazioni Eseguite")
                    
                    st.dataframe(
                        results_bt['operations'],
                        use_container_width=True,
                        hide_index=True
                    )
                    
                    st.info(f"**Totale Trade:** {results_bt['total_trades']}")
                
                # ========================================
                # EXPORT
                # ========================================
                
                st.markdown("---")
                st.subheader("📥 Export Risultati")
                
                csv_data = df_results.to_csv(index=False)
                st.download_button(
                    label="📥 Scarica Risultati Giornalieri (CSV)",
                    data=csv_data,
                    file_name=f"backtest_{portfolio_ticker}_{index_ticker}.csv",
                    mime="text/csv"
                )
                
            except Exception as e:
                st.error(f"❌ Errore durante backtest: {str(e)}")
                import traceback
                st.code(traceback.format_exc())

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; font-size: 0.9em;'>
    <strong>Turbo Hedge Calculator</strong> | Versione 1.0<br>
    Tool professionale per analisi di copertura con Certificati Turbo Short<br>
