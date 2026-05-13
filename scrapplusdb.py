import sqlite3, os, time, asyncio
import aiohttp
import pandas as pd
from dotenv import load_dotenv
from datetime import datetime
from stats_engine import calibrate_alpha
import query

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
    
    cursor.execute('PRAGMA journal_mode=WAL;')
    cursor.execute('PRAGMA synchronous=NORMAL;')

    cursor.execute('''CREATE TABLE IF NOT EXISTS parametri_leghe (
        lega TEXT PRIMARY KEY,
        alpha REAL,
        giornata_target INTEGER,
        ultima_calibrazione TEXT)''')
    
    # Controllo esplicito della colonna giornata_target
    cursor.execute("PRAGMA table_info(parametri_leghe)")
    colonne = [info[1] for info in cursor.fetchall()]
    
    if 'giornata_target' not in colonne:
        print("[DB] Migrazione: Aggiunta colonna giornata_target a parametri_leghe")
        cursor.execute("ALTER TABLE parametri_leghe ADD COLUMN giornata_target INTEGER DEFAULT 1")
    
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
#  2. IL RATE LIMITER
# ──────────────────────────────────────────────
class APIRateLimiter:
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
            self.timestamps = [t for t in self.timestamps if now - t < self.period]
            
            if len(self.timestamps) >= self.max_calls:
                sleep_time = self.period - (now - self.timestamps[0])
                if sleep_time > 0:
                    print(f"[THROTTLE] Limite API raggiunto. Attendo {sleep_time:.1f} sec...")
                    await asyncio.sleep(sleep_time)
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

            return league_code, lega_nome, pd.DataFrame(risultati), pd.DataFrame(futuribili)

    except Exception as e:
        print(f"[ERROR] {league_code}: {e}")
        
    return league_code, LEAGUE_FLAGS.get(league_code, league_code), pd.DataFrame(), pd.DataFrame()


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
#  4. ORCHESTRATORE ASINCRONO E LOGICA GT
# ──────────────────────────────────────────────
async def main():
    API_KEY = os.getenv("FOOTBALL_API_KEY")
    if not API_KEY:
        raise EnvironmentError("API key non trovata. Assicurati di avere un file .env con FOOTBALL_API_KEY=<la_tua_chiave>")

    limiter = APIRateLimiter(max_calls=10, period=60.0)
    start_time = time.time()
    
    all_risultati = []
    all_calendario_filtrato = []
    
    # Mappa per salvare la GT calcolata per ogni lega
    mappa_gt_leghe = {}

    async with aiohttp.ClientSession() as session:
        tasks = [fetch_league_data(session, code, API_KEY, limiter) for code in LEAGUE_FLAGS.keys()]
        results = await asyncio.gather(*tasks)
        
        for league_code, lega_nome, res_df, cal_df in results:
            if not res_df.empty:
                all_risultati.append(optimize_and_calculate(res_df))
                
            # --- LOGICA GIORNATA TARGET (GT) ---
            ga = int(res_df['giornata'].max()) if not res_df.empty else 0
            
            if not cal_df.empty:
                # Controlliamo se ci sono ancora partite della GA da giocare nel calendario
                if ga in cal_df['giornata'].values:
                    gt = ga
                else:
                    gt = ga + 1
                    
                # Conserviamo in memoria la GT di questa lega per salvarla dopo
                mappa_gt_leghe[lega_nome] = gt
                
                # Tagliamo via il futuro remoto: teniamo solo le partite fino alla GT
                cal_df_pulito = cal_df[cal_df['giornata'] <= gt].copy()
                all_calendario_filtrato.append(cal_df_pulito)
            else:
                mappa_gt_leghe[lega_nome] = ga # Fine campionato
                
    # Salvataggio su DB
    print("[INFO] Salvataggio sul Database in corso...")
    connection = init_database('calcio.db')
    
    if all_risultati:
        final_res = pd.concat(all_risultati, ignore_index=True)
        save_to_sqlite(final_res, connection, 'partite')
        
    if all_calendario_filtrato:
        final_cal = pd.concat(all_calendario_filtrato, ignore_index=True)

        # 1. Inserisce le nuove partite o aggiorna le date (upsert)
        save_to_sqlite(final_cal, connection, 'calendario')
        
        # 2. Pulisce la tabella rimuovendo i vecchi match tramite query centralizzata
        connection.execute(query.CLEANUP_CALENDARIO_SQL)

    print("[INFO] Calibrazione parametri Alpha e Aggiornamento GT...")
    
    cursor = connection.cursor()
    
    for lega_nome in LEAGUE_FLAGS.values():
        df_lega = pd.read_sql("SELECT * FROM partite WHERE lega = ?", connection, params=(lega_nome,))
        
        if not df_lega.empty:
            new_alpha = calibrate_alpha(df_lega)
            gt_corrente = mappa_gt_leghe.get(lega_nome, 1)
            
            cursor.execute('''INSERT OR REPLACE INTO parametri_leghe 
                            (lega, alpha, giornata_target, ultima_calibrazione) VALUES (?, ?, ?, ?)''',
                         (lega_nome, new_alpha, gt_corrente, datetime.now().strftime("%Y-%m-%d %H:%M")))
            print(f"   > {lega_nome}: Alpha={new_alpha} | GT={gt_corrente}")
            
    connection.commit()
    connection.close()
    
    elapsed = time.time() - start_time
    print(f"✅ DB Aggiornato con successo in {elapsed:.2f} secondi!")

if __name__ == "__main__":
    asyncio.run(main())
