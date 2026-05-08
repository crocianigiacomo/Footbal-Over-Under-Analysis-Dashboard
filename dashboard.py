import streamlit as st
import pandas as pd
import numpy as np
from scipy.stats import poisson
from scipy.optimize import minimize_scalar
from datetime import datetime
import query

# ──────────────────────────────────────────────
#  1. CONFIGURAZIONE PAGINA E TEMA CSS
# ──────────────────────────────────────────────
st.set_page_config(
    page_title="XG Football Analytics",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
   /* ── PULIZIA TOTALE ── */
    
    /* Nasconde l'header e la decorazione superiore */
    header[data-testid="stHeader"], [data-testid="stDecoration"] {
        display: none !important;
    }

    /* Nasconde il footer standard */
    footer {
        display: none !important;
    }
            
    /* ── RESET E SCROLL SMOOTH ── */
    html { scroll-behavior: smooth; }
    
    [data-testid="stVerticalBlock"] > div { gap: 1rem !important; }

    /* Spazio extra sopra e sotto per non coprire i contenuti con la barra nav o il bordo */
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 160px !important; 
    }

    /* ── TITOLI PRINCIPALI ── */
    .main-title {
        font-size: 2.5rem; font-weight: 800; color: #ffffff; letter-spacing: -0.5px;
        margin-top: 1rem; margin-bottom: 0.2rem; text-align: center;
        font-family: 'Inter', sans-serif;
    }
    .sub-title {
        font-size: 1.1rem; color: #b3b3b3; margin-bottom: 2.5rem;
        font-weight: 500; text-align: center;
        font-family: 'Inter', sans-serif;
            text-transform: uppercase;
    }

    /* ── SECTION TITLES (Con offset per lo scroll) ── */
    .section-title, .section-title-red, .section-title-blue {
        font-size: 1.1rem; font-weight: 700; color: #ffffff;
        background: #181818; padding: 0.8rem 1rem; border-radius: 8px; 
        margin-bottom: 1.2rem; box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        text-transform: uppercase;
        font-family: 'Inter', sans-serif;
        scroll-margin-top: 30px;
    }
    .section-title { border-left: 4px solid #1DB954; }
    .section-title-red { border-left: 4px solid #ED4245; }
    .section-title-blue { border-left: 4px solid #5865F2; }

    /* ── STICKY BOTTOM NAV BAR ── */
    .bottom-nav {
        position: fixed;
        bottom: 50px; 
        left: 50%;
        transform: translateX(-50%); 
        width: 90%; 
        max-width: 450px;
        height: 65px;
        background: rgba(18, 18, 18, 0.95);
        backdrop-filter: blur(10px); 
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 40px; 
        display: flex;
        justify-content: space-around;
        align-items: center;
        z-index: 9999;
        padding: 0 15px;
        box-shadow: 0 8px 32px rgba(0,0,0,0.5)
    }
    .nav-item {
        display: flex; flex-direction: column; align-items: center; justify-content: center;
        text-decoration: none !important; 
        border-bottom: none !important;   
        color: #8e9297 !important; 
        flex: 1; transition: all 0.2s ease-in-out;
        height: 100%;
    }
    /* Effetto al tocco (Mobile) o al passaggio del mouse (Desktop) */
    .nav-item:hover, .nav-item:active, .nav-item:focus { 
        color: #5865F2 !important; 
        transform: translateY(-2px); 
    }
    .nav-item:hover .nav-icon, .nav-item:active .nav-icon, .nav-item:focus .nav-icon {
        filter: drop-shadow(0 0 6px rgba(88,101,242,0.6));
    }
    
    .nav-icon { font-size: 20px; margin-bottom: 2px; transition: 0.2s; }
    .nav-label { font-size: 10px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px; }

    /* ── TABELLE E COMPONENTI ── */
    .tbl-scroll { border-radius: 8px; overflow-x: auto; overflow-y: auto; box-shadow: 0 4px 10px rgba(0,0,0,0.2); background: #181818; margin-bottom: 1rem; }
    .cal-table { width: 100%; border-collapse: collapse; font-size: 0.85rem; color: #dcddde; }
    .cal-table th { background: #202225; color: #b3b3b3; padding: 12px; text-align: left; border-bottom: 1px solid #2f3136; }
    .cal-table td { padding: 10px; border-bottom: 1px solid #282828; }
    .cal-table tr:hover td { background: #2f3136; }
    .num { text-align: center !important; }

    /* Medaglie e Gerarchia Righe */
    .row-gold td { background: rgba(255,187,0,0.07) !important; }
    .row-silver td { background: rgba(180,180,180,0.05) !important; }
    .row-bronze td { background: rgba(180,100,40,0.06) !important; }
    .sep-row td { background: #202225 !important; color: #8e9297; font-size: 0.7rem; font-weight: 700; text-align: center; text-transform: uppercase; }
    .title-row td { font-size: 1.25rem; color: #ffffff; text-transform: uppercase; padding-top: 8px !important; padding-bottom: 8px !important; text-align: center; font-weight: 700; }
    /* Barra Percentuale Custom */
    .pct-wrap { display: flex; align-items: center; gap: 6px; }
    .pct-track { width: 60px; background: #282828; height: 6px; border-radius: 3px; flex-shrink: 0; }
    .pct-label { font-weight: 700; font-size: 0.75rem; white-space: nowrap; }

    /* Mobile Overrides */
    @media screen and (max-width: 768px) {
        .hide-mob { display: none !important; }
        .main-title { font-size: 1.8rem; }
        .sub-title { font-size: 0.9rem; }
        .section-title, .section-title-red, .section-title-blue { font-size: 0.9rem; padding: 0.6rem 0.8rem; }
        .cal-table td, .cal-table th { font-size: 13px !important; padding: 8px 5px !important; }
    }
            
    footer, #MainMenu { visibility: hidden; }
     
</style>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────
#  2. MENU DI NAVIGAZIONE INFERIORE
# ──────────────────────────────────────────────

st.markdown("""
<div class="bottom-nav">
    <a href="#statistiche" class="nav-item">
        <span class="nav-icon">📊</span>
        <span class="nav-label">Rank</span>
    </a>
    <a href="#reti" class="nav-item">
        <span class="nav-icon">🎯</span>
        <span class="nav-label">Gol Stats</span>
    </a>
    <a href="#calendario" class="nav-item">
        <span class="nav-icon">📅</span>
        <span class="nav-label">Calendario</span>
    </a>
    <a href="#previsioni" class="nav-item">
        <span class="nav-icon">🔮</span>
        <span class="nav-label">Predict</span>
    </a>
</div>
""", unsafe_allow_html=True)


# ──────────────────────────────────────────────
#  3. CONNESSIONE DB E DATI
# ──────────────────────────────────────────────
conn = st.connection("calcio_db", type="sql", url="sqlite:///calcio.db")

@st.cache_data(ttl=3600)
def query_leghe():
    return conn.query(query.LISTA_LEGHE_SQL)["lega"].tolist()

def _soglia_widget(label: str, key: str) -> float:
    ss_key = f"_soglia_val_{key}"
    if ss_key not in st.session_state: st.session_state[ss_key] = 2.5
    if st.session_state.get(key) is None: st.session_state[key] = st.session_state[ss_key]
    val = st.segmented_control(label, options=[2.5, 3.5], key=key)
    if val is not None: st.session_state[ss_key] = val
    return st.session_state[ss_key]


# ──────────────────────────────────────────────
#  4. HELPERS GENERATORI TABELLE HTML
# ──────────────────────────────────────────────
def pct_bar_html(value, color):
    return (
        f'<div class="pct-wrap">'
        f'<div class="pct-track"><div style="width:{value}%; background:{color}; height:100%; border-radius:3px;"></div></div>'
        f'<span class="pct-label" style="color:{color}">{value}%</span>'
        f'</div>'
    )

def build_stats_table(df, tipo, soglia):
    rows = ""
    is_over = (tipo == "over")
    val_col = "n_over" if is_over else "n_under"
    MEDALS = {1: "🥇", 2: "🥈", 3: "🥉"}
    ROW_CLASS = {1: "row-gold", 2: "row-silver", 3: "row-bronze"}
    

    for rank, (_, r) in enumerate(df.iterrows(), start=1):
        if rank == 6: rows += f"<tr class='sep-row'><td colspan='5'>— Altre Squadre —</td></tr>"
        pct = r["pct"]
        color = ("#FFBB00" if pct >= 75 else "#FFD667") if is_over else ("#0080FF" if pct >= 75 else "#5AAAFA")
        row_cls = ROW_CLASS.get(rank, "")
        rank_cel = MEDALS[rank] if rank <= 3 else str(rank)

        rows += (
            f"<tr class='{row_cls}'>"
            f"<td class='num'>{rank_cel}</td>"
            f"<td class='hide-mob'>{r['lega']}</td>"
            f"<td><b>{r['squadra']}</b></td>"
            f"<td class='num'>{int(r[val_col])}/{int(r['partite'])}</td>"
            f"<td>{pct_bar_html(pct, color)}</td>"
            f"</tr>"
        )
    return f"<div class='tbl-scroll'><table class='cal-table'><thead><tr class='title-row'><td colspan='5'>top {tipo}</td></tr><tr><th style='text-align:center;'>#</th><th class='hide-mob'>Lega</th><th>Squadra</th><th style='text-align:center;'>Esiti</th><th style= 'text-transform:uppercase;'>% {tipo}</th></tr></thead><tbody>{rows}</tbody></table></div>"

def build_calendario(df):
    rows = ""
    for _, r in df.iterrows():
        dt = r['data_ora'].strftime('%d/%m - %H:%M') if isinstance(r['data_ora'], datetime) else str(r['data_ora'])[:16]
        rows += (
            f"<tr>"
            f"<td class='num' style='color:#5865F2; font-weight:700'>{r['giornata']}</td>"
            f"<td style='text-align:center;'><b>{r['squadra_casa']}</b></td>"
            f"<td style='text-align:center; color:#8e9297'>vs</td>"
            f"<td style='text-align:center;'><b>{r['squadra_trasferta']}</b></td>"
            f"<td style='color:#8e9297;'>{dt}</td>"
            f"</tr>"
        )
    return f"<div class='tbl-scroll'><table class='cal-table'><thead><tr><th style='text-align:center;'>Turno</th><th style='text-align:center;'>Casa</th><th></th><th style='text-align:center;'>Trasferta</th><th>Data</th></tr></thead><tbody>{rows}</tbody></table></div>"

def build_prediction_table(df):
    rows = ""
    for _, r in df.iterrows():
        c = r["Colore"]
        rows += (
            f"<tr>"
            f"<td><b>{r['Partita']}</b></td>"
            f"<td class='num hide-mob'>{r['Gol Attesi Casa']}</td>"
            f"<td class='num hide-mob'>{r['Gol Attesi Trasferta']}</td>"
            f"<td class='num hide-mob'><b>{r['Gol Attesi Totali']}</b></td>"
            f"<td><span style='color:{c};font-weight:bold'>{r['Esito']}</span></td>"
            f"<td>{pct_bar_html(r['Prob %'], c)}</td>"
            f"</tr>"
        )
    return f"<div class='tbl-scroll'><table class='cal-table'><thead><tr><th>Match</th><th class='num hide-mob'>xG C</th><th class='num hide-mob'>xG T</th><th class='num hide-mob'>Tot</th><th>Consiglio</th><th>Affidabilità</th></tr></thead><tbody>{rows}</tbody></table></div>"

def build_gol_table(df):
    rows = ""
    for _, r in df.iterrows():
        rows += (
            f"<tr>"
            f"<td><b>{r['squadra']}</b></td>"
            f"<td style='color:#1DB954; text-align:center'>{int(r['gfc'])}</td>"
            f"<td style='color:#ED4245; text-align:center'>{int(r['gsc'])}</td>"
            f"<td class='hide-mob' style='color:#1DB954; text-align:center'>{round(r['mgfc'], 2)}</td>"
            f"<td class='hide-mob' style='color:#ED4245; text-align:center'>{round(r['mgsc'], 2)}</td>"
            f"<td style='color:#5865F2; text-align:center'>{int(r['gft'])}</td>"
            f"<td style='color:#FEE75C; text-align:center'>{int(r['gst'])}</td>"
            f"<td class='hide-mob' style='color:#5865F2; text-align:center'>{round(r['mgft'], 2)}</td>"
            f"<td class='hide-mob' style='color:#FEE75C; text-align:center'>{round(r['mgst'], 2)}</td>"
            f"<td style='text-align:center'><b>{int(r['totgf'])}</b></td>"
            f"<td style='text-align:center'><b>{int(r['totgs'])}</b></td>"
            f"</tr>"
        )
    
    th_html = """
        <th style='text-align:left;' onclick="srt(0,false)">Squadra</th>
        <th style='color:#1DB954; text-align:center' onclick="srt(1,true)">GFC</th>
        <th style='color:#ED4245; text-align:center' onclick="srt(2,true)">GSC</th>
        <th class='hide-mob' style='color:#1DB954; text-align:center' onclick="srt(3,true)">Med GFC</th>
        <th class='hide-mob' style='color:#ED4245; text-align:center' onclick="srt(4,true)">Med GSC</th>
        <th style='color:#5865F2; text-align:center' onclick="srt(5,true)">GFT</th>
        <th style='color:#FEE75C; text-align:center' onclick="srt(6,true)">GST</th>
        <th class='hide-mob' style='color:#5865F2; text-align:center' onclick="srt(7,true)">Med GFT</th>
        <th class='hide-mob' style='color:#FEE75C; text-align:center' onclick="srt(8,true)">Med GST</th>
        <th style='text-align:center' onclick="srt(9,true)">Tot GF</th>
        <th style='text-align:center' onclick="srt(10,true)">Tot GS</th>
    """
    
    return f"""
    <div id="gol-table-container">
    <style>
      #gol-table-container .wrap {{ width:100%; overflow-x:auto; border-radius:8px; background:#181818; }}
      #gol-table-container table {{ width:100%; border-collapse:collapse; white-space:nowrap; font-size:13px; table-layout:fixed; }}
      #gol-table-container th, #gol-table-container td {{ word-break:break-word; }}
      #gol-table-container th {{ background:#202225; padding:12px; border-bottom:2px solid #2f3136; cursor:pointer; user-select:none; }}
      #gol-table-container td {{ padding:10px; border-bottom:1px solid #282828; color:#dcddde; }}
      #gol-table-container tr:hover td {{ background:#2f3136; }}
      @media screen and (max-width: 768px) {{
        #gol-table-container .wrap {{ overflow-x:hidden; }}
        #gol-table-container table {{ width:auto !important; white-space:normal !important; table-layout:auto !important; }}
      }}
    </style>
    <div class="wrap">
      <table id="gol-tbl"><thead><tr>{th_html}</tr></thead><tbody>{rows}</tbody></table>
    </div>
    <script>
    (function(){{
      var d = {{}};
      window.srt = function(col, num) {{
        var tbl = document.getElementById('gol-tbl'), tbody = tbl.querySelector('tbody'),
            rows = Array.from(tbody.querySelectorAll('tr'));
        d[col] = !d[col]; var asc = d[col];
        rows.sort(function(a, b){{
          var va = a.cells[col].innerText.trim(), vb = b.cells[col].innerText.trim();
          if(num){{ va = parseFloat(va) || 0; vb = parseFloat(vb) || 0; }}
          return asc ? (va < vb ? -1 : va > vb ? 1 : 0) : (va > vb ? -1 : va < vb ? 1 : 0);
        }});
        rows.forEach(function(r){{ tbody.appendChild(r); }});
      }};
    }})();
    </script>
    </div>
    """


# ──────────────────────────────────────────────
#  5. LOGICA PREVISIONI (POISSON / DIXON-COLES)
# ──────────────────────────────────────────────
def dixon_coles_correction(h, a, exp_h, exp_a, rho):
    if h == 0 and a == 0: return max(1e-9, 1 - (exp_h * exp_a * rho))
    elif h == 0 and a == 1: return max(1e-9, 1 + (exp_h * rho))
    elif h == 1 and a == 0: return max(1e-9, 1 + (exp_a * rho))
    elif h == 1 and a == 1: return max(1e-9, 1 - rho)
    return 1.0

def compute_weighted_strengths(df, alpha):
    df = df.copy()
    max_g = df['giornata'].max()
    df['w'] = np.exp(-alpha * (max_g - df['giornata']))
    tot_w = df['w'].sum()
    avg_h = (df['gol_casa'] * df['w']).sum() / tot_w
    avg_a = (df['gol_trasferta'] * df['w']).sum() / tot_w
    
    teams = sorted(set(df['squadra_casa']) | set(df['squadra_trasferta']))
    records = []
    for t in teams:
        hm, am = df[df['squadra_casa']==t], df[df['squadra_trasferta']==t]
        if hm['w'].sum() == 0 or am['w'].sum() == 0: continue
        records.append({
            'squadra': t,
            'avg_gfc': (hm['gol_casa']*hm['w']).sum() / hm['w'].sum(),
            'avg_gsc': (hm['gol_trasferta']*hm['w']).sum() / hm['w'].sum(),
            'avg_gft': (am['gol_trasferta']*am['w']).sum() / am['w'].sum(),
            'avg_gst': (am['gol_casa']*am['w']).sum() / am['w'].sum(),
        })
    return pd.DataFrame(records).set_index('squadra'), avg_h, avg_a

def estimate_rho(df, strengths, avg_h, avg_a, alpha):
    low = df[(df['gol_casa']<=1) & (df['gol_trasferta']<=1)].copy()
    if len(low) < 5: return -0.15
    max_g = df['giornata'].max()
    def neg_ll(rho):
        ll = 0.0
        for _, r in low.iterrows():
            sh, sa = r['squadra_casa'], r['squadra_trasferta']
            if sh not in strengths.index or sa not in strengths.index: continue
            exph = strengths.loc[sh,'avg_gfc'] * strengths.loc[sa,'avg_gst'] / avg_a
            expa = strengths.loc[sa,'avg_gft'] * strengths.loc[sh,'avg_gsc'] / avg_h
            tau = dixon_coles_correction(int(r['gol_casa']), int(r['gol_trasferta']), exph, expa, rho)
            ll += np.exp(-alpha*(max_g-r['giornata'])) * np.log(max(tau, 1e-9))
        return -ll
    res = minimize_scalar(neg_ll, bounds=(-0.5, 0.1), method='bounded')
    return round(res.x, 4) if res.success else -0.15

def get_predictions_section(lega, soglia, alpha):
    df_raw = conn.query(query.MATCH_DATA_SQL, params={"lega": lega}, ttl=3600)
    if df_raw.empty or len(df_raw) < 10:
        st.warning("Dati insufficienti per le previsioni.")
        return

    strengths, avg_h, avg_a = compute_weighted_strengths(df_raw, alpha)
    rho = estimate_rho(df_raw, strengths, avg_h, avg_a, alpha)
    df_n = conn.query(query.CALENDARIO_LEGA_SQL, params={"lega": lega}, ttl=3600)
    
    if df_n.empty:
        st.info("Nessun match futuro in calendario.")
        return

    df_n['data_ora'] = pd.to_datetime(df_n['data_ora'])
    prox = df_n.sort_values('data_ora').iloc[0]['giornata']
    matches = df_n[df_n['giornata'] == prox]

    preds = []
    for _, m in matches.iterrows():
        h, a = m['squadra_casa'], m['squadra_trasferta']
        if h not in strengths.index or a not in strengths.index: continue
        exph = strengths.loc[h,'avg_gfc'] * strengths.loc[a,'avg_gst'] / avg_a
        expa = strengths.loc[a,'avg_gft'] * strengths.loc[h,'avg_gsc'] / avg_h
        
        po, pu = 0.0, 0.0
        for ih in range(10):
            for ia in range(10):
                p = poisson.pmf(ih, exph) * poisson.pmf(ia, expa) * dixon_coles_correction(ih, ia, exph, expa, rho)
                if (ih+ia) > soglia: po += p
                else: pu += p
        
        prob = round((po/(po+pu))*100, 1) if po > pu else round((pu/(po+pu))*100, 1)
        res_label = f"🔥 Over {soglia}" if po > pu else f"❄️ Under {soglia}"
        color = ("#FFBB00" if prob >= 65 else "#FFE9AB") if po > pu else ("#0080FF" if prob >= 65 else "#9ECEFF")
        
        preds.append({
            "Partita": f"{h} vs {a}", "Gol Attesi Casa": round(exph, 2), "Gol Attesi Trasferta": round(expa, 2),
            "Gol Attesi Totali": round(exph+expa, 2), "Esito": res_label, "Prob %": prob, "Colore": color
        })
    if preds: st.html(build_prediction_table(pd.DataFrame(preds)))


# ──────────────────────────────────────────────
#  6. LAYOUT INTERFACCIA PRINCIPALE
# ──────────────────────────────────────────────
st.markdown('<div class="main-title">XG Football Analytics</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Advanced Data & Predictions System</div>', unsafe_allow_html=True)

leghe_disp = query_leghe()

# SEZIONE 1: STATISTICHE
st.markdown('<div id="statistiche" class="section-title">📊 Ranking </div>', unsafe_allow_html=True)
soglia_stats = _soglia_widget("Soglia Gol:", "stats_soglia")
c1, c2 = st.columns(2)
with c1:
    df_ov = conn.query(query.TOP_OVER_SQL, params={"soglia": soglia_stats, "limit": 20}, ttl=3600)
    st.html(build_stats_table(df_ov, "over", soglia_stats))
with c2:
    df_un = conn.query(query.TOP_UNDER_SQL, params={"soglia": soglia_stats, "limit": 20}, ttl=3600)
    st.html(build_stats_table(df_un, "under", soglia_stats))

st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

# SEZIONE 2: RETI
st.markdown('<div id="reti" class="section-title-blue">🎯 Performance Reti </div>', unsafe_allow_html=True)
lega_sel = st.selectbox("Seleziona Lega:", options=leghe_disp, key="gol_lega")
df_gol = conn.query(query.GOL_LEGA_SQL, params={"lega": lega_sel}, ttl=3600)
st.html(build_gol_table(df_gol))

st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

# SEZIONE 3: CALENDARIO
st.markdown('<div id="calendario" class="section-title-blue">📅 Calendario Prossimo Turno</div>', unsafe_allow_html=True)
lega_cal = st.selectbox("Seleziona Lega:", options=leghe_disp, key="cal_box")
df_next = conn.query(query.CALENDARIO_LEGA_SQL, params={"lega": lega_cal}, ttl=3600)
if not df_next.empty:
    df_next['data_ora'] = pd.to_datetime(df_next['data_ora'])
    g_prox = df_next.sort_values('data_ora').iloc[0]['giornata']
    st.html(build_calendario(df_next[df_next['giornata'] == g_prox]))

st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

# SEZIONE 4: PREVISIONI
st.markdown('<div id="previsioni" class="section-title-red">🔮 Previsioni </div>', unsafe_allow_html=True)
cp1, cp2, cp3 = st.columns([2, 1, 1])
with cp1: lega_pred = st.selectbox("Lega:", options=leghe_disp, key="pred_box")
with cp2: soglia_pred = _soglia_widget("Soglia Pred:", "pred_soglia")
with cp3:
    forma = st.toggle("Forma Recente", value=True, key="forma", help="Applica un peso maggiore alle partite più recenti per stimare le forze squadra.")
    alpha = 0.12 if forma else 0.0
with st.spinner("Calcolo in corso..."):
    get_predictions_section(lega_pred, soglia_pred, alpha)

st.markdown("<div style='text-align:center; color:#8e9297; font-size:0.8rem; '>──── Play Responsibly • Mathematical Models Only ────</div>", unsafe_allow_html=True)