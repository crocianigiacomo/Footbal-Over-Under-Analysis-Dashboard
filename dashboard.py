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
    with sqlite3.connect('calcio.db') as db:
        for lega in leghe_disponibili:
            # Recupero parametri ufficiali della lega
            df_params = pd.read_sql("SELECT alpha, giornata_target FROM parametri_leghe WHERE lega = :l", db, params={"l": lega})
            if df_params.empty: continue
            
            # FIX CHIAVE: Forziamo la conversione in tipi Python standard!
            alpha_l = float(df_params['alpha'].iloc[0])
            gt_l = int(df_params['giornata_target'].iloc[0]) 
            
            # Recupero dati per il motore e i soli match DA GIOCARE della Giornata Target
            df_raw_l = pd.read_sql(query.MATCH_DATA_SQL, db, params={"lega": lega})
            df_turno_l = pd.read_sql("SELECT * FROM calendario WHERE lega = :l AND giornata = :gt", db, params={"l": lega, "gt": gt_l})
            
            if not df_turno_l.empty:
                for s in [2.5, 3.5]:
                    p_res = stats_engine.calculate_predictions(df_raw_l, df_turno_l, s, alpha_l)
                    if not p_res.empty:
                        p_res['Lega'] = lega
                        tutte_predizioni.append(p_res)
                            
    if not tutte_predizioni: return pd.DataFrame()
    return pd.concat(tutte_predizioni, ignore_index=True).sort_values(by="Prob %", ascending=False).head(10)

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

# --- RECUPERO DATI LEGA SELEZIONATA ---
# Recuperiamo Alpha e GT dal DB
df_p_lega = conn.query("SELECT alpha, giornata_target FROM parametri_leghe WHERE lega = :l", params={"l": global_lega}, ttl=3600)
alpha_finale = df_p_lega['alpha'].iloc[0] if not df_p_lega.empty and forma else 0.0
gt_lega = df_p_lega['giornata_target'].iloc[0] if not df_p_lega.empty else 0

# Dati per il calendario e il motore
df_raw = conn.query(query.MATCH_DATA_SQL, params={"lega": global_lega}, ttl=3600)
df_cal_full = conn.query(query.CALENDARIO_DETTAGLIATO_SQL, params={"lega": global_lega}, ttl=3600)

# --- SEZIONE 1: PREVISIONI ---
st.markdown('<div id="previsioni" class="section-title-red">🔮 Previsioni </div>', unsafe_allow_html=True)

with st.spinner("Analisi in corso..."):
    if not df_cal_full.empty:
        # A. Recuperi (Giornata < GT)
        df_rec = df_cal_full[df_cal_full['is_recupero'] == 1]
        if not df_rec.empty:
            p_rec = stats_engine.calculate_predictions(df_raw, df_rec, global_soglia, alpha_finale)
            if not p_rec.empty:
                st.markdown('<div style="color:#ed4245; font-weight:700; margin-bottom:10px;">🔄 RECUPERI</div>', unsafe_allow_html=True)
                st.html(ui_components.build_prediction_table(p_rec))
                st.divider()

        # B. Turno Principale (Giornata == GT, solo match da giocare)
        # Filtriamo quelli che NON hanno 'FINISHED' in data_ora
        df_std = df_cal_full[(df_cal_full['is_recupero'] == 0) & (df_cal_full['data_ora'] != 'FINISHED')]
        if not df_std.empty:
            p_std = stats_engine.calculate_predictions(df_raw, df_std, global_soglia, alpha_finale)
            if not p_std.empty:
                st.markdown(f'<div style="color:#5865F2; font-weight:700; margin-bottom:10px;">📌 GIORNATA {gt_lega}</div>', unsafe_allow_html=True)
                st.html(ui_components.build_prediction_table(p_std))
        else:
            st.info("Tutti i match della giornata sono conclusi o non ancora disponibili.")
    else:
        st.warning("Nessuna previsione disponibile.")

st.divider()

# --- SEZIONE 2: CALENDARIO (GAME CENTER) ---
st.markdown('<div id="calendario" class="section-title-blue">📅 Calendario & Risultati</div>', unsafe_allow_html=True)

if not df_cal_full.empty:
    # A. Recuperi
    df_c_rec = df_cal_full[df_cal_full['is_recupero'] == 1]
    if not df_c_rec.empty:
        st.markdown('<div style="color:#ed4245; font-weight:700; margin-bottom:10px;">🔄 RECUPERI</div>', unsafe_allow_html=True)
        st.html(ui_components.build_calendario(df_c_rec))
        st.divider()
    
    # B. Giornata Target (Mostra tutto: finiti e da giocare)
    df_c_std = df_cal_full[df_cal_full['is_recupero'] == 0]
    if not df_c_std.empty:
        st.markdown(f'<div style="color:#5865F2; font-weight:700; margin-bottom:10px;">📌 QUADRO GIORNATA {gt_lega}</div>', unsafe_allow_html=True)
        st.html(ui_components.build_calendario(df_c_std))
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
