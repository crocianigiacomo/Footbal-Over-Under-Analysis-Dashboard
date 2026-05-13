import pandas as pd
import numpy as np
from scipy.stats import poisson
from scipy.optimize import minimize_scalar

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
    
    # Usiamo il GroupBy: operazione migliaia di volte più veloce del ciclo for
    df['wgfc'] = df['gol_casa'] * df['w']
    df['wgsc'] = df['gol_trasferta'] * df['w']
    
    # Aggreghiamo i dati per casa e trasferta separatamente
    casa = df.groupby('squadra_casa').agg(sum_w_c=('w','sum'), sum_gfc=('wgfc','sum'), sum_gsc=('wgsc','sum'))
    tras = df.groupby('squadra_trasferta').agg(sum_w_t=('w','sum'), sum_gft=('wgfc','sum'), sum_gst=('wgsc','sum')) # nota: wgfc qui sono i gol fatti in trasferta
    
    # Uniamo e calcoliamo le medie
    res = casa.join(tras, how='inner')
    res['avg_gfc'] = res['sum_gfc'] / res['sum_w_c']
    res['avg_gsc'] = res['sum_gsc'] / res['sum_w_c']
    res['avg_gft'] = res['sum_gft'] / res['sum_w_t']
    res['avg_gst'] = res['sum_gst'] / res['sum_w_t']
    
    return res[['avg_gfc', 'avg_gsc', 'avg_gft', 'avg_gst']], avg_h, avg_a

def estimate_rho(df, strengths, avg_h, avg_a, alpha):
    low = df[(df['gol_casa']<=1) & (df['gol_trasferta']<=1)].copy()
    if len(low) < 5: return -0.15
    max_g = df['giornata'].max()
    # Convertiamo i dati in matrici/array prima del loop per evitare l'uso di loc/iterrows costanti
    low_records = low.to_dict('records')
    
    def neg_ll(rho):
        ll = 0.0
        for r in low_records:
            sh, sa = r['squadra_casa'], r['squadra_trasferta']
            if sh in strengths.index and sa in strengths.index:
                # Accesso rapido tramite .at o pre-calcolo
                s_h = strengths.loc[sh]
                s_a = strengths.loc[sa]
                
                exph = s_h['avg_gfc'] * s_a['avg_gst'] / avg_a
                expa = s_a['avg_gft'] * s_h['avg_gsc'] / avg_h
                
                tau = dixon_coles_correction(int(r['gol_casa']), int(r['gol_trasferta']), exph, expa, rho)
                weight = np.exp(-alpha * (max_g - r['giornata']))
                ll += weight * np.log(max(tau, 1e-9))
        return -ll
    res = minimize_scalar(neg_ll, bounds=(-0.5, 0.1), method='bounded')
    return round(res.x, 4) if res.success else -0.15

def calculate_predictions(df_raw, df_next, soglia, alpha):
    """Calcola le predizioni e restituisce un DataFrame."""
    if df_raw.empty or len(df_raw) < 10 or df_next.empty:
        return pd.DataFrame()

    strengths, avg_h, avg_a = compute_weighted_strengths(df_raw, alpha)
    rho = estimate_rho(df_raw, strengths, avg_h, avg_a, alpha)
    
    # Il motore ora calcola le previsioni per TUTTE le righe che riceve
    matches = df_next.copy()


    preds = []
    for _, m in matches.iterrows():
        h, a = m['squadra_casa'], m['squadra_trasferta']
        if h not in strengths.index or a not in strengths.index: continue
        exph = strengths.loc[h,'avg_gfc'] * strengths.loc[a,'avg_gst'] / avg_a
        expa = strengths.loc[a,'avg_gft'] * strengths.loc[h,'avg_gsc'] / avg_h
        
        # 1. Calcolo vettoriale delle probabilità di Poisson per i gol (0-9)
        goals = np.arange(10)
        prob_h = poisson.pmf(goals, exph)
        prob_a = poisson.pmf(goals, expa)

        # 2. Creazione matrice 10x10 tramite prodotto esterno (tutte le combinazioni di punteggio)
        prob_matrix = np.outer(prob_h, prob_a)

        # 3. Applicazione correzione Dixon-Coles (sui 4 casi specifici)
        prob_matrix[0, 0] *= dixon_coles_correction(0, 0, exph, expa, rho)
        prob_matrix[0, 1] *= dixon_coles_correction(0, 1, exph, expa, rho)
        prob_matrix[1, 0] *= dixon_coles_correction(1, 0, exph, expa, rho)
        prob_matrix[1, 1] *= dixon_coles_correction(1, 1, exph, expa, rho)

        # 4. Calcolo Over/Under istantaneo tramite maschera di somma gol
        goal_sums = np.add.outer(goals, goals)
        po = prob_matrix[goal_sums > soglia].sum()
        pu = prob_matrix[goal_sums <= soglia].sum()
        
        total_p = po + pu
        if total_p > 0:
            prob = round(float((max(po, pu) / total_p) * 100), 1)
        else:
            prob = 0.0
            
        res_label = f"🔥 Over {soglia}" if po > pu else f"❄️ Under {soglia}"
        color = ("#FFBB00" if prob >= 65 else "#FFE9AB") if po > pu else ("#0080FF" if prob >= 65 else "#9ECEFF")
        
        preds.append({
            "Partita": f"{h} vs {a}", "Gol Attesi Casa": round(exph, 2), "Gol Attesi Trasferta": round(expa, 2),
            "Gol Attesi Totali": round(exph+expa, 2), "Esito": res_label, "Prob %": prob, "Colore": color
        })
    return pd.DataFrame(preds)

def calibrate_alpha(df_raw):
    """Trova l'alpha ottimale minimizzando la Log-Loss sulle ultime partite giocate."""
    
    # 1. GESTIONE INIZIO STAGIONE: Se ci sono meno di 50 partite, usiamo il default
    if len(df_raw) < 50:
        return 0.12

    # Prendo i dati necessari per la simulazione
    max_g = df_raw['giornata'].max()
    # Testiamo l'alpha sulle ultime 3 giornate per vedere quanto è stato accurato
    test_matches = df_raw[df_raw['giornata'] > (max_g - 3)]
    
    def log_loss_objective(alpha_trial):
        total_log_loss = 0
        
                # Calcoliamo le forze una volta sola per l'intero set di test (Hold-out)
        train_data = df_raw[df_raw['giornata'] <= (max_g - 2)]
        test_matches = df_raw[df_raw['giornata'] > (max_g - 2)]
        
        if train_data.empty or test_matches.empty: return 999
        
        strengths, avg_h, avg_a = compute_weighted_strengths(train_data, alpha_trial)
        
        # Calcolo vettorizzato della Log-Loss (senza iterrows se possibile, o ridotto)
        total_ll = 0
        for m in test_matches.to_dict('records'):
            h, a = m['squadra_casa'], m['squadra_trasferta']
            if h in strengths.index and a in strengths.index:
                exph = strengths.at[h,'avg_gfc'] * strengths.at[a,'avg_gst'] / avg_a
                expa = strengths.at[a,'avg_gft'] * strengths.at[h,'avg_gsc'] / avg_h
                prob = poisson.pmf(m['gol_casa'], exph) * poisson.pmf(m['gol_trasferta'], expa)
                total_ll -= np.log(max(prob, 1e-10))
        return total_ll

    # Ottimizzazione tra 0.01 (molto stabile) e 0.30 (molto reattivo alla forma)
    res = minimize_scalar(log_loss_objective, bounds=(0.01, 0.30), method='bounded')
    return round(res.x, 4) if res.success else 0.12