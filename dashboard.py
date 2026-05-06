import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import query  # Il tuo nuovo file con le stringhe SQL

# ──────────────────────────────────────────────
#  CONFIG PAGINA
# ──────────────────────────────────────────────
st.set_page_config(
    page_title="Interactive Football Dashboard",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ──────────────────────────────────────────────
#  RILEVA LARGHEZZA SCHERMO
# ──────────────────────────────────────────────
components.html("""
<script>
(function(){
  var w = window.innerWidth;
  var params = new URLSearchParams(window.parent.location.search);
  if (!params.get('sw') || Math.abs(parseInt(params.get('sw')) - w) > 50) {
    params.set('sw', w);
    window.parent.history.replaceState({}, '', '?' + params.toString());
    window.parent.location.reload();
  }
})();
</script>
""", height=0)

try:
    screen_w = int(st.query_params.get("sw", 1200))
except Exception:
    screen_w = 1200

is_mobile = screen_w < 768

# ──────────────────────────────────────────────
#  CSS PAGINA PRINCIPALE
# ──────────────────────────────────────────────
st.markdown("""
<style>
    .main-title {
        font-size: 3rem; font-weight: 800;
        color: #5AB2FA; letter-spacing: 1px; margin-bottom: 0.2rem; text-align: center;
            font-family: 'Copperplate'; 
    }
    .sub-title {
        font-size: 1.25rem; color: #8b92a5; margin-bottom: 1.5rem;font-family: 'Copperplate'; text-align: center;
    }
    .section-title {
        font-size: 1.05rem; font-weight: 700; color: #ffffff;
        background: linear-gradient(90deg, #00d4aa22, transparent);
        border-left: 3px solid #00d4aa;
        padding: 0.4rem 0.8rem; border-radius: 0 6px 6px 0; margin-bottom: 0.8rem;
    }
    .section-title-red {
        font-size: 1.05rem; font-weight: 700; color: #ffffff;
        background: linear-gradient(90deg, #ff6b6b22, transparent);
        border-left: 3px solid #ff6b6b;
        padding: 0.4rem 0.8rem; border-radius: 0 6px 6px 0; margin-bottom: 0.8rem;
    }
    .section-title-blue {
        font-size: 1.05rem; font-weight: 700; color: #ffffff;
        background: linear-gradient(90deg, #4fc3f722, transparent);
        border-left: 3px solid #4fc3f7;
        padding: 0.4rem 0.8rem; border-radius: 0 6px 6px 0; margin-bottom: 0.8rem;
    }
    .divider { border: none; border-top: 1px solid #2d3348; margin: 1.5rem 0; }

    /* Tabelle Over/Under */
    .cal-table {
        width: 100%; border-collapse: collapse;
        font-size: 0.82rem; color: #e8eaf0;
    }
    .cal-table th {
        background: #252b3b; color: #8b92a5;
        padding: 7px 10px; text-align: left;
        border-bottom: 1px solid #2d3348; white-space: nowrap;
    }
    .cal-table td {
        padding: 6px 10px; border-bottom: 1px solid #1e2333;
        white-space: nowrap;
    }
    .cal-table tr:hover td { background: #1e2435; }
    .cal-table .num { text-align: center; }
    .pct-wrap { display: flex; align-items: center; gap: 6px; }
    .pct-bar  { height: 6px; border-radius: 3px; flex-shrink: 0; }
    .pct-val  { font-weight: 600; font-size: 0.8rem; }
    .tbl-scroll { border-radius: 8px; overflow-x: auto; }

    footer {visibility: hidden;}
    #MainMenu {visibility: hidden;}
    div[data-baseweb="select"], div[data-baseweb="select"] * {
        cursor: pointer !important;
    }
    div[data-baseweb="select"]:hover {
        border-color: #00d4aa !important;
        transition: border-color 0.3s ease;
    }        
</style>
""", unsafe_allow_html=True)


# ──────────────────────────────────────────────
#  CONNESSIONE DB (MODERNA)
# ──────────────────────────────────────────────
conn = st.connection("calcio_db", type="sql", url="sqlite:///calcio.db")

def query_top_over(limit=20):
    return conn.query(query.TOP_OVER_SQL, ttl=300, params={"limit": limit})

def query_top_under(limit=20):
    return conn.query(query.TOP_UNDER_SQL, ttl=300, params={"limit": limit})

def query_leghe():
    df = conn.query(query.LISTA_LEGHE_SQL, ttl=300)
    return df["lega"].tolist()

def query_gol_lega(lega):
    return conn.query(query.GOL_LEGA_SQL, ttl=300, params={"lega": lega})


# ──────────────────────────────────────────────
#  HELPERS HTML
# ──────────────────────────────────────────────
def pct_bar(value, color):
    w = int(min(value, 100))
    return (
        f'<div class="pct-wrap">'
        f'<div class="pct-bar" style="width:{w}px;background:{color}"></div>'
        f'<span class="pct-val" style="color:{color}">{value}%</span>'
        f'</div>'
    )

def build_over_table(df):
    rows = ""
    for i, r in df.iterrows():
        pct   = r["pct"]
        color = "#00d4aa" if pct >= 70 else "#f0a500" if pct >= 55 else "#9e9e9e"
        bar   = pct_bar(pct, color)
        rows += (
            f"<tr>"
            f"<td>{r['lega']}</td>"
            f"<td><b>{r['squadra']}</b></td>"
            f"<td>{bar}</td>"
            f"</tr>"
        )
    return (
        "<div class='tbl-scroll'>"
        "<table class='cal-table'>"
        "<thead><tr>"
        "<th>Lega</th><th>Squadra</th>"
        "<th>% Over</th>"
        "</tr></thead>"
        f"<tbody>{rows}</tbody>"
        "</table></div>"
    )

def build_under_table(df):
    rows = ""
    for i, r in df.iterrows():
        pct   = r["pct"]
        color = "#ff6b6b" if pct >= 70 else "#ffa726" if pct >= 55 else "#9e9e9e"
        bar   = pct_bar(pct, color)
        rows += (
            f"<tr>" 
            f"<td>{r['lega']}</td>"
            f"<td><b>{r['squadra']}</b></td>"
            f"<td>{bar}</td>"
            f"</tr>"
        )
    return (
        "<div class='tbl-scroll'>"
        "<table class='cal-table'>"
        "<thead><tr>"
        "<th>Lega</th><th>Squadra</th>"
        "<th>% Under</th>"
        "</tr></thead>"
        f"<tbody>{rows}</tbody>"
        "</table></div>"
    )

def build_calendario(df):
    """Genera la tabella HTML per le prossime partite con stili coerenti."""
    rows = ""
    for _, r in df.iterrows():
        # Formattazione data: da '2024-05-15T18:00:00Z' a '15/05 18:00'
        try:
            from datetime import datetime
            dt = datetime.strptime(r['data_ora'], '%Y-%m-%dT%H:%M:%SZ')
            data_formattata = dt.strftime('%d/%m %H:%M')
        except:
            data_formattata = r['data_ora'] # Fallback in caso di errore

        rows += (
            f"<tr>"
            f"<td class='num' style='color:#4fc3f7; font-weight:700'>{r['giornata']}</td>"
            f"<td><b>{r['squadra_casa']}</b></td>"
            f"<td><b>{r['squadra_trasferta']}</b></td>"
            f"<td style='color:#8b92a5; font-size:1rem'>{data_formattata}</td>"
            f"</tr>"
        )
        
    return (
        "<div class='tbl-scroll'>"
        "<table class='cal-table'>"
        "<thead><tr>"
        "<th class='num'>Giornata</th><th>Casa</th><th>Trasferta</th><th>Data (UTC)</th>"
        "</tr></thead>"
        f"<tbody>{rows}</tbody>"
        "</table></div>"
    )

def build_gol_table(df, mobile=False):
    rows = ""
    for _, r in df.iterrows():
        rows += (
            f"<tr>"
            f"<td><b>{r['squadra']}</b></td>"
            f"<td class='num c-gfc'  style='color:#00d4aa'>{int(r['gfc'])}</td>"
            f"<td class='num c-gsc'  style='color:#ff6b6b'>{int(r['gsc'])}</td>"
            f"<td class='num c-mgfc hide-mob' style='color:#00d4aa'>{round(float(r['mgfc']), 2)}</td>"
            f"<td class='num c-mgsc hide-mob' style='color:#ff6b6b'>{round(float(r['mgsc']), 2)}</td>"
            f"<td class='num c-gft'  style='color:#4fc3f7'>{int(r['gft'])}</td>"
            f"<td class='num c-gst'  style='color:#ffa726'>{int(r['gst'])}</td>"
            f"<td class='num c-mgft hide-mob' style='color:#4fc3f7'>{round(float(r['mgft']), 2)}</td>"
            f"<td class='num c-mgst hide-mob' style='color:#ffa726'>{round(float(r['mgst']), 2)}</td>"
            f"<td class='num c-totgf'><b>{int(r['totgf'])}</b></td>"
            f"<td class='num c-totgs'><b>{int(r['totgs'])}</b></td>"
            f"</tr>"
        )

    if mobile:
        header_cols = [
            ("srt(0,false)", "",            "Squadra"),
            ("srt(1,true)",  "#00d4aa",     "Gol Fatti Casa"),
            ("srt(2,true)",  "#ff6b6b",     "Gol Subiti Casa"),
            ("srt(3,true)",  "#4fc3f7",     "Gol Fatti Trasf"),
            ("srt(4,true)",  "#ffa726",     "Gol Subiti Trasf"),
            ("srt(5,true)",  "",            "Totale Gol Fatti"),
            ("srt(6,true)",  "",            "Totale Gol Subiti"),
        ]
    else:
        header_cols = [
            ("srt(0,false)", "",            "Squadra"),
            ("srt(1,true)",  "#00d4aa",     "Gol Fatti Casa"),
            ("srt(2,true)",  "#ff6b6b",     "Gol Subiti Casa"),
            ("srt(3,true)",  "#00d4aa",     "Media Gol Fatti Casa"),
            ("srt(4,true)",  "#ff6b6b",     "Media Gol Subiti Casa"),
            ("srt(5,true)",  "#4fc3f7",     "Gol Fatti Trasferta"),
            ("srt(6,true)",  "#ffa726",     "Gol Subiti Trasferta"),
            ("srt(7,true)",  "#4fc3f7",     "Media Gol Fatti Trasferta"),
            ("srt(8,true)",  "#ffa726",     "Media Gol Subiti Trasferta"),
            ("srt(9,true)",  "",            "Totale Gol Fatti"),
            ("srt(10,true)", "",            "Totale Gol Subiti"),
        ]

    th_html = ""
    for fn, color, label in header_cols:
        col_style = f"color:{color};" if color else ""
        th_html += f'<th class="num" onclick="{fn}" style="{col_style}">{label}</th>\n'

    hide_mob_css = ".hide-mob { display: none; }" if mobile else ""

    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    background: #0e1117;
    font-family: "Source Sans Pro", "Segoe UI", Arial, sans-serif;
    font-size: {"12px" if mobile else "13px"};
    color: #e8eaf0;
  }}
  .wrap {{
    width: 100%;
    overflow-x: auto;
    border-radius: 8px;
  }}
  table {{
    width: 100%;
    border-collapse: collapse;
    white-space: nowrap;
  }}
  thead tr {{ position: sticky; top: 0; z-index: 2; }}
  th {{
    background: #252b3b;
    color: #8b92a5;
    padding: {"7px 8px" if mobile else "9px 12px"};
    text-align: right;
    border-bottom: 2px solid #2d3348;
    cursor: pointer;
    user-select: none;
    font-weight: 600;
    font-size: {"11px" if mobile else "12px"};
  }}
  th:first-child {{ text-align: left; }}
  th:hover {{ background: #2e3550; color: #ffffff; }}
  td {{ padding: {"6px 8px" if mobile else "7px 12px"}; border-bottom: 1px solid #1e2333; text-align: right; }}
  td:first-child {{ text-align: left; }}
  tr:hover td {{ background: #1e2435; }}
  th:not(.sort-asc):not(.sort-desc)::after {{ content: " "; font-size: 10px; opacity: 0.35; }}
  .sort-asc::after  {{ content: " "; font-size: 10px; }}
  .sort-desc::after {{ content: " "; font-size: 10px; }}
  {hide_mob_css}
</style>
</head>
<body>
<div class="wrap">
<table id="t">
  <thead><tr>
    {th_html}
  </tr></thead>
  <tbody>{rows}</tbody>
</table>
</div>
<script>
(function(){{
  var d = {{}};
  window.srt = function(col, num) {{
    var tbl   = document.getElementById('t');
    var tbody = tbl.querySelector('tbody');
    var ths   = tbl.querySelectorAll('thead th');
    var rows  = Array.from(tbody.querySelectorAll('tr'));
    d[col] = !d[col];
    var asc = d[col];
    ths.forEach(function(h){{ h.classList.remove('sort-asc','sort-desc'); }});
    ths[col].classList.add(asc ? 'sort-asc' : 'sort-desc');
    rows.sort(function(a, b){{
      var cells_a = Array.from(a.querySelectorAll('td')).filter(function(c){{ return !c.classList.contains('hide-mob'); }});
      var cells_b = Array.from(b.querySelectorAll('td')).filter(function(c){{ return !c.classList.contains('hide-mob'); }});
      var va = cells_a[col] ? cells_a[col].innerText.trim() : '';
      var vb = cells_b[col] ? cells_b[col].innerText.trim() : '';
      if (num){{ va = parseFloat(va)||0; vb = parseFloat(vb)||0; }}
      return asc ? (va<vb?-1:va>vb?1:0) : (va>vb?-1:va<vb?1:0);
    }});
    rows.forEach(function(r){{ tbody.appendChild(r); }});
  }};
}})();
</script>
</body>
</html>"""


# ──────────────────────────────────────────────
#  LOGICA UI (Design Mobile/Desktop)
# ──────────────────────────────────────────────
st.markdown('<div class="main-title">⚽ Interactive Football Dashboard ⚽</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Analisi Over / Under · Gol per squadra e per lega</div>', unsafe_allow_html=True)
st.markdown('<hr class="divider">', unsafe_allow_html=True)

if is_mobile:
    st.markdown('<div class="section-title">🟢 Top 20 Squadre · Over 2.5</div>', unsafe_allow_html=True)
    st.markdown(build_over_table(query_top_over(20)), unsafe_allow_html=True)
    st.markdown("<div style='margin-top:1.5rem'></div>", unsafe_allow_html=True)
    st.markdown('<div class="section-title-red">🔴 Top 20 Squadre · Under 3.5</div>', unsafe_allow_html=True)
    st.markdown(build_under_table(query_top_under(20)), unsafe_allow_html=True)
else:
    col_ov, col_un = st.columns(2, gap="large")
    with col_ov:
        st.markdown('<div class="section-title">🟢 Top 20 Squadre · Over 2.5</div>', unsafe_allow_html=True)
        st.markdown(build_over_table(query_top_over(20)), unsafe_allow_html=True)
    with col_un:
        st.markdown('<div class="section-title-red">🔴 Top 20 Squadre · Under 3.5</div>', unsafe_allow_html=True)
        st.markdown(build_under_table(query_top_under(20)), unsafe_allow_html=True)

st.markdown('<hr class="divider">', unsafe_allow_html=True)

# ──────────────────────────────────────────────
#  GOL PER LEGA
# ──────────────────────────────────────────────
st.markdown('<div class="section-title-blue">📊 Gol Fatti / Subiti per Lega</div>', unsafe_allow_html=True)

leghe = query_leghe()
lega_sel = st.selectbox("Seleziona lega", options=leghe, label_visibility="collapsed")
df_gol = query_gol_lega(lega_sel)

# altezza iframe = header + righe (niente scroll interno)
iframe_h = 40 + len(df_gol) * (30 if is_mobile else 32)
components.html(build_gol_table(df_gol, mobile=is_mobile), height=iframe_h, scrolling=False)

st.markdown("<hr class='divider'>", unsafe_allow_html=True)
# ──────────────────────────────────────────────
#  CALENDARIO PROSSIME PARTITE
# ──────────────────────────────────────────────
st.markdown('<div class="section-title-blue">📅 Prossime Partite</div>', unsafe_allow_html=True)

# Selectbox dedicata per il calendario (usa query_leghe per caricare i nomi)
leghe_disponibili = query_leghe()
lega_cal_sel = st.selectbox(
    "Seleziona lega per il calendario", 
    options=leghe_disponibili, 
    key="cal_box", 
    label_visibility="collapsed"
)

# Esecuzione query per il calendario
df_next = conn.query(query.CALENDARIO_LEGA_SQL, params={"lega": lega_cal_sel})

if not df_next.empty:
    # Identifichiamo la prossima giornata disponibile
    prossima_g = df_next['giornata'].min()
       
    # Filtriamo i dati e generiamo la tabella stilizzata
    df_filtered = df_next[df_next['giornata'] == prossima_g]
    st.markdown(build_calendario(df_filtered), unsafe_allow_html=True)
else:
    st.info("Nessuna partita in programma nel calendario per questa lega.")

st.markdown("<hr class='divider'>", unsafe_allow_html=True)
# ──────────────────────────────────────────────
#  FOOTER
# ──────────────────────────────────────────────
st.markdown(
    "<div style='text-align:center;color:#3d4460;font-size:0.75rem'>"
    "Play Responsibily - We are Not responsable of any losses</div>",
    unsafe_allow_html=True,
)