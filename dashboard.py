import streamlit as st
import pandas as pd
import query
import stats_engine
import ui_components

# 1. CONFIGURAZIONE PAGINA
st.set_page_config(page_title="XG Football Analytics", layout="wide", initial_sidebar_state="collapsed")

# 2. CARICAMENTO STILI CSS ESTERNI
with open('style.css') as f:
    st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

# 3. CONNESSIONE DB E HELPERS
conn = st.connection("calcio_db", type="sql", url="sqlite:///calcio.db")

def query_leghe():
    return conn.query(query.LISTA_LEGHE_SQL, ttl=3600)["lega"].tolist()

def _soglia_widget(label: str, key: str) -> float:
    ss_key = f"_soglia_val_{key}"
    if ss_key not in st.session_state: st.session_state[ss_key] = 2.5
    if st.session_state.get(key) is None: st.session_state[key] = st.session_state[ss_key]
    val = st.segmented_control(label, options=[2.5, 3.5], key=key)
    if val is not None: st.session_state[ss_key] = val
    return st.session_state[ss_key]

# 4. LAYOUT INTERFACCIA
st.markdown('<div class="main-title">XG Football Analytics</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Advanced Data & Predictions System</div>', unsafe_allow_html=True)
st.markdown(ui_components.build_bottom_nav(), unsafe_allow_html=True)

leghe_disp = query_leghe()

# --- SEZIONE PREVISIONI ---
st.markdown('<div id="previsioni" class="section-title-red">🔮 Previsioni </div>', unsafe_allow_html=True)

cp1, cp2, cp3 = st.columns([2, 1, 1])

with cp1: 
    lega_pred = st.selectbox("Seleziona Lega:", options=leghe_disp, key="pred_box")

with cp2: 
    soglia_pred = _soglia_widget("Soglia Gol:", "pred_soglia")

with cp3:
    forma = st.toggle(
        "Forma Recente", 
        value=True, 
        key="forma", 
        help="Applica un peso maggiore alle partite più recenti usando l'Alpha calibrato specificamente per questa lega."
    )

with st.spinner("Calcolo in corso..."):
    # 1. Recupero dinamico dell'Alpha calibrato dal Database
    try:
        # Cerchiamo l'alpha specifico per la lega nella nuova tabella
        df_params = conn.query(
            "SELECT alpha FROM parametri_leghe WHERE lega = :lega", 
            params={"lega": lega_pred}, 
            ttl=3600
        )
        # Se trovato lo usiamo, altrimenti fallback a 0.12
        alpha_db = df_params['alpha'].iloc[0] if not df_params.empty else 0.12
    except Exception:
        # In caso di errore (es. tabella non ancora creata), usiamo il default
        alpha_db = 0.12
    
    # Se il toggle è attivo usiamo l'alpha calibrato, altrimenti 0.0 (tutte le partite pesano uguale)
    alpha_finale = alpha_db if forma else 0.0

        # 2. Recupero dati per il calcolo
    df_raw = conn.query(query.MATCH_DATA_SQL, params={"lega": lega_pred}, ttl=3600)
    # [span_2](start_span)Cambiato nome query[span_2](end_span)
    df_cal = conn.query(query.CALENDARIO_DETTAGLIATO_SQL, params={"lega": lega_pred}, ttl=3600)
    
    # 3. Esecuzione del motore statistico
    if not df_cal.empty:
        # [span_3](start_span)Filtro per passare al motore solo partite da ora in poi[span_3](end_span)
        df_cal['data_ora'] = pd.to_datetime(df_cal['data_ora'], utc=True)
        df_cal = df_cal[df_cal['data_ora'] >= pd.Timestamp.now(tz='UTC')]
        
    preds_df = stats_engine.calculate_predictions(df_raw, df_cal, soglia_pred, alpha_finale)

    
    # 4. Visualizzazione Risultati
    if not preds_df.empty:
        st.html(ui_components.build_prediction_table(preds_df))
        # Mostriamo all'utente quale valore di Alpha sta usando il modello per trasparenza
        st.markdown(
            f"<div style='text-align:right; font-size:0.8rem; color:#8e9297;'>"
            f"Parametro Alpha utilizzato: <b>{alpha_finale}</b>"
            f"</div>", 
            unsafe_allow_html=True
        )
    else:
        st.html(ui_components.build_empty_state(
            "🔮", "Previsioni non disponibili",
            f"Dati storici insufficienti per {lega_pred}."
        ))

