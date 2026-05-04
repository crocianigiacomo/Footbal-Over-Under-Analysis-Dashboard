import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import query  # Importiamo il nostro nuovo file di query

# ──────────────────────────────────────────────
#  CONFIG PAGINA
# ──────────────────────────────────────────────
st.set_page_config(
    page_title="Calcio Stats Dashboard",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# [Manteniamo il tuo script JS per rilevamento larghezza e CSS...]
# ... (il codice CSS rimane lo stesso che hai fornito) ...

# ──────────────────────────────────────────────
#  CONNESSIONE DB (MODERNA)
# ──────────────────────────────────────────────
# st.connection gestisce automaticamente cache e thread-safety
conn = st.connection("calcio_db", type="sql", url="sqlite:///calcio.db")

def query_top_over(limit=20):
    return conn.query(query.TOP_OVER_SQL, ttl=300, params={"limit": limit})

def query_top_under(limit=20):
    return conn.query(query.TOP_UNDER_SQL, ttl=300, params={"limit": limit})

def query_leghe():
    df = conn.query(query.LISTA_LEGHE_SQL, ttl=3600)
    return df["lega"].tolist()

def query_gol_lega(lega):
    return conn.query(query.GOL_LEGA_SQL, ttl=300, params={"lega": lega})

# [Manteniamo i tuoi helpers HTML build_over_table, build_under_table, build_gol_table...]
# ... (le funzioni di rendering HTML rimangono identiche) ...

# ──────────────────────────────────────────────
#  LOGICA UI (Design Mobile/Desktop)
# ──────────────────────────────────────────────
# [Rilevamento is_mobile...]
try:
    screen_w = int(st.query_params.get("sw", 1200))
except Exception:
    screen_w = 1200
is_mobile = screen_w < 768

st.markdown('<div class="main-title">⚽ Calcio Stats Dashboard</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Analisi Over / Under · Gol per squadra e per lega</div>', unsafe_allow_html=True)
st.markdown('<hr class="divider">', unsafe_allow_html=True)

if is_mobile:
    st.markdown('<div class="section-title">🟢 Top 20 Squadre · Over 2.5</div>', unsafe_allow_html=True)
    st.markdown(build_over_table(query_top_over(20)), unsafe_allow_html=True)
    # ... resto del layout mobile ...
else:
    col_ov, col_un = st.columns(2, gap="large")
    with col_ov:
        st.markdown('<div class="section-title">🟢 Top 20 Squadre · Over 2.5</div>', unsafe_allow_html=True)
        st.markdown(build_over_table(query_top_over(20)), unsafe_allow_html=True)
    with col_un:
        st.markdown('<div class="section-title-red">🔴 Top 20 Squadre · Under 3.5</div>', unsafe_allow_html=True)
        st.markdown(build_under_table(query_top_under(20)), unsafe_allow_html=True)

st.markdown('<hr class="divider">', unsafe_allow_html=True)

# GOL PER LEGA
st.markdown('<div class="section-title-blue">📊 Gol Fatti / Subiti per Lega</div>', unsafe_allow_html=True)
leghe = query_leghe()
lega_sel = st.selectbox("Seleziona lega", options=leghe, label_visibility="collapsed")
df_gol = query_gol_lega(lega_sel)

# Rendering tabella gol con iframe dinamico
iframe_h = 55 + len(df_gol) * (34 if is_mobile else 37)
components.html(build_gol_table(df_gol, mobile=is_mobile), height=iframe_h, scrolling=False)

st.markdown("<hr class='divider'>", unsafe_allow_html=True)
st.markdown("<div style='text-align:center;color:#3d4460;font-size:0.75rem'>Dashboard Ottimizzata · query.py + st.connection</div>", unsafe_allow_html=True)