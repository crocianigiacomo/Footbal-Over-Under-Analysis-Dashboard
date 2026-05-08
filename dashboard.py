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
    /* Spaziature generali Streamlit */
    [data-testid="stVerticalBlock"] > div { gap: 0.5rem !important; }
    .block-container {
        padding-top: 2rem !important;
        padding-bottom: 2rem !important;
    }

    /* ── TITOLI PRINCIPALI ── */
    .main-title {
        font-size: 2.5rem; font-weight: 800;
        color: #ffffff; letter-spacing: -0.5px;
        margin-top: 2rem; margin-bottom: 0.2rem; text-align: center;
        font-family: 'Inter', 'Segoe UI', sans-serif;
    }
    .sub-title {
        font-size: 1.1rem; color: #b3b3b3; margin-bottom: 2.5rem;
        font-weight: 500; text-align: center;
        font-family: 'Inter', 'Segoe UI', sans-serif;
    }

    /* ── TITOLI SEZIONI ── */
    .section-title, .section-title-red, .section-title-blue {
        font-size: 1.1rem; font-weight: 700; color: #ffffff;
        background: #181818; padding: 0.6rem 1rem; 
        border-radius: 6px; margin-bottom: 1rem;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .section-title { border-left: 4px solid #1DB954; }
    .section-title-red { border-left: 4px solid #ED4245; }
    .section-title-blue { border-left: 4px solid #5865F2; }

    /* ── LINEA DIVISORIA E BARRE PERCENTUALI ── */
    .divider { border: none; border-top: 1px solid #282828; margin: 1rem 0; }
    
    .pct-wrap { display: flex; align-items: center; gap: 6px; min-width: 0; }
    .pct-track {
        width: clamp(36px, 10vw, 100px);
        background: #282828; height: 6px; border-radius: 3px; flex-shrink: 0;
    }
    .pct-label { font-weight: 600; font-size: 0.75rem; white-space: nowrap; }

    /* ── TABELLE GENERICHE ── */
    .tbl-scroll { border-radius: 8px; overflow-x: auto; box-shadow: 0 4px 10px rgba(0,0,0,0.2); }
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
    .cal-table td { padding: 8px 12px; border-bottom: 1px solid #2f3136; white-space: normal; }
    .cal-table tr:last-child td { border-bottom: none; }
    .cal-table tr:hover td { background: #2f3136; transition: background 0.2s; }
    .num { text-align: center !important; }

    /* ── GERARCHIA RIGHE TABELLA E MEDAGLIE ── */
    .row-gold td { background: rgba(255,187,0,0.07) !important; }
    .row-silver td { background: rgba(180,180,180,0.05) !important; }
    .row-bronze td { background: rgba(180,100,40,0.06) !important; }
    .row-gold:hover td { background: rgba(255,187,0,0.13) !important; }
    .row-silver:hover td { background: rgba(180,180,180,0.10) !important; }
    .row-bronze:hover td { background: rgba(180,100,40,0.11) !important; }
    .rank-badge { display: inline-flex; align-items: center; justify-content: center; font-size: 1rem; }
    .sep-row td {
        padding: 4px 12px !important; background: #202225 !important;
        color: #8e9297 !important; font-size: 0.7rem !important;
        font-weight: 700 !important; letter-spacing: 0.08em !important;
        text-transform: uppercase !important;
        border-top: 1px solid #2f3136 !important; border-bottom: 1px solid #2f3136 !important;
    }

    /* ── MOBILE OVERRIDES ── */
    @media screen and (max-width: 768px) {
        .block-container { padding-top: 0.5rem !important; }
        .hide-mob { display: none !important; }
        .cal-table td, .cal-table th { padding: 8px 5px !important; font-size: 13px !important; }
        .main-title { font-size: 1.7rem !important; }
        .sub-title  { font-size: 0.95rem !important; margin-bottom: 1rem !important; }
        div[data-baseweb="select"] > div { min-height: 44px !important; }
        [data-testid="stSegmentedControl"] button { min-height: 44px !important; font-size: 14px !important; padding: 0 18px !important; }
    }

    footer, #MainMenu { visibility: hidden; }

    /* ── STILI WIDGET STREAMLIT (SELECTBOX & SEGMENTED CONTROL) ── */
    div[data-baseweb="select"] > div { background: #1e1e1e !important; border-color: #2f3136 !important; border-radius: 8px !important; cursor: pointer !important; }
    div[data-baseweb="select"] > div:hover { border-color: #5865F2 !important; }
    div[data-baseweb="select"] input, div[data-baseweb="select"] [role="combobox"], div[data-baseweb="select"] * { cursor: pointer !important; user-select: none !important; }
    div[data-baseweb="select"] svg { color: #b3b3b3 !important; }
    [data-baseweb="menu"] { background: #1e1e1e !important; border: 1px solid #2f3136 !important; border-radius: 8px !important; box-shadow: 0 8px 24px rgba(0,0,0,0.4) !important; }
    [data-baseweb="option"] { background: #1e1e1e !important; color: #dcddde !important; cursor: pointer !important; }
    [data-baseweb="option"]:hover { background: #2f3136 !important; }
    
    [data-testid="stSegmentedControl"] > div { background: #1e1e1e !important; border: 1px solid #2f3136 !important; border-radius: 8px !important; padding: 3px !important; gap: 3px !important; }
    [data-testid="stSegmentedControl"] button { border-radius: 6px !important; font-weight: 600 !important; color: #8e9297 !important; transition: background 0.2s, color 0.2s !important; border: none !important; }
    [data-testid="stSegmentedControl"] button[aria-selected="true"] { background: #5865F2 !important; color: #ffffff !important; box-shadow: 0 2px 8px rgba(88,101,242,0.4) !important; }
    [data-testid="stWidgetLabel"] p { color: #b3b3b3 !important; font-size: 0.8rem !important; font-weight: 600 !important; letter-spacing: 0.04em !important; text-transform: uppercase !important; }
</style>
""", unsafe_allow_html=True)


# ──────────────────────────────────────────────
#  2. CONNESSIONE E HELPERS DATI
# ──────────────────────────────────────────────
conn = st.connection("calcio_db", type="sql", url="sqlite:///calcio.db")

@st.cache_data(ttl=3600)
def query_leghe():
    """Recupera la lista delle leghe dal DB."""
    return conn.query(query.LISTA_LEGHE_SQL)["lega"].tolist()

def _soglia_widget(label: str, key: str) -> float:
    """Gestisce il widget della soglia evitando reset indesiderati in Streamlit."""
    ss_key = f"_soglia_val_{key}"
    if ss_key not in st.session_state:
        st.session_state[ss_key] = 2.5

    if st.session_state.get(key) is None:
        st.session_state[key] = st.session_state[ss_key]

    val = st.segmented_control(label, options=[2.5, 3.5], key=key)
    if val is not None:
        st.session_state[ss_key] = val

    return st.session_state[ss_key]


# ──────────────────────────────────────────────
#  3. GENERATORI COMPONENTI HTML / SVG
# ──────────────────────────────────────────────
EMPTY_CALENDAR_SVG = """
<svg width="64" height="64" viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg">
  <rect x="8" y="14" width="48" height="42" rx="6" stroke="#5865F2" stroke-width="2.5"/>
  <line x1="8" y1="26" x2="56" y2="26" stroke="#5865F2" stroke-width="2.5"/>
  <rect x="20" y="8" width="4" height="12" rx="2" fill="#5865F2"/>
  <rect x="40" y="8" width="4" height="12" rx="2" fill="#5865F2"/>
  <circle cx="22" cy="38" r="3" fill="#8e9297"/>
  <circle cx="32" cy="38" r="3" fill="#8e9297"/>
  <circle cx="42" cy="38" r="3" fill="#8e9297"/>
  <circle cx="22" cy="48" r="3" fill="#8e9297"/>
  <circle cx="32" cy="48" r="3" fill="#8e9297"/>
</svg>"""

EMPTY_PRED_SVG = """
<svg width="64" height="64" viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg">
  <circle cx="32" cy="32" r="22" stroke="#ED4245" stroke-width="2.5"/>
  <path d="M32 20 L36 28 L45 29 L38 36 L40 45 L32 41 L24 45 L26 36 L19 29 L28 28 Z" stroke="#ED4245" stroke-width="2" stroke-linejoin="round"/>
  <line x1="32" y1="8" x2="32" y2="4" stroke="#ED4245" stroke-width="2.5" stroke-linecap="round"/>
  <line x1="32" y1="60" x2="32" y2="56" stroke="#ED4245" stroke-width="2.5" stroke-linecap="round"/>
  <line x1="8" y1="32" x2="4" y2="32" stroke="#ED4245" stroke-width="2.5" stroke-linecap="round"/>
  <line x1="60" y1="32" x2="56" y2="32" stroke="#ED4245" stroke-width="2.5" stroke-linecap="round"/>
</svg>"""

def empty_state(icon_svg: str, title: str, subtitle: str) -> str:
    return f"""
    <div style="display:flex;flex-direction:column;align-items:center;justify-content:center;
        padding:3rem 2rem;border-radius:12px;background:#181818;border:1px dashed #2f3136;
        text-align:center;gap:1rem;">
        <div style="opacity:0.5">{icon_svg}</div>
        <div style="color:#ffffff;font-weight:700;font-size:1rem">{title}</div>
        <div style="color:#8e9297;font-size:0.85rem;max-width:320px;line-height:1.5">{subtitle}</div>
    </div>"""

def pct_bar(value, color):
    return (
        f'<div class="pct-wrap">'
        f'<div class="pct-track">'
        f'<div style="width:{value}%; background:{color}; height:100%; border-radius:3px;"></div>'
        f'</div>'
        f'<span class="pct-label" style="color:{color}">{value}%</span>'
        f'</div>'
    )

def build_stats_table(df, tipo, soglia):
    rows = ""
    is_over = (tipo == "over")
    val_col = "n_over" if is_over else "n_under"
    MEDALS = {1: "🥇", 2: "🥈", 3: "🥉"}
    ROW_CLASS = {1: "row-gold", 2: "row-silver", 3: "row-bronze"}
    ncols = 5

    for rank, (_, r) in enumerate(df.iterrows(), start=1):
        if rank == 6:
            rows += f"<tr class='sep-row'><td colspan='{ncols}'>— Altre squadre —</td></tr>"
        pct = r["pct"]
        color = ("#FFBB00" if pct >= 75 else "#FFD667" if pct >= 60 else "#FFE9AB") if is_over \
                else ("#0080FF" if pct >= 75 else "#5AAAFA" if pct >= 60 else "#9ECEFF")
        row_cls = ROW_CLASS.get(rank, "")
        rank_cel = f"<span class='rank-badge'>{MEDALS[rank]}</span>" if rank <= 3 else str(rank)
        
        rows += (
            f"<tr class='{row_cls}'>"
            f"<td class='num'>{rank_cel}</td>"
            f"<td class='hide-mob'>{r['lega']}</td>"
            f"<td><b>{r['squadra']}</b></td>"
            f"<td class='num'>{int(r[val_col])} / {int(r['partite'])}</td>"
            f"<td>{pct_bar(pct, color)}</td>"
            f"</tr>"
        )

    th_label = f"% {tipo.capitalize()} {soglia}"
    return (
        f"<div class='tbl-scroll'><table class='cal-table'>"
        f"<thead><tr>"
        f"<th class='num'>#</th>"
        f"<th class='hide-mob'>Lega</th>"
        f"<th>Squadra</th>"
        f"<th class='num'>Esiti</th>"
        f"<th>{th_label}</th>"
        f"</tr></thead>"
        f"<tbody>{rows}</tbody></table></div>"
    )

def build_calendario(df):
    rows = ""
    for _, r in df.iterrows():
        dt = r['data_ora']
        try:
            data_fmt = dt.strftime('%d/%m - %H:%M')
        except Exception:
            data_fmt = str(dt)[:16]

        rows += (
            f"<tr>"
            f"<td class='num' style='color:#5865F2; font-weight:700'>{r['giornata']}</td>"
            f"<td style='text-align: center;'><b>{r['squadra_casa']}</b></td>"
            f"<td style='text-align: center;'>-</td>"
            f"<td style='text-align: center;'><b>{r['squadra_trasferta']}</b></td>"
            f"<td style='color:#8e9297;'>{data_fmt}</td>"
            f"</tr>"
        )

    return (
        "<div class='tbl-scroll'><table class='cal-table'>"
        "<thead><tr>"
        "<th class='num'>G.</th>"
        "<th style='text-align: center;'>Casa</th>"
        "<th style='text-align: center;'>VS</th>"
        "<th style='text-align: center;'>Trasferta</th>"
        "<th>Data (UTC)</th>"
        "</tr></thead>"
        f"<tbody>{rows}</tbody></table></div>"
    )

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
            f"<td>{pct_bar(r['Prob %'], c)}</td>"
            f"</tr>"
        )
    return (
        "<div class='tbl-scroll'><table class='cal-table'>"
        "<thead><tr>"
        "<th>Match</th>"
        "<th class='num hide-mob'>xG Casa</th>"
        "<th class='num hide-mob'>xG Trasf</th>"
        "<th class='num hide-mob'>xG Tot</th>"
        "<th>Consiglio</th>"
        "<th>Affidabilità</th>"
        "</tr></thead>"
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

    header_cols = [
        (0,  "",        "Squadra",       False),
        (1,  "#1DB954", "GF Casa",       False),
        (2,  "#ED4245", "GS Casa",       False),
        (3,  "#1DB954", "Med GF Casa",   True),
        (4,  "#ED4245", "Med GS Casa",   True),
        (5,  "#5865F2", "GF Trasf",      False),
        (6,  "#FEE75C", "GS Trasf",      False),
        (7,  "#5865F2", "Med GF Trasf",  True),
        (8,  "#FEE75C", "Med GS Trasf",  True),
        (9,  "",        "Tot GF",        False),
        (10, "",        "Tot GS",        False),
    ]

    th_html = ""
    for idx, color, label, hide in header_cols:
        c_class = "hide-mob" if hide else ""
        c_style = f"color:{color}; text-align:{'left' if idx == 0 else 'center'};"
        th_html += f'<th class="{c_class}" onclick="srt({idx},{str(idx != 0).lower()})" style="{c_style}">{label}</th>\n'

    return f"""
    <div id="gol-table-container">
    <style>
      #gol-table-container {{ font-family: "Inter", "Segoe UI", sans-serif; font-size: 13px; color: #dcddde; }}
      #gol-table-container .wrap {{ width: 100%; overflow-x: auto; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.3); background: #181818; }}
      #gol-table-container table {{ width: 100%; border-collapse: collapse; white-space: nowrap; }}
      #gol-table-container thead tr {{ position: sticky; top: 0; z-index: 2; }}
      #gol-table-container th {{ background: #202225; padding: 12px 10px; border-bottom: 2px solid #2f3136; cursor: pointer; user-select: none; font-weight: 600; font-size: 12px; transition: background 0.2s; }}
      #gol-table-container th:hover {{ background: #2f3136; color: #ffffff; }}
      #gol-table-container td {{ padding: 10px 10px; border-bottom: 1px solid #282828; }}
      #gol-table-container tr:hover td {{ background: #2f3136; }}
      #gol-table-container th:not(.sort-asc):not(.sort-desc)::after {{ content: " "; font-size: 10px; opacity: 0.35; }}
      #gol-table-container .sort-asc::after  {{ content: " ▲"; font-size: 10px; }}
      #gol-table-container .sort-desc::after {{ content: " ▼"; font-size: 10px; }}
      @media screen and (max-width: 768px) {{
        #gol-table-container .hide-mob {{ display: none !important; }}
        #gol-table-container th, #gol-table-container td {{ padding: 10px 6px; font-size: 11px; }}
      }}
    </style>
    <div class="wrap">
    <table id="gol-tbl">
      <thead><tr>{th_html}</tr></thead>
      <tbody>{rows}</tbody>
    </table>
    </div>
    <script>
    (function(){{
      var d = {{}};
      window.srt = function(col, num) {{
        var tbl = document.getElementById('gol-tbl'), tbody = tbl.querySelector('tbody'),
            ths = tbl.querySelectorAll('thead th'), rows = Array.from(tbody.querySelectorAll('tr'));
        if(!tbl) return;
        d[col] = !d[col]; var asc = d[col];
        ths.forEach(function(h){{ h.classList.remove('sort-asc','sort-desc'); }});
        ths[col].classList.add(asc ? 'sort-asc' : 'sort-desc');
        rows.sort(function(a, b){{
          var va = a.cells[col] ? a.cells[col].innerText.trim() : '';
          var vb = b.cells[col] ? b.cells[col].innerText.trim() : '';
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
#  4. LOGICA PREVISIONI E MODELLO MATEMATICO
# ──────────────────────────────────────────────
def dixon_coles_correction(h, a, exp_h, exp_a, rho):
    if   h == 0 and a == 0: return max(1e-9, 1 - (exp_h * exp_a * rho))
    elif h == 0 and a == 1: return max(1e-9, 1 + (exp_h * rho))
    elif h == 1 and a == 0: return max(1e-9, 1 + (exp_a * rho))
    elif h == 1 and a == 1: return max(1e-9, 1 - rho)
    else: return 1.0

def compute_weighted_strengths(df: pd.DataFrame, alpha: float):
    df = df.copy()
    max_g = df['giornata'].max()
    df['w'] = np.exp(-alpha * (max_g - df['giornata']))

    tot_w = df['w'].sum()
    avg_home_lge = (df['gol_casa'] * df['w']).sum() / tot_w
    avg_away_lge = (df['gol_trasferta'] * df['w']).sum() / tot_w

    teams = sorted(set(df['squadra_casa']) | set(df['squadra_trasferta']))
    records = []
    
    for team in teams:
        hm = df[df['squadra_casa'] == team]
        am = df[df['squadra_trasferta'] == team]
        wh, wa = hm['w'].sum(), am['w'].sum()
        
        if wh == 0 or wa == 0:
            continue
            
        records.append({
            'squadra': team,
            'avg_gfc': (hm['gol_casa'] * hm['w']).sum() / wh,
            'avg_gsc': (hm['gol_trasferta'] * hm['w']).sum() / wh,
            'avg_gft': (am['gol_trasferta'] * am['w']).sum() / wa,
            'avg_gst': (am['gol_casa'] * am['w']).sum() / wa,
        })

    return pd.DataFrame(records).set_index('squadra'), avg_home_lge, avg_away_lge

def estimate_rho(df: pd.DataFrame, strengths: pd.DataFrame, avg_home_lge: float, avg_away_lge: float, alpha: float) -> float:
    df = df.copy()
    max_g = df['giornata'].max()
    df['w'] = np.exp(-alpha * (max_g - df['giornata']))
    low = df[(df['gol_casa'] <= 1) & (df['gol_trasferta'] <= 1)]

    if len(low) < 5:
        return -0.15

    def neg_ll(rho):
        ll = 0.0
        for _, row in low.iterrows():
            sh, sa = row['squadra_casa'], row['squadra_trasferta']
            if sh not in strengths.index or sa not in strengths.index:
                continue
            exp_h = strengths.loc[sh, 'avg_gfc'] * strengths.loc[sa, 'avg_gst'] / avg_away_lge
            exp_a = strengths.loc[sa, 'avg_gft'] * strengths.loc[sh, 'avg_gsc'] / avg_home_lge
            tau = dixon_coles_correction(int(row['gol_casa']), int(row['gol_trasferta']), exp_h, exp_a, rho)
            ll += row['w'] * np.log(max(tau, 1e-9))
        return -ll

    result = minimize_scalar(neg_ll, bounds=(-0.5, 0.1), method='bounded')
    return round(result.x, 4) if result.success else -0.15

def get_predictions_section(lega: str, soglia: float, alpha: float):
    df_raw = conn.query(query.MATCH_DATA_SQL, params={"lega": lega}, ttl=3600)

    if df_raw.empty or len(df_raw) < 10:
        st.markdown(
            empty_state(EMPTY_PRED_SVG, "Dati insufficienti", "Non ci sono abbastanza partite storiche per calcolare le previsioni."),
            unsafe_allow_html=True
        )
        return

    strengths, avg_home_lge, avg_away_lge = compute_weighted_strengths(df_raw, alpha)
    rho = estimate_rho(df_raw, strengths, avg_home_lge, avg_away_lge, alpha)

    df_n = conn.query(query.CALENDARIO_LEGA_SQL, params={"lega": lega}, ttl=3600)
    
    if df_n.empty:
        st.markdown(
            empty_state(EMPTY_CALENDAR_SVG, "Nessuna partita futura", "Non sono presenti match futuri in calendario per questa lega."),
            unsafe_allow_html=True
        )
        return

    df_n['data_ora'] = pd.to_datetime(df_n['data_ora'])
    prox = df_n.sort_values('data_ora').iloc[0]['giornata']
    matches = df_n[df_n['giornata'] == prox]

    st.write(f"#### 📅 Turno in analisi: Giornata {prox}")

    preds_data = []
    for _, m in matches.iterrows():
        h, a = m['squadra_casa'], m['squadra_trasferta']
        if h not in strengths.index or a not in strengths.index:
            continue

        exp_h = strengths.loc[h, 'avg_gfc'] * strengths.loc[a, 'avg_gst'] / avg_away_lge
        exp_a = strengths.loc[a, 'avg_gft'] * strengths.loc[h, 'avg_gsc'] / avg_home_lge

        prob_over_raw, prob_under_raw = 0.0, 0.0
        for ih in range(10):
            for ia in range(10):
                p = poisson.pmf(ih, exp_h) * poisson.pmf(ia, exp_a)
                p *= dixon_coles_correction(ih, ia, exp_h, exp_a, rho)
                if (ih + ia) > soglia:
                    prob_over_raw += p
                else:
                    prob_under_raw += p

        tot = prob_over_raw + prob_under_raw
        if tot == 0: continue
        
        prob_o = round((prob_over_raw / tot) * 100, 1)
        prob_u = round((prob_under_raw / tot) * 100, 1)

        if prob_o > prob_u:
            label, prob = f"🔥 Over {soglia}", prob_o
            color = "#FFBB00" if prob_o >= 85 else "#FFD667" if prob_o >= 65 else "#FFE9AB"
        else:
            label, prob = f"❄️ Under {soglia}", prob_u
            color = "#0080FF" if prob_u >= 85 else "#5AAAFA" if prob_u >= 65 else "#9ECEFF"

        preds_data.append({
            "Partita": f"{h} vs {a}",
            "Gol Attesi Casa": round(exp_h, 2),
            "Gol Attesi Trasferta": round(exp_a, 2),
            "Gol Attesi Totali": round(exp_h + exp_a, 2),
            "Esito": label,
            "Prob %": prob,
            "Colore": color,
        })

    if preds_data:
        st.markdown(build_prediction_table(pd.DataFrame(preds_data)), unsafe_allow_html=True)
    else:
        st.markdown(
            empty_state(EMPTY_PRED_SVG, "Previsioni non disponibili", "Alcune squadre del prossimo turno non hanno dati storici sufficienti."),
            unsafe_allow_html=True
        )


# ──────────────────────────────────────────────
#  5. LAYOUT E INTERFACCIA PRINCIPALE
# ──────────────────────────────────────────────
st.markdown('<div class="main-title">XG Football Analytics</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Advanced Data & Predictions System</div>', unsafe_allow_html=True)

leghe_disp = query_leghe()

# --- SEZIONE 1: STATISTICHE GLOBALI ---
st.markdown('<div id="statistiche" class="section-title">📊 Top Statistiche Globali</div>', unsafe_allow_html=True)
soglia_stats = _soglia_widget("Seleziona Soglia Gol:", "stats_soglia")

c1, c2 = st.columns(2, gap="large")
with c1:
    with st.spinner("Caricamento Over..."):
        df_ov = conn.query(query.TOP_OVER_SQL, params={"soglia": soglia_stats, "limit": 20}, ttl=3600)
    st.markdown(build_stats_table(df_ov, "over", soglia_stats), unsafe_allow_html=True)
    
with c2:
    with st.spinner("Caricamento Under..."):
        df_un = conn.query(query.TOP_UNDER_SQL, params={"soglia": soglia_stats, "limit": 20}, ttl=3600)
    st.markdown(build_stats_table(df_un, "under", soglia_stats), unsafe_allow_html=True)

st.markdown('<hr class="divider">', unsafe_allow_html=True)

# --- SEZIONE 2: CLASSIFICA GOL ---
st.markdown('<div id="reti" class="section-title-blue">🎯 Performance Reti e Classifica xG</div>', unsafe_allow_html=True)
lega_sel = st.selectbox("Seleziona Lega per visualizzare il dettaglio:", options=leghe_disp, key="gol_lega")

with st.spinner(f"Caricamento dati {lega_sel}..."):
    df_gol = conn.query(query.GOL_LEGA_SQL, params={"lega": lega_sel}, ttl=3600)

st.html(build_gol_table(df_gol))
st.markdown('<hr class="divider">', unsafe_allow_html=True)

# --- SEZIONE 3: CALENDARIO PROSSIMO TURNO ---
st.markdown('<div id="calendario" class="section-title-blue">📅 Calendario Prossimo Turno</div>', unsafe_allow_html=True)
lega_cal = st.selectbox("Seleziona Lega:", options=leghe_disp, key="cal_box")

with st.spinner(f"Caricamento calendario {lega_cal}..."):
    df_next = conn.query(query.CALENDARIO_LEGA_SQL, params={"lega": lega_cal}, ttl=3600)

if not df_next.empty:
    df_next['data_ora'] = pd.to_datetime(df_next['data_ora'])
    prossima_g_cal = df_next.sort_values('data_ora').iloc[0]['giornata']
    st.write(f"#### Giornata {prossima_g_cal}")
    st.markdown(build_calendario(df_next[df_next['giornata'] == prossima_g_cal]), unsafe_allow_html=True)
else:
    st.markdown(
        empty_state(EMPTY_CALENDAR_SVG, "Nessuna partita in programma", 
                    f"Il calendario per {lega_cal} non contiene partite future. Riprova dopo l'aggiornamento del database."),
        unsafe_allow_html=True
    )

st.markdown('<hr class="divider">', unsafe_allow_html=True)

# --- SEZIONE 4: PREVISIONI ALGORITMICHE ---
st.markdown('<div id="previsioni" class="section-title-red">🔮 Previsioni Algoritmiche</div>', unsafe_allow_html=True)

c_p1, c_p2, c_p3 = st.columns([2, 1, 1])
with c_p1:
    lega_pred = st.selectbox("Analizza Lega:", options=leghe_disp, key="pred_box")
with c_p2:
    soglia_pred = _soglia_widget("Soglia Previsione:", "pred_soglia")
with c_p3:
    forma_recente = st.toggle(
        "Forma Recente",
        value=True,
        key="forma_recente",
        help="Attivo: le ultime partite pesano di più nel calcolo. Disattivo: tutta la stagione vale uguale."
    )
    alpha = 0.10 if forma_recente else 0.0

with st.spinner(f"Calcolo previsioni {lega_pred}..."):
    get_predictions_section(lega_pred, soglia_pred, alpha)

# --- FOOTER ---
st.markdown(
    "<div style='text-align:center; color:#8e9297; font-size:0.8rem; margin-top:3rem; margin-bottom:2rem;'>"
    "Play Responsibly • Algorithm relies purely on historical mathematical models."
    "</div>",
    unsafe_allow_html=True
)