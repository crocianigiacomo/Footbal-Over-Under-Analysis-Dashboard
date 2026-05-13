import streamlit as st
import pandas as pd
import query
import stats_engine
import ui_components

# --- FUNZIONE AGGREGATRICE IN CACHE ---
@st.cache_data(ttl=3600, show_spinner=False)
def genera_schedina_globale(leghe_disponibili):
    import sqlite3
    tutte_predizioni = []
    
    with sqlite3.connect('calcio.db') as db:
        for lega in leghe_disponibili:
            df_p = pd.read_sql("SELECT alpha FROM parametri_leghe WHERE lega = :lega", db, params={"lega": lega})
            alpha_l = df_p['alpha'].iloc[0] if not df_p.empty else 0.12
            
            df_raw_l = pd.read_sql(query.MATCH_DATA_SQL, db, params={"lega": lega})
            df_cal_l = pd.read_sql(query.CALENDARIO_DETTAGLIATO_SQL, db, params={"lega": lega})
            
            if not df_cal_l.empty:
                df_fut_l = df_cal_l[(pd.to_datetime(df_cal_l['data_ora'], utc=True) >= pd.Timestamp.now(tz='UTC')) & (df_cal_l['is_recupero'] == 0)]
                
                # --- FIX: ISOLIAMO SOLO IL PROSSIMO TURNO ---
                if not df_fut_l.empty:
                    g_target = df_fut_l['giornata'].iloc[0] # Trova la prossima giornata giocabile
                    df_turno_corrente = df_fut_l[df_fut_l['giornata'] == g_target] # Filtra solo quella
                    
                    # Calcoliamo per entrambe le soglie SOLO sul turno corrente
                    for s in [2.5, 3.5]:
                        p_res = stats_engine.calculate_predictions(df_raw_l, df_turno_corrente, s, alpha_l)
                        if not p_res.empty:
                            p_res['Lega'] = lega
                            tutte_predizioni.append(p_res)
                            
    if not tutte_predizioni:
        return pd.DataFrame()

    df_total = pd.concat(tutte_predizioni, ignore_index=True)
    # Ordina per affidabilità e prende i top 10 globali
    return df_total.sort_values(by="Prob %", ascending=False).head(10)


# 1. CONFIGURAZIONE
st.set_page_config(page_title="XG Football Analytics", layout="wide", initial_sidebar_state="collapsed")

with open('style.css') as f:
    st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

conn = st.connection("calcio_db", type="sql", url="sqlite:///calcio.db")

def query_leghe():
    return conn.query(query.LISTA_LEGHE_SQL, ttl=3600)["lega"].tolist()

leghe_disp = query_leghe()

# 2. TITOLI E NAV BAR
st.markdown('<div class="main-title">XG Football Analytics</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Advanced Data & Predictions System</div>', unsafe_allow_html=True)
st.markdown(ui_components.build_bottom_nav(), unsafe_allow_html=True)

# 3. CONSOLE DI COMANDO UNIFICATA
with st.container(border=True):
    c_f1, c_f2, c_f3 = st.columns([2, 1, 1])
    with c_f1:
        global_lega = st.selectbox("🌍 Lega:", options=leghe_disp, key="g_lega")
    with c_f2:
        global_soglia = st.segmented_control("🎯 Soglia:", options=[2.5, 3.5], key="g_soglia")
        if global_soglia is None: global_soglia = 2.5
    with c_f3:
        st.write("") # Spaziatore per allineamento
        forma = st.toggle("📈 Forma Recente", value=True, key="g_forma")

st.divider()

# --- SEZIONE 1: PREVISIONI (Spostata in alto) ---
st.markdown('<div id="previsioni" class="section-title-red">🔮 Previsioni </div>', unsafe_allow_html=True)