st.divider()

# --- SEZIONE CALENDARIO ---
st.markdown('<div id="calendario" class="section-title-blue">📅 Calendario e Recuperi</div>', unsafe_allow_html=True)
lega_cal = st.selectbox("Seleziona Lega:", options=leghe_disp, key="cal_box")

# Eseguiamo la nuova query dettagliata
df_cal = conn.query(query.CALENDARIO_DETTAGLIATO_SQL, params={"lega": lega_cal}, ttl=3600)

if not df_cal.empty:
    df_cal['data_ora'] = pd.to_datetime(df_cal['data_ora'], utc=True)
    now = pd.Timestamp.now(tz='UTC')
    
    # Filtriamo solo i match futuri
    df_display = df_cal[df_cal['data_ora'] >= now]
    
    if not df_display.empty:
        # 1. Visualizzazione RECUPERI (se presenti)
        df_rec = df_display[df_display['is_recupero'] == 1]
        if not df_rec.empty:
            st.markdown('<div style="color:#ed4245; font-weight:700; margin-bottom:10px;">🔄 PARTITE DI RECUPERO</div>', unsafe_allow_html=True)
            st.html(ui_components.build_calendario(df_rec))
            st.divider()
        
        # 2. Visualizzazione TURNO PRINCIPALE
        df_std = df_display[df_display['is_recupero'] == 0]
        if not df_std.empty:
            g_num = df_std['giornata'].iloc[0]
            st.markdown(f'<div style="color:#5865F2; font-weight:700; margin-bottom:10px;">📌 PROSSIMO TURNO (Giornata {g_num})</div>', unsafe_allow_html=True)
            st.html(ui_components.build_calendario(df_std))
    else:
        st.info("Nessun match in programma.")

else:
    st.html(ui_components.build_empty_state(
        "📅", "Nessuna partita in programma",
        f"Il calendario per {lega_cal} non contiene partite future."
    ))

st.divider()

# --- SEZIONE STATISTICHE ---
st.markdown('<div id="statistiche" class="section-title">📊 Ranking </div>', unsafe_allow_html=True)
soglia_stats = _soglia_widget("Soglia Gol:", "stats_soglia")
c1, c2 = st.columns(2)
with c1:
    with st.spinner(""):
        df_ov = conn.query(query.TOP_OVER_SQL, params={"soglia": soglia_stats, "limit": 20}, ttl=3600)
    st.html(ui_components.build_stats_table(df_ov, "over", soglia_stats))
with c2:
    with st.spinner(""):
        df_un = conn.query(query.TOP_UNDER_SQL, params={"soglia": soglia_stats, "limit": 20}, ttl=3600)
    st.html(ui_components.build_stats_table(df_un, "under", soglia_stats))

st.divider()

# --- SEZIONE RETI ---
st.markdown('<div id="reti" class="section-title-blue">🎯 Performance Reti </div>', unsafe_allow_html=True)
lega_sel = st.selectbox("Seleziona Lega:", options=leghe_disp, key="gol_lega")
with st.spinner(""):
    df_gol = conn.query(query.GOL_LEGA_SQL, params={"lega": lega_sel}, ttl=3600)
st.html(ui_components.build_gol_table(df_gol))

st.divider()

# --- SEZIONE FOOTER ---
st.markdown('<div class="footer">Made with ❤️ by Roosco | Data from Football-Data.org</div>', unsafe_allow_html=True)