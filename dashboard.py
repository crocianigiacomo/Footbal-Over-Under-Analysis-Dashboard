import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
from scipy.stats import poisson
from datetime import datetime
import query  

# ──────────────────────────────────────────────
#  CONFIG PAGINA E TEMA
# ──────────────────────────────────────────────
st.set_page_config(
    page_title="XG Football Analytics",
    layout="wide",
    initial_sidebar_state="collapsed",
)

components.html("""
<script>
    var w = window.innerWidth;
    var params = new URLSearchParams(window.parent.location.search);
    if (!params.get('sw') || Math.abs(parseInt(params.get('sw')) - w) > 100) {
        params.set('sw', w);
        window.parent.history.replaceState({}, '', '?' + params.toString());
        window.parent.location.reload();
    }
</script>
""", height=0)

screen_w = int(st.query_params.get("sw", 1200))
is_mobile = screen_w < 768

st.markdown("""
<style>
    
    
    [data-testid="stVerticalBlock"] > div {
    gap: 0.5rem !important;
    }
            
    /* Spaziature generali */
    .block-container {
        padding-top: 2rem !important;
        padding-bottom: 2rem !important;
    }
    
    /* Titoli Moderni */
    .main-title {
        font-size: 2.5rem; font-weight: 800;
        color: #ffffff; letter-spacing: -0.5px; 
        margin-top: 0 !important; margin-bottom: 0.2rem; text-align: center;
        font-family: 'Inter', 'Segoe UI', sans-serif;
    }
    .sub-title {
        font-size: 1.1rem; color: #b3b3b3; margin-bottom: 2.5rem;
        font-weight: 500; text-align: center;
        font-family: 'Inter', 'Segoe UI', sans-serif;
    }
    
    /* Sezioni con bordi curvi stile Card */
    .section-title {
        font-size: 1.1rem; font-weight: 700; color: #ffffff;
        background: #181818; border-left: 4px solid #1DB954; /* Spotify Green */
        padding: 0.6rem 1rem; border-radius: 6px; margin-bottom: 1rem;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .section-title-red {
        font-size: 1.1rem; font-weight: 700; color: #ffffff;
        background: #181818; border-left: 4px solid #ED4245; /* Discord Red */
        padding: 0.6rem 1rem; border-radius: 6px; margin-bottom: 1rem;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .section-title-blue {
        font-size: 1.1rem; font-weight: 700; color: #ffffff;
        background: #181818; border-left: 4px solid #5865F2; /* Discord Blurple */
        padding: 0.6rem 1rem; border-radius: 6px; margin-bottom: 1rem;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    
    .divider { border: none; border-top: 1px solid #282828; margin: 1rem 0; }

    /* Tabelle Generiche in Streamlit (Over/Under, Calendario, Previsioni) */
    .cal-table {
        width: 100%; border-collapse: separate; border-spacing: 0;
        font-size: 0.85rem; color: #dcddde; background: #181818;
        border-radius: 8px; overflow: hidden;
    }
    .cal-table th {
        background: #202225; color: #b3b3b3;
        padding: 10px 12px; text-align: left;
        border-bottom: 1px solid #2f3136; white-space: nowrap; font-weight: 600;
    }
    .cal-table td {
        padding: 8px 12px; border-bottom: 1px solid #2f3136;
        white-space: normal;
    }
    @media screen and (max-width: 768px) {
        .hide-mob { display: none !important; }
        .cal-table td, .cal-table th { 
            padding: 6px 4px !important; 
            font-size: 11px !important;
        }
        .pct-bar { width: 40px !important; }
    }
    .cal-table tr:last-child td { border-bottom: none; }
    .cal-table tr:hover td { background: #2f3136; transition: background 0.2s; }
    
    .num { text-align: center !important; }
    
    .pct-wrap { display: flex; align-items: center; gap: 8px; }
    .pct-bar  { height: 6px; border-radius: 3px; flex-shrink: 0; }
    .pct-val  { font-weight: 600; font-size: 0.8rem; }
    .tbl-scroll { border-radius: 8px; overflow-x: auto; box-shadow: 0 4px 10px rgba(0,0,0,0.2); }

    footer, #MainMenu {visibility: hidden;}
    
    /* Selectbox Interattivo */
    div[data-baseweb="select"], div[data-baseweb="select"] * { cursor: pointer !important; }
    div[data-baseweb="select"]:hover { border-color: #5865F2 !important; transition: border-color 0.3s ease; }
</style>
""", unsafe_allow_html=True)