with st.spinner("Analisi in corso..."):
    # Recupero Alpha
    try:
        df_p = conn.query("SELECT alpha FROM parametri_leghe WHERE lega = :l", params={"l": global_lega}, ttl=3600)
        alpha_db = df_p['alpha'].iloc[0] if not df_p.empty else 0.12
    except: alpha_db = 0.12
    
    alpha_finale = alpha_db if forma else 0.0
    df_raw = conn.query(query.MATCH_DATA_SQL, params={"lega": global_lega}, ttl=3600)
    df_cal = conn.query(query.CALENDARIO_DETTAGLIATO_SQL, params={"lega": global_lega}, ttl=3600)
    
    mostrato = False
    if not df_cal.empty:
        df_fut = df_cal[pd.to_datetime(df_cal['data_ora'], utc=True) >= pd.Timestamp.now(tz='UTC')]
        
        # Recuperi
        df_rec = df_fut[df_fut['is_recupero'] == 1]
        if not df_rec.empty:
            p_rec = stats_engine.calculate_predictions(df_raw, df_rec, global_soglia, alpha_finale)
            if not p_rec.empty:
                st.markdown('<div style="color:#ed4245; font-weight:700; margin-bottom:10px;">🔄 RECUPERI</div>', unsafe_allow_html=True)
                st.html(ui_components.build_prediction_table(p_rec))
                st.divider()
                mostrato = True

        # Turno Standard
        df_std = df_fut[df_fut['is_recupero'] == 0]
        if not df_std.empty:
            g_target = df_std['giornata'].iloc[0]
            df_curr_p = df_std[df_std['giornata'] == g_target]
            p_std = stats_engine.calculate_predictions(df_raw, df_curr_p, global_soglia, alpha_finale)
            if not p_std.empty:
                st.markdown(f'<div style="color:#5865F2; font-weight:700; margin-bottom:10px;">📌 TURNO PRINCIPALE</div>', unsafe_allow_html=True)
                st.html(ui_components.build_prediction_table(p_std))
                mostrato = True
    
    if not mostrato: st.warning("Nessuna previsione disponibile.")
    st.markdown(f"<div style='text-align:right; font-size:0.7rem; color:#8e9297;'>Alpha: {alpha_finale}</div>", unsafe_allow_html=True)

st.divider()

# --- SEZIONE 2: CALENDARIO ---
st.markdown('<div id="calendario" class="section-title-blue">📅 Calendario</div>', unsafe_allow_html=True)

if not df_cal.empty:
    df_viva = df_cal[pd.to_datetime(df_cal['data_ora'], utc=True) >= pd.Timestamp.now(tz='UTC')]
    
    # Recuperi
    df_c_rec = df_viva[df_viva['is_recupero'] == 1]
    if not df_c_rec.empty:
        st.markdown('<div style="color:#ed4245; font-weight:700; margin-bottom:10px;">🔄 RECUPERI</div>', unsafe_allow_html=True)
        st.html(ui_components.build_calendario(df_c_rec))
        st.divider()
    
    # Turno Standard (Rimosso il numero giornata tra parentesi)
    df_c_std = df_viva[df_viva['is_recupero'] == 0]
    if not df_c_std.empty:
        g_c = df_c_std['giornata'].iloc[0]
        st.markdown('<div style="color:#5865F2; font-weight:700; margin-bottom:10px;">📌 PROSSIMO TURNO</div>', unsafe_allow_html=True)
        st.html(ui_components.build_calendario(df_c_std[df_c_std['giornata'] == g_c]))
else:
    st.info("Calendario non disponibile.")

st.divider()

# --- SEZIONE 3: RANKING (Limite ridotto a 15) ---
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
st.divider()

# --- SEZIONE 5: SCHEDINA DELLA SETTIMANA ---
st.markdown('<div id="schedina" class="section-title-red">🎟️ Schedina della Settimana </div>', unsafe_allow_html=True)
with st.spinner("Calcolo schedina in corso..."):
    df_top_10 = genera_schedina_globale(leghe_disp) 
    
    if not df_top_10.empty:
        st.html(ui_components.build_betting_slip(df_top_10))
    else:
        st.warning("Dati insufficienti per generare la schedina.")
st.divider()

# --- FOOTER ---
st.markdown('<div class="footer">Made with ❤️ by Roosco | Data from Football-Data.org</div>', unsafe_allow_html=True)