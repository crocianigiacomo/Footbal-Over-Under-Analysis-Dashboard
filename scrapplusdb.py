import sqlite3, os, time, asyncio
import aiohttp
import pandas as pd
from dotenv import load_dotenv

load_dotenv() 

LEAGUE_FLAGS = {
    'SA':  'Serie A',
    'PL': 'Premier League',
    'PD':  'La Liga',
    'BL1': 'Bundesliga',
    'FL1': 'Ligue 1',
    'PPL': 'Liga Portugal',
    'DED': 'Eredivisie'
}

# ──────────────────────────────────────────────
#  1. OTTIMIZZAZIONE DATABASE (WAL MODE)
# ──────────────────────────────────────────────
def init_database(db_path='calcio.db'):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Attiviamo il WAL per permettere alla Dashboard di leggere 
    # mentre questo script sta scrivendo, senza lock!
    cursor.execute('PRAGMA journal_mode=WAL;')
    cursor.execute('PRAGMA synchronous=NORMAL;')

    # Nuova tabella per i parametri delle leghe
    cursor.execute('''CREATE TABLE IF NOT EXISTS parametri_leghe (
        lega TEXT PRIMARY KEY,
        alpha REAL,
        ultima_calibrazione TEXT)''')
    
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

# ──────────────────────────────────────────────
#  2. IL RATE LIMITER (IL "VIGILE URBANO")
# ──────────────────────────────────────────────
class APIRateLimiter:
    """Garantisce di non superare max_calls nel periodo indicato (in secondi)."""
    def __init__(self, max_calls: int, period: float):
        self.max_calls = max_calls
        self.period = period
        self.timestamps = []
        self.lock = None

    async def _get_lock(self):
        if self.lock is None:
            self.lock = asyncio.Lock()
        return self.lock

    async def wait(self):
        async with await self._get_lock():
            now = time.monotonic()
            # Eliminiamo lo storico delle chiamate più vecchie del nostro periodo (es. 60 sec)
            self.timestamps = [t for t in self.timestamps if now - t < self.period]
            
            if len(self.timestamps) >= self.max_calls:
                # Calcoliamo quanto manca prima che si "liberi" uno slot
                sleep_time = self.period - (now - self.timestamps[0])
                if sleep_time > 0:
                    print(f"[THROTTLE] Limite API raggiunto. Attendo {sleep_time:.1f} sec...")
                    await asyncio.sleep(sleep_time)
                # Aggiorniamo il timestamp corrente dopo aver riposato
                now = time.monotonic()
                self.timestamps = [t for t in self.timestamps if now - t < self.period]
            
            self.timestamps.append(now)

def _get_name(team: dict) -> str:
    return team['shortName'] if team.get('shortName') else team['name']

# ──────────────────────────────────────────────
#  3. FETCH ASINCRONO
# ──────────────────────────────────────────────
async def fetch_league_data(session: aiohttp.ClientSession, league_code: str, api_key: str, limiter: APIRateLimiter):
    url = f"https://api.football-data.org/v4/competitions/{league_code}/matches"
    headers = {'X-Auth-Token': api_key}
    
    # Prima di sparare la richiesta, chiediamo il permesso al Rate Limiter
    await limiter.wait()
    
    print(f"[INFO] Fetching {LEAGUE_FLAGS[league_code]}...")
    try:
        async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as response:
            response.raise_for_status()
            data = await response.json()
            
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

            return league_code, pd.DataFrame(risultati), pd.DataFrame(futuribili)

    except asyncio.TimeoutError:
        print(f"[TIMEOUT] {league_code}: il server non ha risposto in tempo.")
    except aiohttp.ClientResponseError as e:
        print(f"[HTTP ERROR] {league_code}: {e.status} - {e.message}")
    except Exception as e:
        print(f"[ERROR] {league_code}: {e}")
        
    return league_code, pd.DataFrame(), pd.DataFrame()