# ──────────────────────────────────────────────
#  CONNESSIONE DB E DATI
# ──────────────────────────────────────────────
conn = st.connection("calcio_db", type="sql", url="sqlite:///calcio.db")

def query_leghe():
    return conn.query(query.LISTA_LEGHE_SQL)["lega"].tolist()


# ──────────────────────────────────────────────
#  HELPERS HTML (GENERATORI TABELLE)
# ──────────────────────────────────────────────
def pct_bar(value, color):
    w = int(min(value, 80))
    return f'<div class="pct-wrap"><div class="pct-bar" style="width:{w}px;background:{color}"></div><span class="pct-val" style="color:{color};font-weight:600;font-size:0.75rem">{value}%</span></div>'

def build_stats_table(df, tipo, soglia):
    rows = ""
    is_over = tipo == "over"
    val_col = "n_over" if is_over else "n_under"
    
    for i, r in df.iterrows():
        pct = r["pct"]
        if is_over:
            color = "#1DB954" if pct >= 75 else "#FEE75C" if pct >= 60 else "#9e9e9e"
        else:
            color = "#ED4245" if pct >= 75 else "#FEE75C" if pct >= 60 else "#9e9e9e"
            
        rows += (
            f"<tr>"
            f"<td class='num hide-mob'>{i+1}</td>"
            f"<td class='hide-mob'>{r['lega']}</td>"
            f"<td><b>{r['squadra']}</b></td>"
            f"<td class='num'>{int(r[val_col])} / {int(r['partite'])}</td>"
            f"<td>{pct_bar(pct, color)}</td>"
            f"</tr>"
        )
        
    th_label = f"% {tipo.capitalize()} {soglia}"
    return (
        f"<div class='tbl-scroll'><table class='cal-table'>"
        f"<thead><tr><th class='num hide-mob'>#</th><th class='hide-mob'>Lega</th><th>Squadra</th><th class='num'>Esiti</th><th>{th_label}</th></tr></thead>"
        f"<tbody>{rows}</tbody></table></div>"
    )

def build_calendario(df):
    rows = ""
    for _, r in df.iterrows():
        try:
            dt = datetime.strptime(r['data_ora'], '%Y-%m-%dT%H:%M:%SZ')
            data_fmt = dt.strftime('%d/%m %H:%M')
        except:
            data_fmt = r['data_ora']

        rows += (
            f"<tr>"
            f"<td class='num' style='color:#5865F2; font-weight:700'>{r['giornata']}</td>"
            f"<td><b>{r['squadra_casa']}</b></td>"
            f"<td><b>{r['squadra_trasferta']}</b></td>"
            f"<td style='color:#8e9297;'>{data_fmt}</td>"
            f"</tr>"
        )
        
    return (
        "<div class='tbl-scroll'><table class='cal-table'>"
        "<thead><tr><th class='num'>G.</th><th>Casa</th><th>Trasferta</th><th>Data (UTC)</th></tr></thead>"
        f"<tbody>{rows}</tbody></table></div>"
    )

