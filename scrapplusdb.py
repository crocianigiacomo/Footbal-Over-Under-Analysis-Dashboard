import sqlite3, requests, time, os
import pandas as pd
from dotenv import load_dotenv

load_dotenv() 

LEAGUE_FLAGS = {
    'SA':  'Serie A',
    'PD':  'La Liga',
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
        winner_code INTEGER,
        UNIQUE(lega, giornata, squadra_casa, squadra_trasferta))''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS calendario (
        id INTEGER PRIMARY KEY AUTOINCREMENT, lega TEXT, giornata INTEGER,
        squadra_casa TEXT, squadra_trasferta TEXT, data_ora TEXT,
        UNIQUE(lega, giornata, squadra_casa, squadra_trasferta))''')
    conn.commit()
    return conn


def _get_name(team: dict) -> str:
    """Restituisce shortName se presente, altrimenti name."""
    return team['shortName'] if team.get('shortName') else team['name']


def fetch_and_process_league(league_code: str, api_key: str):
    url = f"https://api.football-data.org/v4/competitions/{league_code}/matches"
    headers = {'X-Auth-Token': api_key}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        lega_nome = LEAGUE_FLAGS.get(league_code, data['competition']['name'])
        risultati, futuribili = [], []

        for m in data.get('matches', []):
            if m['status'] == 'FINISHED':
                risultati.append({
                    'lega':              lega_nome,
                    'giornata':          m['matchday'],
                    'squadra_casa':      _get_name(m['homeTeam']),
                    'squadra_trasferta': _get_name(m['awayTeam']),
                    'gol_casa':          m['score']['fullTime']['home'],
                    'gol_trasferta':     m['score']['fullTime']['away'],
                    'gol_casa_1t':       m['score']['halfTime']['home'],
                    'gol_trasferta_1t':  m['score']['halfTime']['away'],
                })
            elif m['status'] in ['SCHEDULED', 'TIMED']:
                futuribili.append({
                    'lega':              lega_nome,
                    'giornata':          m['matchday'],
                    'squadra_casa':      _get_name(m['homeTeam']),
                    'squadra_trasferta': _get_name(m['awayTeam']),
                    'data_ora':          m['utcDate'],
                })

        return pd.DataFrame(risultati), pd.DataFrame(futuribili)

    except requests.exceptions.Timeout:
        print(f"[TIMEOUT] {league_code}: il server non ha risposto in tempo.")
        return pd.DataFrame(), pd.DataFrame()
    except requests.exceptions.HTTPError as e:
        print(f"[HTTP ERROR] {league_code}: {e.response.status_code} - {e}")
        return pd.DataFrame(), pd.DataFrame()
    except requests.exceptions.RequestException as e:
        print(f"[NETWORK ERROR] {league_code}: {e}")
        return pd.DataFrame(), pd.DataFrame()
    except (KeyError, ValueError) as e:
        print(f"[PARSE ERROR] {league_code}: struttura risposta inattesa - {e}")
        return pd.DataFrame(), pd.DataFrame()


def optimize_and_calculate(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    df[['gol_casa_1t', 'gol_trasferta_1t']] = df[['gol_casa_1t', 'gol_trasferta_1t']].apply(
        pd.to_numeric, errors='coerce'
    )
    df['gol_casa_2t']      = df['gol_casa']      - df['gol_casa_1t']
    df['gol_trasferta_2t'] = df['gol_trasferta'] - df['gol_trasferta_1t']

    # winner_code: 1=casa, 2=trasferta, 3=pareggio
    df['winner_code'] = 3
    df.loc[df['gol_casa'] > df['gol_trasferta'], 'winner_code'] = 1
    df.loc[df['gol_casa'] < df['gol_trasferta'], 'winner_code'] = 2

    return df.where(pd.notnull(df), None)


def save_to_sqlite(df: pd.DataFrame, conn, table: str):
    if df.empty:
        return
    cursor = conn.cursor()
    cols         = ", ".join(df.columns)
    placeholders = ", ".join(["?"] * len(df.columns))
    cursor.executemany(
        f"INSERT OR REPLACE INTO {table} ({cols}) VALUES ({placeholders})",
        [tuple(x) for x in df.values]
    )
    conn.commit()


if __name__ == "__main__":
    API_KEY = os.getenv("FOOTBALL_API_KEY")
    if not API_KEY:
        raise EnvironmentError(
            "API key non trovata. Assicurati di avere un file .env con FOOTBALL_API_KEY=<la_tua_chiave>"
        )

    connection = init_database('calcio.db')
    for code in LEAGUE_FLAGS.keys():
        print(f"[INFO] Fetching {LEAGUE_FLAGS[code]}...")
        res, cal = fetch_and_process_league(code, API_KEY)
        if not res.empty:
            save_to_sqlite(optimize_and_calculate(res), connection, 'partite')
        if not cal.empty:
            save_to_sqlite(cal, connection, 'calendario')
        time.sleep(1) 

    connection.close()
    print("DB Aggiornato!")