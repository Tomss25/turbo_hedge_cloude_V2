# ============================================================================
# MODERN UI SNIPPETS per app.py
# ============================================================================
# 
# Sostituisci le sezioni corrispondenti in app.py con questi snippet
# per ottenere il layout moderno v2.0
#
# ============================================================================

# ----------------------------------------------------------------------------
# SNIPPET 1: Metriche Principali (Modern Gradient Cards)
# Sostituisci righe ~383-450 circa (sezione RESULTS SECTION)
# ----------------------------------------------------------------------------

st.markdown("---")
st.markdown("""
<div style='text-align: center; margin-bottom: 2rem;'>
    <h2 style='font-size: 2.5rem; 
               background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
               -webkit-background-clip: text; 
               -webkit-text-fill-color: transparent;
               margin: 0;'>
        📊 Risultati della Copertura
    </h2>
</div>
""", unsafe_allow_html=True)

# Metriche principali con gradient cards
metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)

with metric_col1:
    st.markdown(f"""
    <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                padding: 2rem 1.5rem; 
                border-radius: 16px; 
                color: white; 
                text-align: center;
                box-shadow: 0 8px 24px rgba(102, 126, 234, 0.25);
                transition: all 0.3s ease;'>
        <p style='margin: 0; font-size: 0.75rem; opacity: 0.95; 
                  text-transform: uppercase; letter-spacing: 0.1em; font-weight: 600;'>
            N° CERTIFICATI
        </p>
        <p style='margin: 0.75rem 0 0 0; font-size: 2.5rem; font-weight: 800; letter-spacing: -0.02em;'>
            {int(results['n_turbo']):,}
        </p>
        <p style='margin: 0.5rem 0 0 0; font-size: 0.875rem; opacity: 0.9;'>
            Posizione ottimale
        </p>
    </div>
    """, unsafe_allow_html=True)

with metric_col2:
    st.markdown(f"""
    <div style='background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
                padding: 2rem 1.5rem; 
                border-radius: 16px; 
                color: white; 
                text-align: center;
                box-shadow: 0 8px 24px rgba(240, 147, 251, 0.25);'>
        <p style='margin: 0; font-size: 0.75rem; opacity: 0.95; 
                  text-transform: uppercase; letter-spacing: 0.1em; font-weight: 600;'>
            CAPITALE TURBO
        </p>
        <p style='margin: 0.75rem 0 0 0; font-size: 2.5rem; font-weight: 800;'>
            €{results['capitale_turbo']:,.0f}
        </p>
        <p style='margin: 0.5rem 0 0 0; font-size: 0.875rem; opacity: 0.9;'>
            {results['capitale_turbo']/results['valore_portafoglio']*100:.1f}% del portafoglio
        </p>
    </div>
    """, unsafe_allow_html=True)

with metric_col3:
    st.markdown(f"""
    <div style='background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
                padding: 2rem 1.5rem; 
                border-radius: 16px; 
                color: white; 
                text-align: center;
                box-shadow: 0 8px 24px rgba(79, 172, 254, 0.25);'>
        <p style='margin: 0; font-size: 0.75rem; opacity: 0.95; 
                  text-transform: uppercase; letter-spacing: 0.1em; font-weight: 600;'>
            HEDGE RATIO
        </p>
        <p style='margin: 0.75rem 0 0 0; font-size: 2.5rem; font-weight: 800;'>
            {results['hedge_ratio']:.1f}%
        </p>
        <p style='margin: 0.5rem 0 0 0; font-size: 0.875rem; opacity: 0.9;'>
            Efficacia copertura
        </p>
    </div>
    """, unsafe_allow_html=True)

with metric_col4:
    st.markdown(f"""
    <div style='background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
                padding: 2rem 1.5rem; 
                border-radius: 16px; 
                color: white; 
                text-align: center;
                box-shadow: 0 8px 24px rgba(67, 233, 123, 0.25);'>
        <p style='margin: 0; font-size: 0.75rem; opacity: 0.95; 
                  text-transform: uppercase; letter-spacing: 0.1em; font-weight: 600;'>
            LEVA FINANZIARIA
        </p>
        <p style='margin: 0.75rem 0 0 0; font-size: 2.5rem; font-weight: 800;'>
            {results['leva']:.2f}x
        </p>
        <p style='margin: 0.5rem 0 0 0; font-size: 0.875rem; opacity: 0.9;'>
            Esposizione amplificata
        </p>
    </div>
    """, unsafe_allow_html=True)


# ----------------------------------------------------------------------------
# SNIPPET 2: Section Headers (Modern Gradient Style)
# Usa questo per tutti gli st.header() nell'app
# ----------------------------------------------------------------------------

def modern_header(emoji, title):
    """Helper function for modern section headers"""
    st.markdown(f"""
    <div style='margin: 3rem 0 1.5rem 0;'>
        <h2 style='font-size: 2rem; 
                   color: #2d3748;
                   margin: 0; 
                   padding-bottom: 0.75rem;
                   border-bottom: 3px solid #667eea;
                   display: inline-block;'>
            {emoji} {title}
        </h2>
    </div>
    """, unsafe_allow_html=True)