def build_prediction_table(df):
    rows = ""
    for i, r in df.iterrows():
        color = r["Colore"]
        rows += (
            f"<tr>"
            f"<td><b>{r['Partita']}</b></td>"
            f"<td><b>{r['Gol Attesi Casa']}</b></td>"
            f"<td><b>{r['Gol Attesi Trasferta']}</b></td>"
            f"<td><b>{r['Gol Attesi Totali']}</b></td>"
            f"<td><span style='font-size:0.85rem; font-weight:bold; color:{color}; padding:2px 6px; background:#282828; border-radius:4px;'>{r['Esito']}</span></td>"
            f"<td>{pct_bar(r['Prob %'], color)}</td>"
            f"</tr>"
        )
        
    return (
        "<div class='tbl-scroll'><table class='cal-table'>"
        "<thead><tr><th>Match</th><th class='hide-mob'>Gol Attesi Casa</th><th class='hide-mob'>Gol Attesi Trasferta</th><th class='hide-mob'>Gol Attesi Totali</th><th>Consiglio</th><th>Affidabilità Modello</th></tr></thead>"
        f"<tbody>{rows}</tbody></table></div>"
    )

def build_gol_table(df):
    rows = ""
    for _, r in df.iterrows():
        rows += (
            f"<tr>"
            f"<td><b>{r['squadra']}</b></td>"
            f"<td style='color:#1DB954; text-align:center'>{int(r['gfc'])}</td>"
            f"<td style='color:#ED4245; text-align:center'>{int(r['gsc'])}</td>"
            f"<td class='hide-mob' style='color:#1DB954; text-align:center'>{round(float(r['mgfc']), 2)}</td>"
            f"<td class='hide-mob' style='color:#ED4245; text-align:center'>{round(float(r['mgsc']), 2)}</td>"
            f"<td style='color:#5865F2; text-align:center'>{int(r['gft'])}</td>"
            f"<td style='color:#FEE75C; text-align:center'>{int(r['gst'])}</td>"
            f"<td class='hide-mob' style='color:#5865F2; text-align:center'>{round(float(r['mgft']), 2)}</td>"
            f"<td class='hide-mob' style='color:#FEE75C; text-align:center'>{round(float(r['mgst']), 2)}</td>"
            f"<td style='text-align:center'><b>{int(r['totgf'])}</b></td>"
            f"<td style='text-align:center'><b>{int(r['totgs'])}</b></td>"
            f"</tr>"
        )

    # Config: Indice, Colore Testo, Nome Colonna, HideOnMobile
    header_cols = [
        (0, "", "Squadra", False),
        (1, "#1DB954", "GF Casa", False),
        (2, "#ED4245", "GS Casa", False),
        (3, "#1DB954", "Med GF Casa", True),
        (4, "#ED4245", "Med GS Casa", True),
        (5, "#5865F2", "GF Trasf", False),
        (6, "#FEE75C", "GS Trasf", False),
        (7, "#5865F2", "Med GF Trasf", True),
        (8, "#FEE75C", "Med GS Trasf", True),
        (9, "", "Tot GF", False),
        (10, "", "Tot GS", False),
    ]

    th_html = ""
    for idx, color, label, hide in header_cols:
        c_class = "hide-mob" if hide else ""
        c_style = f"color:{color}; text-align:{'left' if idx==0 else 'center'};"
        th_html += f'<th class="{c_class}" onclick="srt({idx}, {str(idx!=0).lower()})" style="{c_style}">{label}</th>\n'

    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ background: #121212; font-family: "Inter", "Segoe UI", sans-serif; font-size: 13px; color: #dcddde; }}
  .wrap {{ width: 100%; overflow-x: auto; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.3); background: #181818; }}
  table {{ width: 100%; border-collapse: collapse; white-space: nowrap; }}
  thead tr {{ position: sticky; top: 0; z-index: 2; }}
  th {{ background: #202225; padding: 12px 10px; border-bottom: 2px solid #2f3136; cursor: pointer; user-select: none; font-weight: 600; font-size: 12px; transition: background 0.2s; }}
  th:hover {{ background: #2f3136; color: #ffffff; }}
  td {{ padding: 10px 10px; border-bottom: 1px solid #282828; }}
  tr:hover td {{ background: #2f3136; }}
  th:not(.sort-asc):not(.sort-desc)::after {{ content: " "; font-size: 10px; opacity: 0.35; }}
  .sort-asc::after  {{ content: " ▲"; font-size: 10px; }}
  .sort-desc::after {{ content: " ▼"; font-size: 10px; }}
  
  /* PURE CSS MEDIA QUERY PER IL MOBILE */
  @media screen and (max-width: 768px) {{
    .hide-mob {{ display: none !important; }}
    th, td {{ padding: 10px 6px; font-size: 11px; }}
  }}
</style>
</head>
<body>
<div class="wrap">
<table id="t">
  <thead><tr>{th_html}</tr></thead>
  <tbody>{rows}</tbody>
</table>
</div>
<script>
(function(){{
  var d = {{}};
  window.srt = function(col, num) {{
    var tbl = document.getElementById('t'), tbody = tbl.querySelector('tbody'), ths = tbl.querySelectorAll('thead th'), rows = Array.from(tbody.querySelectorAll('tr'));
    d[col] = !d[col]; var asc = d[col];
    ths.forEach(function(h){{ h.classList.remove('sort-asc','sort-desc'); }});
    ths[col].classList.add(asc ? 'sort-asc' : 'sort-desc');
    rows.sort(function(a, b){{
      var va = a.cells[col] ? a.cells[col].innerText.trim() : '';
      var vb = b.cells[col] ? b.cells[col].innerText.trim() : '';
      if(num){{ va=parseFloat(va)||0; vb=parseFloat(vb)||0; }}
      return asc ? (va<vb?-1:va>vb?1:0) : (va>vb?-1:va<vb?1:0);
    }});
    rows.forEach(function(r){{ tbody.appendChild(r); }});
  }};
}})();
</script>
</body>
</html>"""


# ──────────────────────────────────────────────
#  LOGICA PREVISIONI E POISSON
# ──────────────────────────────────────────────
def get_predictions_section(lega, soglia):
    df_strength = conn.query(query.TEAM_STRENGTH_SQL, params={"lega": lega})
    if df_strength.empty: 
        st.warning("Dati storici insufficienti per questa lega.")
        return
        
    df_strength.set_index('squadra', inplace=True)
    
    df_next = conn.query(query.CALENDARIO_LEGA_SQL, params={"lega": lega})
    if df_next.empty:
        st.info("Nessun match futuro trovato in calendario.")
        return

    prossima_g = df_next['giornata'].min()
    matches = df_next[df_next['giornata'] == prossima_g]
    st.write(f"#### 📅 Turno in analisi: Giornata {prossima_g}")
    
    preds_data = []
    for _, m in matches.iterrows():
        h, a = m['squadra_casa'], m['squadra_trasferta']
        if h in df_strength.index and a in df_strength.index:
            # Calcolo xG (Expected Goals)
            exp_h = (df_strength.loc[h, 'avg_gfc'] * df_strength.loc[a, 'avg_gst']) / df_strength.loc[h, 'avg_gfc_league']
            exp_a = (df_strength.loc[a, 'avg_gft'] * df_strength.loc[h, 'avg_gsc']) / df_strength.loc[h, 'avg_gft_league']
            
            # Calcolo probabilità con distribuzione Poisson (fino a 6 gol)
            over_prob = sum(poisson.pmf(ih, exp_h) * poisson.pmf(ia, exp_a) for ih in range(7) for ia in range(7) if (ih + ia) > soglia)
            prob_o = round(over_prob * 100, 1)
            prob_u = round(100 - prob_o, 1)
            
            if prob_o > prob_u:
                label, prob, color = f"🔥 Over {soglia}", prob_o, "#1DB954"
            else:
                label, prob, color = f"❄️ Under {soglia}", prob_u, "#ED4245"
            
            preds_data.append({
                "Partita": f"{h} vs {a}", 
                "Gol Attesi Casa": round(exp_h, 2), 
                "Gol Attesi Trasferta": round(exp_a, 2),
                "Gol Attesi Totali": round(exp_h + exp_a, 2), 
                "Esito": label, 
                "Prob %": prob, 
                "Colore": color
            })
    
    if preds_data:
        st.markdown(build_prediction_table(pd.DataFrame(preds_data)), unsafe_allow_html=True)


# ──────────────────────────────────────────────
#  LAYOUT INTERFACCIA PRINCIPALE
# ──────────────────────────────────────────────
st.markdown('<div class="main-title">XG Football Analytics</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Advanced Data & Predictions System</div>', unsafe_allow_html=True)

leghe_disp = query_leghe()

# --- SEZIONE 1: STATISTICHE GLOBALI (Senza filtro lega) ---
st.markdown('<div class="section-title">📊 Top Statistiche Globali</div>', unsafe_allow_html=True)
soglia_stats = st.segmented_control("Seleziona Soglia Gol:", [2.5, 3.5], default=2.5, key="stats_soglia")

c1, c2 = st.columns(2, gap="large")
with c1:
    df_ov = conn.query(query.TOP_OVER_SQL, params={"soglia": soglia_stats, "limit": 20})
    st.markdown(build_stats_table(df_ov, "over", soglia_stats), unsafe_allow_html=True)
with c2:
    df_un = conn.query(query.TOP_UNDER_SQL, params={"soglia": soglia_stats, "limit": 20})
    st.markdown(build_stats_table(df_un, "under", soglia_stats), unsafe_allow_html=True)

st.markdown('<hr class="divider">', unsafe_allow_html=True)


# --- SEZIONE 2: CLASSIFICA GOL (Dettaglio per Lega) ---
st.markdown('<div class="section-title-blue">🎯 Performance Reti e Classifica xG</div>', unsafe_allow_html=True)
lega_sel = st.selectbox("Seleziona Lega per visualizzare il dettaglio:", options=leghe_disp, key="gol_lega")
df_gol = conn.query(query.GOL_LEGA_SQL, params={"lega": lega_sel})

# Calcola altezza Iframe dinamica in base al numero di squadre
multiplier = 32 if is_mobile else 42
h_iframe = (len(df_gol) * multiplier)

components.html(build_gol_table(df_gol), height=h_iframe, scrolling=False)

st.markdown('<hr class="divider">', unsafe_allow_html=True)


# --- SEZIONE 3: CALENDARIO PROSSIMO TURNO ---
st.markdown('<div class="section-title-blue">📅 Calendario Prossimo Turno</div>', unsafe_allow_html=True)
lega_cal = st.selectbox("Seleziona Lega:", options=leghe_disp, key="cal_box")
df_next = conn.query(query.CALENDARIO_LEGA_SQL, params={"lega": lega_cal})

if not df_next.empty:
    prossima_g_cal = df_next['giornata'].min()
    st.write(f"#### Giornata {prossima_g_cal}")
    st.markdown(build_calendario(df_next[df_next['giornata'] == prossima_g_cal]), unsafe_allow_html=True)
else:
    st.info("Nessuna partita futura in programma per questa lega.")

st.markdown('<hr class="divider">', unsafe_allow_html=True)


# --- SEZIONE 4: PREVISIONI ALGORITMICHE (Poisson) ---
st.markdown('<div class="section-title-red">🔮 Previsioni Algoritmiche</div>', unsafe_allow_html=True)

c_p1, c_p2 = st.columns([2, 1])
with c_p1: 
    lega_pred = st.selectbox("Analizza Lega:", options=leghe_disp, key="pred_box")
with c_p2: 
    soglia_pred = st.segmented_control("Soglia Previsione:", [2.5, 3.5], default=2.5, key="pred_soglia")

get_predictions_section(lega_pred, soglia_pred)

# --- FOOTER ---
st.markdown(
    "<div style='text-align:center; color:#8e9297; font-size:0.8rem; margin-top:3rem; margin-bottom: 2rem;'>"
    "Play Responsibly • Algorithm relies purely on historical mathematical models."
    "</div>", 
    unsafe_allow_html=True
)