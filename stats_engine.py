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
    
    teams = sorted(set(df['squadra_casa']) | set(df['squadra_trasferta']))
    records = []
    for t in teams:
        hm, am = df[df['squadra_casa']==t], df[df['squadra_trasferta']==t]
        if hm['w'].sum() == 0 or am['w'].sum() == 0: continue
        records.append({
            'squadra': t,
            'avg_gfc': (hm['gol_casa']*hm['w']).sum() / hm['w'].sum(),
            'avg_gsc': (hm['gol_trasferta']*hm['w']).sum() / hm['w'].sum(),
            'avg_gft': (am['gol_trasferta']*am['w']).sum() / am['w'].sum(),
            'avg_gst': (am['gol_casa']*am['w']).sum() / am['w'].sum(),
        })
    return pd.DataFrame(records).set_index('squadra'), avg_h, avg_a

def estimate_rho(df, strengths, avg_h, avg_a, alpha):
    low = df[(df['gol_casa']<=1) & (df['gol_trasferta']<=1)].copy()
    if len(low) < 5: return -0.15
    max_g = df['giornata'].max()
    def neg_ll(rho):
        ll = 0.0
        for _, r in low.iterrows():
            sh, sa = r['squadra_casa'], r['squadra_trasferta']
            if sh not in strengths.index or sa not in strengths.index: continue
            exph = strengths.loc[sh,'avg_gfc'] * strengths.loc[sa,'avg_gst'] / avg_a
            expa = strengths.loc[sa,'avg_gft'] * strengths.loc[sh,'avg_gsc'] / avg_h
            tau = dixon_coles_correction(int(r['gol_casa']), int(r['gol_trasferta']), exph, expa, rho)
            ll += np.exp(-alpha*(max_g-r['giornata'])) * np.log(max(tau, 1e-9))
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
        
        po, pu = 0.0, 0.0
        for ih in range(10):
            for ia in range(10):
                p = poisson.pmf(ih, exph) * poisson.pmf(ia, expa) * dixon_coles_correction(ih, ia, exph, expa, rho)
                if (ih+ia) > soglia: po += p
                else: pu += p
        
        prob = round((po/(po+pu))*100, 1) if po > pu else round((pu/(po+pu))*100, 1)
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
        
        for _, match in test_matches.iterrows():
            # Calcolo le forze squadre usando solo i dati PRECEDENTI a questa partita
            past_data = df_raw[df_raw['giornata'] < match['giornata']]
            if past_data.empty: continue
            
            # Calcolo medie e forze con l'alpha in prova
            try:
                strengths, avg_h, avg_a = compute_weighted_strengths(past_data, alpha_trial)
                h, a = match['squadra_casa'], match['squadra_trasferta']
                
                if h not in strengths.index or a not in strengths.index: continue
                
                exph = strengths.loc[h,'avg_gfc'] * strengths.loc[a,'avg_gst'] / avg_a
                expa = strengths.loc[a,'avg_gft'] * strengths.loc[h,'avg_gsc'] / avg_h
                
                # Calcolo probabilità del risultato reale (es. 2-1)
                prob_match = poisson.pmf(match['gol_casa'], exph) * poisson.pmf(match['gol_trasferta'], expa)
                
                # Log-Loss: aggiungo -log(probabilità) [min 1e-10 per evitare log(0)]
                total_log_loss -= np.log(max(prob_match, 1e-10))
            except (ValueError, KeyError, ZeroDivisionError):
                continue
                
        return total_log_loss

    # Ottimizzazione tra 0.01 (molto stabile) e 0.30 (molto reattivo alla forma)
    res = minimize_scalar(log_loss_objective, bounds=(0.01, 0.30), method='bounded')
    return round(res.x, 4) if res.success else 0.12