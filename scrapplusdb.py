import sqlite3
import requests
import pandas as pd
import time
import os

def init_database(db_path='calcio.db'):
    """Inizializza il DB e crea la tabella e gli indici se non esistono."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS partite (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lega TEXT NOT NULL,
            giornata INTEGER NOT NULL,
            squadra_casa TEXT NOT NULL,
            squadra_trasferta TEXT NOT NULL,
            gol_casa INTEGER NOT NULL,
            gol_trasferta INTEGER NOT NULL,
            gol_casa_1t INTEGER,
            gol_trasferta_1t INTEGER,
            gol_casa_2t INTEGER,
            gol_trasferta_2t INTEGER,
            winner_code INTEGER,
            UNIQUE(lega, giornata, squadra_casa, squadra_trasferta)
        )
    ''')
    
    # Creazione Indici
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_lega ON partite(lega)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_giornata ON partite(giornata)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_squadra_casa ON partite(squadra_casa)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_squadra_trasferta ON partite(squadra_trasferta)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_lega_giornata ON partite(lega, giornata)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_winner_code ON partite(winner_code)')
    
    conn.commit()
    return conn

def fetch_and_process_league(league_id, season, api_key):
    """Scarica i dati dall'API e crea un DataFrame."""
    url = f"https://v3.football.api-sports.io/fixtures?league={league_id}&season={season}"
    headers = {
        'x-apisports-key': api_key,
        'x-rapidapi-host': 'v3.football.api-sports.io'
    }
    
    print(f"Scaricamento dati per la lega {league_id}...")
    response = requests.get(url, headers=headers)
    
    if response.status_code != 200:
        print(f"Errore API: {response.status_code}")
        return pd.DataFrame()

    data = response.json()
    matches = data.get('response', [])
    
    if not matches:
        return pd.DataFrame()

    processed_data = []
    for match in matches:
        status = match['fixture']['status']['short']
        # Accettiamo solo partite terminate
        if status not in ['FT', 'AET', 'PEN']:
            continue
        round_name = str(match['league']['round'])    
        home_goals = match['goals']['home']
        away_goals = match['goals']['away']
        
        
        if 'Regular Season' not in round_name:
            continue
        
        if home_goals is None or away_goals is None:
            continue

        processed_data.append({
            'lega': match['league']['name'],
            'giornata': match['league']['round'].replace('Regular Season - ', ''), # Pulisce la stringa della giornata se serve
            'squadra_casa': match['teams']['home']['name'],
            'squadra_trasferta': match['teams']['away']['name'],
            'gol_casa': home_goals,
            'gol_trasferta': away_goals,
            'gol_casa_1t': match['score']['halftime']['home'],
            'gol_trasferta_1t': match['score']['halftime']['away']
        })

    return pd.DataFrame(processed_data)

def optimize_and_calculate(df):
    """Calcola i dati mancanti in modo vettoriale."""
    if df.empty:
        return df
        
    # Gestione valori mancanti
    df['gol_casa_1t'] = df['gol_casa_1t'].fillna(0).astype(int)
    df['gol_trasferta_1t'] = df['gol_trasferta_1t'].fillna(0).astype(int)
    
    # Calcolo 2° tempo
    df['gol_casa_2t'] = df['gol_casa'] - df['gol_casa_1t']
    df['gol_trasferta_2t'] = df['gol_trasferta'] - df['gol_trasferta_1t']
    
    # Calcolo Winner Code (1=Casa, 2=Trasferta, 3=Pareggio)
    df['winner_code'] = 3
    df.loc[df['gol_casa'] > df['gol_trasferta'], 'winner_code'] = 1
    df.loc[df['gol_casa'] < df['gol_trasferta'], 'winner_code'] = 2
    
    # NOVITÀ: Tenta la conversione. Se non è un numero, diventa NaN.
    df['giornata'] = pd.to_numeric(df['giornata'], errors='coerce')
    # Rimuove le righe con NaN (le finte giornate) e poi converte in intero
    df = df.dropna(subset=['giornata'])
    df['giornata'] = df['giornata'].astype(int)
    
    return df

def save_to_sqlite(df, conn):
    """Esegue un INSERT OR REPLACE massivo nel database SQLite."""
    if df.empty:
        return
        
    cursor = conn.cursor()
    
    # Convertiamo il DataFrame in una lista di tuple per l'inserimento
    data_to_insert = list(df[[
        'lega', 'giornata', 'squadra_casa', 'squadra_trasferta', 
        'gol_casa', 'gol_trasferta', 'gol_casa_1t', 'gol_trasferta_1t', 
        'gol_casa_2t', 'gol_trasferta_2t', 'winner_code'
    ]].itertuples(index=False, name=None))
    
    # Usiamo executemany per un caricamento in blocco velocissimo
    cursor.executemany('''
        INSERT OR REPLACE INTO partite 
        (lega, giornata, squadra_casa, squadra_trasferta, 
         gol_casa, gol_trasferta, gol_casa_1t, gol_trasferta_1t,
         gol_casa_2t, gol_trasferta_2t, winner_code)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', data_to_insert)
    
    conn.commit()
    print(f"Salvate/Aggiornate {len(df)} partite nel database.")

if __name__ == "__main__":
    # Imposta la directory di lavoro corrente
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    API_KEY = "8d80925a05b476b916b6a136371c0194" #  API key
    # Serie A, La Liga, Bundesliga, Ligue 1, Primeira Liga, Eredivisie
    LEAGUES = [135, 140, 78, 61, 94, 88] 
    SEASON = 2024 # Assicurati di impostare la stagione corretta (es. 2024 per 2024/2025)
    
    # Connessione al DB (se non esiste lo crea)
    conn = init_database('calcio.db')
    
    for league_id in LEAGUES:
        df_raw = fetch_and_process_league(league_id, SEASON, API_KEY)
        
        if not df_raw.empty:
            df_clean = optimize_and_calculate(df_raw)
            save_to_sqlite(df_clean, conn)
        else:
            print(f"Nessun dato per la lega {league_id}")
            
        # Pausa per rispettare i rate limit gratuiti (10 richieste/minuto su API-Football)
        time.sleep(7)
        
    conn.close()
    print("Processo di aggiornamento completato con successo!")