import streamlit as st
import pandas as pd
import sqlite3
import query
import stats_engine
import ui_components

# 1. CONFIGURAZIONE
st.set_page_config(page_title="XG Football Analytics", layout="wide", initial_sidebar_state="collapsed")

with open('style.css') as f:
    st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

conn = st.connection("calcio_db", type="sql", url="sqlite:///calcio.db")

# --- FUNZIONE AGGREGATRICE IN CACHE PER LA SCHEDINA ---
@st.cache_data(ttl=3600, show_spinner=False)
def genera_schedina_globale(leghe_disponibili):
    tutte_predizioni = []
    
    # Usiamo la connessione in sola lettura per non bloccare il WAL mode!
    with sqlite3.connect('file:calcio.db?mode=ro', uri=True) as db:
        # BULK EXTRACTION: Facciamo solo 3 query totali per estrarre tutto
        df_params_all = pd.read_sql("SELECT lega, alpha, giornata_target FROM parametri_leghe", db)
        df_raw_all = pd.read_sql("SELECT lega, giornata, squadra_casa, squadra_trasferta, gol_casa, gol_trasferta FROM partite", db)
        df_cal_all = pd.read_sql("SELECT lega, giornata, squadra_casa, squadra_trasferta FROM calendario", db)

    # Filtraggio super-veloce in memoria (RAM) tramite Pandas
    for lega in leghe_disponibili:
        df_params = df_params_all[df_params_all['lega'] == lega]
        if df_params.empty: continue
        
        alpha_l = float(df_params['alpha'].iloc[0])
        gt_l = int(df_params['giornata_target'].iloc[0]) 
        
        df_raw_l = df_raw_all[df_raw_all['lega'] == lega]
        df_turno_l = df_cal_all[(df_cal_all['lega'] == lega) & (df_cal_all['giornata'] == gt_l)]
        
        if not df_turno_l.empty:
            for s in [2.5, 3.5]:
                p_res = stats_engine.calculate_predictions(df_raw_l, df_turno_l, s, alpha_l)
                if not p_res.empty:
                    p_res['Lega'] = lega
                    tutte_predizioni.append(p_res)
                            
    if not tutte_predizioni: return pd.DataFrame()
    return pd.concat(tutte_predizioni, ignore_index=True).sort_values(by="Prob %", ascending=False).head(10)

@st.cache_data(ttl=3600, show_spinner=False)
def prepara_dati_lega(lega, usa_forma):
    # 1. Recupero parametri
    df_p = conn.query("SELECT alpha, giornata_target FROM parametri_leghe WHERE lega = :l", params={"l": lega}, ttl=3600)
    alpha = float(df_p['alpha'].iloc[0]) if not df_p.empty and usa_forma else 0.0
    gt = int(df_p['giornata_target'].iloc[0]) if not df_p.empty else 0
    
    # 2. Query dati massivi
    df_raw = conn.query(query.MATCH_DATA_SQL, params={"lega": lega}, ttl=3600)
    df_cal = conn.query(query.CALENDARIO_DETTAGLIATO_SQL, params={"lega": lega}, ttl=3600)
    
    # 3. Filtraggi preparatori centralizzati (eseguiti 1 sola volta grazie alla cache)
    df_rec = df_cal[df_cal['is_recupero'] == 1]
    df_da_giocare = df_cal[(df_cal['is_recupero'] == 0) & (df_cal['match_status'] == 'SCHEDULED')]
    df_turno_intero = df_cal[df_cal['is_recupero'] == 0]
    
    return alpha, gt, df_raw, df_rec, df_da_giocare, df_turno_intero

# 2. CARICAMENTO DATI INIZIALI
def query_leghe():
    return conn.query(query.LISTA_LEGHE_SQL, ttl=3600)["lega"].tolist()

leghe_disp = query_leghe()

# 3. TITOLI E NAV BAR
st.markdown('<div class="main-title">XG Football Analytics</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Advanced Data & Predictions System</div>', unsafe_allow_html=True)
st.markdown(ui_components.build_bottom_nav(), unsafe_allow_html=True)

# 4. CONSOLE DI COMANDO UNIFICATA (Centrata via CSS)
with st.container(border=True):
    global_lega = st.selectbox("🌍 Lega:", options=leghe_disp, key="g_lega")
    c_f1, c_f2 = st.columns(2)
    with c_f1:
        global_soglia = st.segmented_control("🎯 Soglia:", options=[2.5, 3.5], key="g_soglia")
        if global_soglia is None: global_soglia = 2.5
    with c_f2:
        forma = st.toggle("📈 Forma Recente", value=True, key="g_forma")

