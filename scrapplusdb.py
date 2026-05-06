import sqlite3
import requests
import pandas as pd
import time
import os

def init_database(db_path='calcio.db'):
    """Crea il database e la tabella 'partite' se non esistono."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Creazione della tabella con la struttura corretta
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
    # NUOVA TABELLA per le partite future
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS calendario (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lega TEXT NOT NULL,
            giornata INTEGER NOT NULL,
            squadra_casa TEXT NOT NULL,
            squadra_trasferta TEXT NOT NULL,
            data_ora TEXT,
            UNIQUE(lega, giornata, squadra_casa, squadra_trasferta)
        )
    ''')
    
    # Creazione indici per velocizzare la dashboard
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_lega ON partite(lega)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_giornata ON partite(giornata)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_squadra_casa ON partite(squadra_casa)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_squadra_trasferta ON partite(squadra_trasferta)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_lega_giornata ON partite(lega, giornata)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_winner_code ON partite(winner_code)')
    
    conn.commit()
    return conn

def fetch_and_process_league(league_code, api_key):
    """Scarica i dati da Football-Data.org."""
    url = f"https://api.football-data.org/v4/competitions/{league_code}/matches"
    headers = { 'X-Auth-Token': api_key }
    
    print(f"Scaricamento dati per la lega {league_code}...")
    try:
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            print(f"❌ Errore API {response.status_code}")
            return pd.DataFrame()
            
        data = response.json()
        matches = data.get('matches', [])
        risultati = []
        futuribili = []
      
        for match in matches:
            # LOGICA PER RISULTATI (Partite finite)
            if match['status'] == 'FINISHED':
                risultati.append({
                    'lega': data['competition']['name'],
                    'giornata': match['matchday'],
                    'squadra_casa': match['homeTeam']['shortName'] or match['homeTeam']['name'],
                    'squadra_trasferta': match['awayTeam']['shortName'] or match['awayTeam']['name'],
                    'gol_casa': match['score']['fullTime']['home'],
                    'gol_trasferta': match['score']['fullTime']['away'],
                    'gol_casa_1t': match['score']['halfTime']['home'],
                    'gol_trasferta_1t': match['score']['halfTime']['away']
            })

            # LOGICA PER CALENDARIO (Partite future)
            elif match['status'] in ['SCHEDULED', 'TIMED']:
                futuribili.append({
                    'lega': data['competition']['name'],
                    'giornata': match['matchday'],
                    'squadra_casa': match['homeTeam']['shortName'] or match['homeTeam']['name'],
                    'squadra_trasferta': match['awayTeam']['shortName'] or match['awayTeam']['name'],
                    'data_ora': match['utcDate']
            })
        return pd.DataFrame(risultati), pd.DataFrame(futuribili)
    except Exception as e:
        print(f"❌ Errore durante la chiamata: {e}")
        return pd.DataFrame()

def optimize_and_calculate(df):
    """Pulisce i dati e converte NaN in None per SQLite."""
    if df.empty: return df
    
    df['gol_casa_1t'] = pd.to_numeric(df['gol_casa_1t'], errors='coerce')
    df['gol_trasferta_1t'] = pd.to_numeric(df['gol_trasferta_1t'], errors='coerce')
    
    df['gol_casa_2t'] = df['gol_casa'] - df['gol_casa_1t']
    df['gol_trasferta_2t'] = df['gol_trasferta'] - df['gol_trasferta_1t']
    
    df['winner_code'] = 3
    df.loc[df['gol_casa'] > df['gol_trasferta'], 'winner_code'] = 1
    df.loc[df['gol_casa'] < df['gol_trasferta'], 'winner_code'] = 2
    
    df['giornata'] = pd.to_numeric(df['giornata'], errors='coerce').fillna(0).astype(int)
    
    # Fix critico per i valori nulli (NaN -> None)
    return df.where(pd.notnull(df), None)

def save_to_sqlite(df, conn):
    """Salvataggio massivo."""
    if df.empty: return
    
    colonne = ['lega', 'giornata', 'squadra_casa', 'squadra_trasferta', 
               'gol_casa', 'gol_trasferta', 'gol_casa_1t', 'gol_trasferta_1t', 
               'gol_casa_2t', 'gol_trasferta_2t', 'winner_code']
    
    data_to_insert = list(df[colonne].itertuples(index=False, name=None))
    cursor = conn.cursor()
    
    try:
        cursor.executemany(f'''
            INSERT OR REPLACE INTO partite ({", ".join(colonne)})
            VALUES ({", ".join(["?" for _ in colonne])})
        ''', data_to_insert)
        conn.commit()
        print(f"✅ Aggiornate {len(data_to_insert)} partite.")
    except Exception as e:
        print(f"❌ Errore DB: {e}")

def save_calendario_to_sqlite(df, conn):
    """Salva le partite future nella tabella calendario."""
    if df.empty: return
    
    colonne = ['lega', 'giornata', 'squadra_casa', 'squadra_trasferta', 'data_ora']
    data_to_insert = list(df[colonne].itertuples(index=False, name=None))
    cursor = conn.cursor()
    
    try:
        cursor.executemany(f'''
            INSERT OR REPLACE INTO calendario ({", ".join(colonne)})
            VALUES ({", ".join(["?" for _ in colonne])})
        ''', data_to_insert)
        conn.commit()
        print(f"📅 Inserite/Aggiornate {len(data_to_insert)} partite nel calendario.")
    except Exception as e:
        print(f"❌ Errore DB Calendario: {e}")

if __name__ == "__main__":
    API_KEY = "c4bdfa76ae97456daa5038d8f85f8f59"
    # SA=SerieA, PD=LaLiga, BL1=Bundesliga, FL1=Ligue1, PPL=LigaPortugal, DED=Eredivisie
    LEAGUES = ['SA', 'PD', 'BL1', 'FL1', 'PPL', 'DED']
    
    # Inizializza il DB e crea la tabella se manca
    connection = init_database('calcio.db')
    
    for code in LEAGUES:
        df_risultati, df_calendario = fetch_and_process_league(code, API_KEY)
        
        if not df_risultati.empty:
            df_clean = optimize_and_calculate(df_risultati)
            save_to_sqlite(df_clean, connection)
            
        if not df_calendario.empty:
            save_calendario_to_sqlite(df_calendario, connection)
        
        time.sleep(6.5) # Rispetta il limite di 10 chiamate/min
        
    connection.close()
    print("Aggiornamento terminato!")