import json
import sqlite3
from datetime import datetime
import os

#commento prova
class CalcioDatabase:
    def __init__(self, db_path='calcio.db'):
        #iniziaiza db
        self.db_path = db_path
        self.conn = None
        self.init_database()
    
    def init_database(self):
        #connette a database e crea tabella se non esiste
        self.conn = sqlite3.connect(self.db_path)
        cursor = self.conn.cursor()
        
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
        
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_lega ON partite(lega)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_giornata ON partite(giornata)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_squadra_casa ON partite(squadra_casa)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_squadra_trasferta ON partite(squadra_trasferta)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_lega_giornata ON partite(lega, giornata)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_winner_code ON partite(winner_code)')
        
        self.conn.commit()
    
    def insert_partita(self, lega, giornata, squadra_casa, 
                       squadra_trasferta, gol_casa, gol_trasferta, 
                       gol_casa_1t, gol_trasferta_1t, winner_code):
        #inserisce o aggiorna partita
        cursor = self.conn.cursor()
        
        # Calcola gol 2T
        gol_casa_2t = gol_casa - gol_casa_1t if gol_casa_1t is not None else None
        gol_trasferta_2t = gol_trasferta - gol_trasferta_1t if gol_trasferta_1t is not None else None
        
        cursor.execute('''
            INSERT OR REPLACE INTO partite 
            (lega, giornata, squadra_casa, squadra_trasferta, 
             gol_casa, gol_trasferta, gol_casa_1t, gol_trasferta_1t,
             gol_casa_2t, gol_trasferta_2t, winner_code)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (lega, giornata, squadra_casa, squadra_trasferta,
              gol_casa, gol_trasferta, gol_casa_1t, gol_trasferta_1t,
              gol_casa_2t, gol_trasferta_2t, winner_code))
        
        self.conn.commit()
    
    def get_stats_by_lega(self):
        #raggrupa stats per lega
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT 
                lega,
                COUNT(*) as partite,
                MAX(giornata) as ultima_giornata
            FROM partite
            GROUP BY lega
            ORDER BY lega
        ''')
        return cursor.fetchall()
    
    def close(self):
        if self.conn:
            self.conn.close()


def process_json_files():
    #da file json a dati in db
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    db = CalcioDatabase()
    
    # Dizionario per tracciare le importazioni per lega
    importazioni = {}
    
    for round_num in range(1, 39):
        filename = f'round_{round_num}.json'
        
        if not os.path.exists(filename):
            continue
        
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if 'events' not in data or len(data['events']) == 0:
                continue
            
            lega = data['events'][0]['tournament']['name']
            
            if lega not in importazioni:
                importazioni[lega] = []
            
            partite_importate = 0
            
            for match in data['events']:
                # Salta partite posticipate o non iniziate
                status = match.get('status', {}).get('description', '')
                if status in ['Postponed', 'Not started']:
                    continue
                
                home_team = match.get('homeTeam', {}).get('name', 'Sconosciuto')
                away_team = match.get('awayTeam', {}).get('name', 'Sconosciuto')
                
                home_score = match.get('homeScore', {}).get('current')
                away_score = match.get('awayScore', {}).get('current')
                
                # Salta partite senza risultato
                if home_score is None or away_score is None:
                    continue
                
                # Estrai gol 1T
                home_score_1t = match.get('homeScore', {}).get('period1')
                away_score_1t = match.get('awayScore', {}).get('period1')
                
                # Winner code
                winner_code = match.get('winnerCode', 3)
                
                
                db.insert_partita(
                    lega=lega,
                    giornata=round_num,
                    squadra_casa=home_team,
                    squadra_trasferta=away_team,
                    gol_casa=home_score,
                    gol_trasferta=away_score,
                    gol_casa_1t=home_score_1t,
                    gol_trasferta_1t=away_score_1t,
                    winner_code=winner_code
                )
                partite_importate += 1
            
            if partite_importate > 0:
                importazioni[lega].append(round_num)
                print(f"Giornata {round_num:2d}: {partite_importate} partite")
            
        except Exception as e:
            print(f"Errore giornata {round_num}: {e}")
    
    
    db.close()


if __name__ == "__main__":
    process_json_files()