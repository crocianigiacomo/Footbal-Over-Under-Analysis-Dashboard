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
    var params = new URLSearchParams(window.parent.location.search);
    if (!params.get('sw')) {
        params.set('sw', window.innerWidth);
        window.parent.history.replaceState({}, '', '?' + params.toString());
        window.parent.location.reload();
    }
</script>
""", height=0)

screen_w = int(st.query_params.get("sw", 1200))
is_mobile = screen_w < 768

st.markdown("""
<style>
    [data-testid="stVerticalBlock"] > div { gap: 0.5rem !important; }

    .block-container {
        padding-top: 2rem !important;
        padding-bottom: 2rem !important;
    }

    /* ── TITOLI ── */
    .main-title {
        font-size: 2.5rem; font-weight: 800;
        color: #ffffff; letter-spacing: -0.5px;
        margin-top: 1rem; margin-bottom: 0.2rem; text-align: center;
        font-family: 'Inter', 'Segoe UI', sans-serif;
    }
    .sub-title {
        font-size: 1.1rem; color: #b3b3b3; margin-bottom: 2.5rem;
        font-weight: 500; text-align: center;
        font-family: 'Inter', 'Segoe UI', sans-serif;
    }

    /* ── SECTION TITLES ── */
    .section-title {
        font-size: 1.1rem; font-weight: 700; color: #ffffff;
        background: #181818; border-left: 4px solid #1DB954;
        padding: 0.6rem 1rem; border-radius: 6px; margin-bottom: 1rem;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        scroll-margin-top: 20px; /* offset drawer */
    }
    .section-title-red {
        font-size: 1.1rem; font-weight: 700; color: #ffffff;
        background: #181818; border-left: 4px solid #ED4245;
        padding: 0.6rem 1rem; border-radius: 6px; margin-bottom: 1rem;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        scroll-margin-top: 20px;
    }
    .section-title-blue {
        font-size: 1.1rem; font-weight: 700; color: #ffffff;
        background: #181818; border-left: 4px solid #5865F2;
        padding: 0.6rem 1rem; border-radius: 6px; margin-bottom: 1rem;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        scroll-margin-top: 20px;
    }

    /* ── FAB + DRAWER  ── */
    #mob-fab, #mob-overlay, #mob-drawer { 
        display: none !important; 
    }

    @media screen and (max-width: 768px) {
        #mob-fab {
            display: flex !important; align-items: center; justify-content: center;
            position: fixed; bottom: 90px; right: 20px; z-index: 999999;
            width: 52px; height: 52px; border-radius: 50%;
            background: #5865F2;
            box-shadow: 0 4px 16px rgba(88,101,242,0.55);
            font-size: 22px; cursor: pointer;
            transition: transform 0.2s, box-shadow 0.2s;
            user-select: none;
        }
        #mob-fab:active { transform: scale(0.92); }

        #mob-overlay {
            display: none; position: fixed; inset: 0; z-index: 999998;
            background: rgba(0,0,0,0.55); backdrop-filter: blur(2px);
        }
        #mob-overlay.open { display: block !important; }

        #mob-drawer {
            position: fixed; top: 0; right: -290px; z-index: 999999;
            width: 275px; height: 100dvh;
            background: #181818; border-left: 1px solid #2f3136;
            box-shadow: -8px 0 32px rgba(0,0,0,0.5);
            transition: right 0.28s cubic-bezier(0.4,0,0.2,1);
            display: flex !important; flex-direction: column; overflow: hidden;
        }
        #mob-drawer.open { right: 0 !important; }

        .drawer-header {
            display: flex; align-items: center; justify-content: space-between;
            padding: 22px 16px 16px;
            border-bottom: 1px solid #2f3136;
        }
        .drawer-header span {
            font-size: 11px; font-weight: 700; color: #8e9297;
            letter-spacing: 0.1em; text-transform: uppercase;
        }
        .drawer-close {
            width: 32px; height: 32px; border-radius: 50%;
            background: #2f3136; border: none; color: #b3b3b3;
            font-size: 16px; cursor: pointer;
            display: flex; align-items: center; justify-content: center;
        }
        .drawer-close:active { background: #404249; }

        .drawer-nav { display: flex; flex-direction: column; padding: 14px 12px; gap: 8px; }
        .drawer-nav a {
            display: flex; align-items: center; gap: 12px;
            padding: 14px 16px; border-radius: 10px;
            background: #202225; text-decoration: none;
            color: #dcddde; font-size: 15px; font-weight: 600;
            border: 1px solid #2f3136; min-height: 52px;
            transition: background 0.15s, border-color 0.15s;
        }
        .drawer-nav a .nav-icon { font-size: 20px; line-height: 1; }
        .drawer-nav a .nav-dot {
            width: 8px; height: 8px; border-radius: 50%;
            margin-left: auto; flex-shrink: 0;
        }
        .drawer-nav a:active { background: #2f3136; border-color: #5865F2; }
    }

    /* ── DIVIDER ── */
    .divider { border: none; border-top: 1px solid #282828; margin: 1rem 0; }

    /* ── TABELLE GENERICHE ── */
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
    .tbl-scroll { border-radius: 8px; overflow-x: auto; box-shadow: 0 4px 10px rgba(0,0,0,0.2); }

    /* ── PCT BAR ── */
    .pct-wrap { display: flex; align-items: center; gap: 6px; min-width: 0; }
    /* FIX: flex-shrink:0 + width clampato evita overflow su schermi < 360px */
    .pct-track {
        width: clamp(36px, 10vw, 80px);
        background: #282828; height: 6px; border-radius: 3px; flex-shrink: 0;
    }
    .pct-label { font-weight: 600; font-size: 0.75rem; white-space: nowrap; }

    /* ── MOBILE OVERRIDES ── */
    @media screen and (max-width: 768px) {
        /* Navbar occupa spazio: abbassa il contenuto principale */
        .block-container { padding-top: 0.5rem !important; }

        .hide-mob { display: none !important; }

        /* FIX: 13px minimo — leggibile su qualsiasi schermo reale */
        .cal-table td, .cal-table th {
            padding: 8px 5px !important;
            font-size: 13px !important;
        }

        /* Titoli più compatti su mobile */
        .main-title { font-size: 1.7rem !important; }
        .sub-title  { font-size: 0.95rem !important; margin-bottom: 1rem !important; }

        /* Touch target minimo 44px per selectbox */
        div[data-baseweb="select"] > div { min-height: 44px !important; }

        /* Segmented control: bottoni più alti e leggibili */
        [data-testid="stSegmentedControl"] button {
            min-height: 44px !important;
            font-size: 14px !important;
            padding: 0 18px !important;
        }
    }

    footer, #MainMenu { visibility: hidden; }

    div[data-baseweb="select"], div[data-baseweb="select"] * { cursor: pointer !important; }
    div[data-baseweb="select"]:hover { border-color: #5865F2 !important; transition: border-color 0.3s ease; }
</style>
""", unsafe_allow_html=True)


# ──────────────────────────────────────────────
#  CONNESSIONE DB E DATI (con cache TTL)
# ──────────────────────────────────────────────
conn = st.connection("calcio_db", type="sql", url="sqlite:///calcio.db")


def query_leghe():
    """Lista leghe disponibili — cached 1 ora."""
    return conn.query(query.LISTA_LEGHE_SQL, ttl=3600)["lega"].tolist()


# ──────────────────────────────────────────────
#  HELPERS SOGLIA: evita deselect di segmented_control
# ──────────────────────────────────────────────
def _soglia_widget(label: str, key: str) -> float:
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
#  HELPERS HTML (GENERATORI TABELLE)
# ──────────────────────────────────────────────
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
    is_over = tipo == "over"
    val_col = "n_over" if is_over else "n_under"

    for rank, (_, r) in enumerate(df.iterrows(), start=1):
        pct = r["pct"]
        if is_over:
            color = "#FFBB00" if pct >= 75 else "#FFD667" if pct >= 60 else "#FFE9AB"
        else:
            color = "#0080FF" if pct >= 75 else "#5AAAFA" if pct >= 60 else "#9ECEFF"

        rows += (
            f"<tr>"
            f"<td class='num hide-mob'>{rank}</td>"
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
        f"<th class='num hide-mob'>#</th>"
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
    var tbl = document.getElementById('t'), tbody = tbl.querySelector('tbody'),
        ths = tbl.querySelectorAll('thead th'), rows = Array.from(tbody.querySelectorAll('tr'));
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
</body>
</html>"""


# ──────────────────────────────────────────────
#  LOGICA PREVISIONI E POISSON
# ──────────────────────────────────────────────
def dixon_coles_correction(h, a, exp_h, exp_a, rho=-0.15):
    
    if   h == 0 and a == 0: return 1 - (exp_h * exp_a * rho)
    elif h == 0 and a == 1: return 1 + (exp_h * rho)
    elif h == 1 and a == 0: return 1 + (exp_a * rho)
    elif h == 1 and a == 1: return 1 - rho
    else: return 1.0


def get_predictions_section(lega, soglia):
    df_s = conn.query(query.TEAM_STRENGTH_SQL, params={"lega": lega}, ttl=3600)
    if df_s.empty:
        st.warning("Dati storici insufficienti per questa lega.")
        return

    df_s.set_index('squadra', inplace=True)

    df_n = conn.query(query.CALENDARIO_LEGA_SQL, params={"lega": lega}, ttl=3600)
    if df_n.empty:
        st.info("Nessun match futuro trovato in calendario.")
        return

    df_n['data_ora'] = pd.to_datetime(df_n['data_ora'])
    prox   = df_n.sort_values('data_ora').iloc[0]['giornata']
    matches = df_n[df_n['giornata'] == prox]

    st.write(f"#### 📅 Turno in analisi: Giornata {prox}")

    preds_data = []
    for _, m in matches.iterrows():
        h, a = m['squadra_casa'], m['squadra_trasferta']
        if h not in df_s.index or a not in df_s.index:
            continue

        exp_h = (df_s.loc[h, 'avg_gfc'] * df_s.loc[a, 'avg_gst']) / df_s.loc[h, 'avg_away_league']
        exp_a = (df_s.loc[a, 'avg_gft'] * df_s.loc[h, 'avg_gsc']) / df_s.loc[h, 'avg_home_league']

        prob_over_raw  = 0.0
        prob_under_raw = 0.0

        for ih in range(10):
            for ia in range(10):
                p_base      = poisson.pmf(ih, exp_h) * poisson.pmf(ia, exp_a)
                p_corrected = p_base * dixon_coles_correction(ih, ia, exp_h, exp_a)

                if (ih + ia) > soglia:
                    prob_over_raw  += p_corrected
                else:
                    prob_under_raw += p_corrected

        # Normalizzazione
        tot_prob = prob_over_raw + prob_under_raw
        if tot_prob == 0:
            continue
        prob_o = round((prob_over_raw  / tot_prob) * 100, 1)
        prob_u = round((prob_under_raw / tot_prob) * 100, 1)

        if prob_o > prob_u:
            label, prob = f"🔥 Over {soglia}", prob_o
            match prob_o:
                case p if p >= 85: color = "#FFBB00"
                case p if p >= 65: color = "#FFD667"
                case _:            color = "#FFE9AB"
        else:
            label, prob = f"❄️ Under {soglia}", prob_u
            match prob_u:
                case p if p >= 85: color = "#0080FF"
                case p if p >= 65: color = "#5AAAFA"
                case _:            color = "#9ECEFF"

        preds_data.append({
            "Partita":              f"{h} vs {a}",
            "Gol Attesi Casa":      round(exp_h, 2),
            "Gol Attesi Trasferta": round(exp_a, 2),
            "Gol Attesi Totali":    round(exp_h + exp_a, 2),
            "Esito":                label,
            "Prob %":               prob,
            "Colore":               color,
        })

    if preds_data:
        st.markdown(build_prediction_table(pd.DataFrame(preds_data)), unsafe_allow_html=True)


# ──────────────────────────────────────────────
#  LAYOUT INTERFACCIA PRINCIPALE
# ──────────────────────────────────────────────
st.markdown('<div class="main-title">XG Football Analytics</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Advanced Data & Predictions System</div>', unsafe_allow_html=True)

# FAB + drawer 
st.markdown("""
<div id="mob-fab">☰</div>

<div id="mob-overlay"></div>

<div id="mob-drawer">
  <div class="drawer-header">
    <span>Navigazione</span>
    <button class="drawer-close">✕</button>
  </div>
  <nav class="drawer-nav">
    <a data-target="statistiche">
      <span class="nav-icon">📊</span> Top Statistiche
      <span class="nav-dot" style="background:#1DB954"></span>
    </a>
    <a data-target="reti">
      <span class="nav-icon">🎯</span> Performance Reti
      <span class="nav-dot" style="background:#5865F2"></span>
    </a>
    <a data-target="calendario">
      <span class="nav-icon">📅</span> Calendario
      <span class="nav-dot" style="background:#5865F2"></span>
    </a>
    <a data-target="previsioni">
      <span class="nav-icon">🔮</span> Previsioni
      <span class="nav-dot" style="background:#ED4245"></span>
    </a>
  </nav>
</div>
""", unsafe_allow_html=True)

# Iniezione sicura del Javascript nel DOM di Streamlit
components.html("""
<script>
    const doc = window.parent.document;
    const fab = doc.getElementById('mob-fab');
    const overlay = doc.getElementById('mob-overlay');
    const drawer = doc.getElementById('mob-drawer');

    if (fab && overlay && drawer) {
        // Apri il drawer e nascondi il bottone per estetica
        fab.onclick = function() {
            drawer.classList.add('open');
            overlay.classList.add('open');
            fab.style.display = 'none'; 
        };

        // Logica per chiudere il drawer
        const closeDrawer = function() {
            drawer.classList.remove('open');
            overlay.classList.remove('open');
            fab.style.display = 'flex'; 
        };

        overlay.onclick = closeDrawer;
        
        const closeBtn = doc.querySelector('.drawer-close');
        if (closeBtn) closeBtn.onclick = closeDrawer;

        // Navigazione fluida
        const links = doc.querySelectorAll('.drawer-nav a');
        links.forEach(link => {
            link.onclick = function(e) {
                e.preventDefault();
                closeDrawer();
                const targetId = this.getAttribute('data-target');
                setTimeout(() => {
                    const targetEl = doc.getElementById(targetId);
                    if (targetEl) targetEl.scrollIntoView({ behavior: 'smooth', block: 'start' });
                }, 250); // Piccolo delay per far chiudere il drawer prima dello scroll
            };
        });
    }
</script>
""", height=0)

leghe_disp = query_leghe()

# --- SEZIONE 1: STATISTICHE GLOBALI ---
st.markdown('<div id="statistiche" class="section-title">📊 Top Statistiche Globali</div>', unsafe_allow_html=True)
soglia_stats = _soglia_widget("Seleziona Soglia Gol:", "stats_soglia")

c1, c2 = st.columns(2, gap="large")
with c1:
    df_ov = conn.query(query.TOP_OVER_SQL,  params={"soglia": soglia_stats, "limit": 20}, ttl=3600)
    st.markdown(build_stats_table(df_ov, "over",  soglia_stats), unsafe_allow_html=True)
with c2:
    df_un = conn.query(query.TOP_UNDER_SQL, params={"soglia": soglia_stats, "limit": 20}, ttl=3600)
    st.markdown(build_stats_table(df_un, "under", soglia_stats), unsafe_allow_html=True)

st.markdown('<hr class="divider">', unsafe_allow_html=True)


# --- SEZIONE 2: CLASSIFICA GOL ---
st.markdown('<div id="reti" class="section-title-blue">🎯 Performance Reti e Classifica xG</div>', unsafe_allow_html=True)
lega_sel = st.selectbox("Seleziona Lega per visualizzare il dettaglio:", options=leghe_disp, key="gol_lega")
df_gol   = conn.query(query.GOL_LEGA_SQL, params={"lega": lega_sel}, ttl=3600)

multiplier = 42 if is_mobile else 38   
h_iframe   = 42 + len(df_gol) * multiplier  
components.html(build_gol_table(df_gol), height=h_iframe, scrolling=False)

st.markdown('<hr class="divider">', unsafe_allow_html=True)


# --- SEZIONE 3: CALENDARIO PROSSIMO TURNO ---
st.markdown('<div id="calendario" class="section-title-blue">📅 Calendario Prossimo Turno</div>', unsafe_allow_html=True)
lega_cal = st.selectbox("Seleziona Lega:", options=leghe_disp, key="cal_box")
df_next  = conn.query(query.CALENDARIO_LEGA_SQL, params={"lega": lega_cal}, ttl=3600)

if not df_next.empty:
    df_next['data_ora'] = pd.to_datetime(df_next['data_ora'])
    prossima_g_cal = df_next.sort_values('data_ora').iloc[0]['giornata']
    st.write(f"#### Giornata {prossima_g_cal}")
    st.markdown(
        build_calendario(df_next[df_next['giornata'] == prossima_g_cal]),
        unsafe_allow_html=True
    )
else:
    st.info("Nessuna partita futura in programma per questa lega.")

st.markdown('<hr class="divider">', unsafe_allow_html=True)


# --- SEZIONE 4: PREVISIONI ALGORITMICHE (Poisson + Dixon-Coles) ---
st.markdown('<div id="previsioni" class="section-title-red">🔮 Previsioni Algoritmiche</div>', unsafe_allow_html=True)

c_p1, c_p2 = st.columns([2, 1])
with c_p1:
    lega_pred = st.selectbox("Analizza Lega:", options=leghe_disp, key="pred_box")
with c_p2:
    soglia_pred = _soglia_widget("Soglia Previsione:", "pred_soglia")

get_predictions_section(lega_pred, soglia_pred)

# --- FOOTER ---
st.markdown(
    "<div style='text-align:center; color:#8e9297; font-size:0.8rem; margin-top:3rem; margin-bottom:2rem;'>"
    "Play Responsibly • Algorithm relies purely on historical mathematical models."
    "</div>",
    unsafe_allow_html=True
)