st.divider()

# --- RECUPERO E PREPARAZIONE DATI ---
alpha_finale, gt_lega, df_raw, df_rec, df_da_giocare, df_turno_intero = prepara_dati_lega(global_lega, forma)

# --- SEZIONE 1: PREVISIONI ---
st.markdown('<div id="previsioni" class="section-title-red">🔮 Previsioni </div>', unsafe_allow_html=True)

with st.spinner("Analisi in corso..."):
    if not df_rec.empty or not df_da_giocare.empty:
        # A. Recuperi
        if not df_rec.empty:
            p_rec = stats_engine.calculate_predictions(df_raw, df_rec, global_soglia, alpha_finale)
            if not p_rec.empty:
                st.markdown('<div style="color:#ed4245; font-weight:700; margin-bottom:10px;">🔄 RECUPERI</div>', unsafe_allow_html=True)
                st.html(ui_components.build_prediction_table(p_rec))
                st.divider()

        # B. Turno Principale (Solo match da giocare)
        if not df_da_giocare.empty:
            p_std = stats_engine.calculate_predictions(df_raw, df_da_giocare, global_soglia, alpha_finale)
            if not p_std.empty:
                st.markdown(f'<div style="color:#5865F2; font-weight:700; margin-bottom:10px;">📌 GIORNATA {gt_lega}</div>', unsafe_allow_html=True)
                st.html(ui_components.build_prediction_table(p_std))
    else:
        st.warning("Nessuna previsione disponibile per i match in arrivo.")

st.divider()

# --- SEZIONE 2: CALENDARIO E RISULTATI ---
st.markdown('<div id="calendario" class="section-title-blue">📅 Calendario & Risultati</div>', unsafe_allow_html=True)

if not df_turno_intero.empty or not df_rec.empty:
        # A. Recuperi
        if not df_rec.empty:
            st.markdown('<div style="color:#ed4245; font-weight:700; margin-bottom:10px;">🔄 RECUPERI</div>', unsafe_allow_html=True)
            st.html(ui_components.build_calendario(df_rec))
            st.divider()
        
        # B. Giornata Target (Tutti i match)
        if not df_turno_intero.empty:
            st.markdown(f'<div style="color:#5865F2; font-weight:700; margin-bottom:10px;">📌 QUADRO GIORNATA {gt_lega}</div>', unsafe_allow_html=True)
            st.html(ui_components.build_calendario(df_turno_intero))
else:
    st.info("Calendario non disponibile.")

st.divider()

# --- SEZIONE 3: RANKING ---
st.markdown('<div id="statistiche" class="section-title">📊 Ranking Globale </div>', unsafe_allow_html=True)
r1, r2 = st.columns(2)
with r1:
    df_ov = conn.query(query.TOP_OVER_SQL, params={"soglia": global_soglia, "limit": 15}, ttl=3600)
    st.html(ui_components.build_stats_table(df_ov, "over", global_soglia))
with r2:
    df_un = conn.query(query.TOP_UNDER_SQL, params={"soglia": global_soglia, "limit": 15}, ttl=3600)
    st.html(ui_components.build_stats_table(df_un, "under", global_soglia))

st.divider()

# --- SEZIONE 4: RETI ---
st.markdown('<div id="reti" class="section-title-blue">🎯 Performance Reti </div>', unsafe_allow_html=True)
df_g = conn.query(query.GOL_LEGA_SQL, params={"lega": global_lega}, ttl=3600)
st.html(ui_components.build_gol_table(df_g))

# --- SEZIONE 5: SCHEDINA DELLA SETTIMANA ---
st.divider()
st.markdown('<div id="schedina" class="section-title-red">🎟️ Schedina della Settimana </div>', unsafe_allow_html=True)
with st.spinner("Estrazione Top 10 globale in corso..."):
    df_top_10 = genera_schedina_globale(leghe_disp)
    if not df_top_10.empty:
        st.html(ui_components.build_betting_slip(df_top_10))
    else:
        st.warning("Dati insufficienti per generare la schedina.")

st.divider()
st.markdown('<div class="footer">Made with ❤️ by Roosco | Data from Football-Data.org</div>', unsafe_allow_html=True)