def optimize_and_calculate(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty: return df
    df[['gol_casa_1t', 'gol_trasferta_1t']] = df[['gol_casa_1t', 'gol_trasferta_1t']].apply(pd.to_numeric, errors='coerce')
    df['gol_casa_2t']      = df['gol_casa']      - df['gol_casa_1t']
    df['gol_trasferta_2t'] = df['gol_trasferta'] - df['gol_trasferta_1t']
    df['winner_code'] = 3
    df.loc[df['gol_casa'] > df['gol_trasferta'], 'winner_code'] = 1
    df.loc[df['gol_casa'] < df['gol_trasferta'], 'winner_code'] = 2
    return df.where(pd.notnull(df), None)

def save_to_sqlite(df: pd.DataFrame, conn, table: str):
    if df.empty: return
    cursor = conn.cursor()
    cols = ", ".join(df.columns)
    placeholders = ", ".join(["?"] * len(df.columns))
    cursor.executemany(f"INSERT OR REPLACE INTO {table} ({cols}) VALUES ({placeholders})", [tuple(x) for x in df.values])
    conn.commit()

# ──────────────────────────────────────────────
#  4. ORCHESTRATORE ASINCRONO PRINCIPALE
# ──────────────────────────────────────────────
async def main():
    API_KEY = os.getenv("FOOTBALL_API_KEY")
    if not API_KEY:
        raise EnvironmentError("API key non trovata. Assicurati di avere un file .env con FOOTBALL_API_KEY=<la_tua_chiave>")

    # Inizializziamo il limitatore: max 10 chiamate ogni 60 secondi
    limiter = APIRateLimiter(max_calls=10, period=60.0)
    
    start_time = time.time()
    all_risultati = []
    all_calendario = []

    # Creiamo una sessione HTTP persistente (molto più veloce di requests.get!)
    async with aiohttp.ClientSession() as session:
        # Prepariamo la lista dei task da lanciare in parallelo
        tasks = [fetch_league_data(session, code, API_KEY, limiter) for code in LEAGUE_FLAGS.keys()]
        
        # Lanciamo tutti i task in contemporanea e aspettiamo che finiscano
        results = await asyncio.gather(*tasks)
        
        # Raccogliamo i risultati
        for league_code, res_df, cal_df in results:
            if not res_df.empty:
                all_risultati.append(optimize_and_calculate(res_df))
            if not cal_df.empty:
                all_calendario.append(cal_df)

    # Salvataggio su DB: facciamolo alla fine, tutto insieme, in modo velocissimo
    print("[INFO] Salvataggio sul Database in corso...")
    connection = init_database('calcio.db')
    
    if all_risultati:
        final_res = pd.concat(all_risultati, ignore_index=True)
        save_to_sqlite(final_res, connection, 'partite')
        
    if all_calendario:
        final_cal = pd.concat(all_calendario, ignore_index=True)
        connection.execute("DELETE FROM calendario")
        save_to_sqlite(final_cal, connection, 'calendario')

    connection.close()

    print("[INFO] Calibrazione parametri Alpha per ogni lega...")
    from stats_engine import calibrate_alpha
    from datetime import datetime
    
    conn_params = init_database('calcio.db')
    cursor = conn_params.cursor()
    
    for lega in LEAGUE_FLAGS.values():
        df_lega = pd.read_sql("SELECT * FROM partite WHERE lega = ?", conn_params, params=(lega,))
        
        if not df_lega.empty:
            new_alpha = calibrate_alpha(df_lega)
            cursor.execute('''INSERT OR REPLACE INTO parametri_leghe 
                            (lega, alpha, ultima_calibrazione) VALUES (?, ?, ?)''',
                         (lega, new_alpha, datetime.now().strftime("%Y-%m-%d %H:%M")))
            print(f"   > {lega}: Alpha impostato a {new_alpha}")
            
    conn_params.commit()
    conn_params.close()
    
    elapsed = time.time() - start_time
    print(f"✅ DB Aggiornato con successo in {elapsed:.2f} secondi!")

if __name__ == "__main__":
    # Avvia l'event loop di asyncio
    asyncio.run(main())