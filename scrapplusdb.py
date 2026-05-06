import sqlite3, requests, time, os
import pandas as pd

# Mappatura definitiva con Emoji e Nomi richiesti
LEAGUE_FLAGS = {
    'SA': 'Serie A',
    'PD': 'La Liga',
    'BL1': 'Bundesliga',
    'FL1': 'Ligue 1',
    'PPL': 'Liga Portugal',
    'DED': 'Eredivisie'
}

def init_database(db_path='calcio.db'):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS partite (
        id INTEGER PRIMARY KEY AUTOINCREMENT, lega TEXT, giornata INTEGER,
        squadra_casa TEXT, squadra_trasferta TEXT, gol_casa INTEGER, gol_trasferta INTEGER,
        gol_casa_1t INTEGER, gol_trasferta_1t INTEGER, gol_casa_2t INTEGER, gol_trasferta_2t INTEGER,
        winner_code INTEGER, UNIQUE(lega, giornata, squadra_casa, squadra_trasferta))''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS calendario (
        id INTEGER PRIMARY KEY AUTOINCREMENT, lega TEXT, giornata INTEGER,
        squadra_casa TEXT, squadra_trasferta TEXT, data_ora TEXT,
        UNIQUE(lega, giornata, squadra_casa, squadra_trasferta))''')
    conn.commit()
    return conn

def fetch_and_process_league(league_code, api_key):
    url = f"https://api.football-data.org/v4/competitions/{league_code}/matches"
    headers = { 'X-Auth-Token': api_key }
    try:
        response = requests.get(url, headers=headers)
        if response.status_code != 200: return pd.DataFrame(), pd.DataFrame()
        data = response.json()
        lega_nome = LEAGUE_FLAGS.get(league_code, data['competition']['name'])
        risultati, futuribili = [], []
        for m in data.get('matches', []):
            if m['status'] == 'FINISHED':
                risultati.append({
                    'lega': lega_nome, 'giornata': m['matchday'],
                    'squadra_casa': m['homeTeam']['shortName'] or m['homeTeam']['name'],
                    'squadra_trasferta': m['awayTeam']['shortName'] or m['awayTeam']['name'],
                    'gol_casa': m['score']['fullTime']['home'], 'gol_trasferta': m['score']['fullTime']['away'],
                    'gol_casa_1t': m['score']['halfTime']['home'], 'gol_trasferta_1t': m['score']['halfTime']['away']
                })
            elif m['status'] in ['SCHEDULED', 'TIMED']:
                futuribili.append({
                    'lega': lega_nome, 'giornata': m['matchday'],
                    'squadra_casa': m['homeTeam']['shortName'] or m['homeTeam']['name'],
                    'squadra_trasferta': m['awayTeam']['shortName'] or m['awayTeam']['name'],
                    'data_ora': m['utcDate']
                })
        return pd.DataFrame(risultati), pd.DataFrame(futuribili)
    except: return pd.DataFrame(), pd.DataFrame()

def optimize_and_calculate(df):
    if df.empty: return df
    df[['gol_casa_1t', 'gol_trasferta_1t']] = df[['gol_casa_1t', 'gol_trasferta_1t']].apply(pd.to_numeric, errors='coerce')
    df['gol_casa_2t'], df['gol_trasferta_2t'] = df['gol_casa'] - df['gol_casa_1t'], df['gol_trasferta'] - df['gol_trasferta_1t']
    df['winner_code'] = 3
    df.loc[df['gol_casa'] > df['gol_trasferta'], 'winner_code'] = 1
    df.loc[df['gol_casa'] < df['gol_trasferta'], 'winner_code'] = 2
    return df.where(pd.notnull(df), None)

def save_to_sqlite(df, conn, table):
    if df.empty: return
    cursor = conn.cursor()
    cols = ", ".join(df.columns)
    placeholders = ", ".join(["?"] * len(df.columns))
    cursor.executemany(f"INSERT OR REPLACE INTO {table} ({cols}) VALUES ({placeholders})", [tuple(x) for x in df.values])
    conn.commit()

if __name__ == "__main__":
    API_KEY = "c4bdfa76ae97456daa5038d8f85f8f59" 
    connection = init_database('calcio.db')
    for code in LEAGUE_FLAGS.keys():
        res, cal = fetch_and_process_league(code, API_KEY)
        if not res.empty: save_to_sqlite(optimize_and_calculate(res), connection, 'partite')
        if not cal.empty: save_to_sqlite(cal, connection, 'calendario')
        time.sleep(1)  # Evita di sovraccaricare l'API
    connection.close()
    print("DB Aggiornato!")