# Esempio uso:
# modern_header("📊", "Analisi Performance")


# ----------------------------------------------------------------------------
# SNIPPET 3: Info Boxes (Modern Style)
# Sostituisci st.info(), st.success(), st.warning(), st.error()
# ----------------------------------------------------------------------------

def modern_info_box(message, box_type="info"):
    """
    Modern info box with gradient
    box_type: 'info', 'success', 'warning', 'error'
    """
    
    colors = {
        'info': {
            'gradient': 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
            'icon': 'ℹ️'
        },
        'success': {
            'gradient': 'linear-gradient(135deg, #48bb78 0%, #38a169 100%)',
            'icon': '✅'
        },
        'warning': {
            'gradient': 'linear-gradient(135deg, #ed8936 0%, #dd6b20 100%)',
            'icon': '⚠️'
        },
        'error': {
            'gradient': 'linear-gradient(135deg, #f56565 0%, #e53e3e 100%)',
            'icon': '❌'
        }
    }
    
    config = colors.get(box_type, colors['info'])
    
    st.markdown(f"""
    <div style='background: {config['gradient']};
                padding: 1.5rem;
                border-radius: 12px;
                color: white;
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
                margin: 1rem 0;'>
        <p style='margin: 0; font-weight: 600; font-size: 1.05rem;'>
            {config['icon']} {message}
        </p>
    </div>
    """, unsafe_allow_html=True)

# Esempio uso:
# modern_info_box("Calcolo completato con successo!", "success")


# ----------------------------------------------------------------------------
# SNIPPET 4: Buttons (Modern Gradient Style)
# I button già hanno lo stile dal CSS, ma puoi forzare con HTML
# ----------------------------------------------------------------------------

def modern_button_html(label, button_id="btn"):
    """Generate modern gradient button HTML"""
    return f"""
    <button style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                   color: white;
                   border: none;
                   border-radius: 12px;
                   padding: 1rem 3rem;
                   font-weight: 700;
                   font-size: 1.1rem;
                   cursor: pointer;
                   box-shadow: 0 6px 20px rgba(102, 126, 234, 0.3);
                   transition: all 0.3s ease;
                   text-transform: uppercase;
                   letter-spacing: 0.05em;'
            onmouseover='this.style.transform="translateY(-3px)"; this.style.boxShadow="0 10px 30px rgba(102, 126, 234, 0.45)";'
            onmouseout='this.style.transform="translateY(0)"; this.style.boxShadow="0 6px 20px rgba(102, 126, 234, 0.3)";'
            id='{button_id}'>
        {label}
    </button>
    """


# ----------------------------------------------------------------------------
# SNIPPET 5: Data Display Cards (Alternative to columns)
# ----------------------------------------------------------------------------

def data_card(title, value, subtitle="", gradient="linear-gradient(135deg, #667eea 0%, #764ba2 100%)"):
    """Display data in modern card format"""
    st.markdown(f"""
    <div style='background: {gradient};
                padding: 1.75rem;
                border-radius: 12px;
                color: white;
                box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
                margin: 0.5rem 0;'>
        <p style='margin: 0; font-size: 0.875rem; opacity: 0.9; text-transform: uppercase; letter-spacing: 0.05em;'>
            {title}
        </p>
        <p style='margin: 0.5rem 0 0 0; font-size: 2rem; font-weight: 700;'>
            {value}
        </p>
        {f"<p style='margin: 0.25rem 0 0 0; font-size: 0.875rem; opacity: 0.85;'>{subtitle}</p>" if subtitle else ""}
    </div>
    """, unsafe_allow_html=True)

# Esempio uso:
# data_card("Fair Value", f"€{results['fair_value']:.4f}", "Valore intrinseco")


# ----------------------------------------------------------------------------
# SNIPPET 6: Progress/Status Indicators
# ----------------------------------------------------------------------------

def status_indicator(percentage, label="Completamento"):
    """Visual progress indicator"""
    color = "#48bb78" if percentage >= 70 else "#ed8936" if percentage >= 40 else "#f56565"
    
    st.markdown(f"""
    <div style='margin: 1rem 0;'>
        <div style='display: flex; justify-content: space-between; margin-bottom: 0.5rem;'>
            <span style='font-weight: 600; color: #2d3748;'>{label}</span>
            <span style='font-weight: 700; color: {color};'>{percentage:.1f}%</span>
        </div>
        <div style='background: #e2e8f0; height: 12px; border-radius: 10px; overflow: hidden;'>
            <div style='background: linear-gradient(90deg, {color} 0%, {color} 100%);
                        width: {percentage}%;
                        height: 100%;
                        transition: width 0.5s ease;'></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# Esempio uso:
# status_indicator(results['hedge_ratio'], "Hedge Ratio")


# ============================================================================
# FINE SNIPPETS
# ============================================================================
