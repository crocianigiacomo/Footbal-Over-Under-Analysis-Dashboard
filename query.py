import sqlite3
import pandas as pd

class StatsQuery:
    def __init__(self, db_path='calcio.db'):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
    
    def get_leghe_disponibili(self):
        #lista leghe
        query = "SELECT DISTINCT lega FROM partite ORDER BY lega"
        cursor = self.conn.cursor()
        cursor.execute(query)
        return [row[0] for row in cursor.fetchall()]
    
    def statistiche_over3(self, lega=None):
        #query partite over 2.5
        where_clause = f"WHERE lega = '{lega}'" if lega else ""
        
        query = f'''
            WITH squadre_partite AS (
                SELECT lega, squadra_casa AS squadra, COUNT(*) as partite_over3
                FROM partite
                {where_clause} AND (gol_casa + gol_trasferta) >= 3
                GROUP BY lega, squadra_casa
                UNION ALL
                SELECT lega, squadra_trasferta AS squadra, COUNT(*) as partite_over3
                FROM partite
                {where_clause} AND (gol_casa + gol_trasferta) >= 3
                GROUP BY lega, squadra_trasferta
            ),
            gol_stats AS (
                SELECT 
                    lega,
                    squadra,
                    SUM(partite_over3) as totale_partite_over3
                FROM squadre_partite
                GROUP BY lega, squadra
            ),
            gol_fatti_subiti AS (
                SELECT 
                    lega,
                    squadra_casa AS squadra,
                    SUM(gol_casa) as gol_fatti,
                    SUM(gol_trasferta) as gol_subiti
                FROM partite
                {where_clause}
                GROUP BY lega, squadra_casa
                UNION ALL
                SELECT 
                    lega,
                    squadra_trasferta AS squadra,
                    SUM(gol_trasferta) as gol_fatti,
                    SUM(gol_casa) as gol_subiti
                FROM partite
                {where_clause}
                GROUP BY lega, squadra_trasferta
            ),
            totali AS (
                SELECT 
                    lega,
                    squadra,
                    SUM(gol_fatti) as gol_fatti,
                    SUM(gol_subiti) as gol_subiti
                FROM gol_fatti_subiti
                GROUP BY lega, squadra
            )
            SELECT 
                g.lega as "Lega",
                g.squadra as "Squadra",
                g.totale_partite_over3 as "Over 2.5",
                COALESCE(t.gol_fatti, 0) as "Gol Fatti",
                COALESCE(t.gol_subiti, 0) as "Gol Subiti"
            FROM gol_stats g
            LEFT JOIN totali t ON g.squadra = t.squadra AND g.lega = t.lega
            ORDER BY g.lega, g.totale_partite_over3 DESC
        '''
        
        df = pd.read_sql_query(query, self.conn)
        return df
    
    def confronto_leghe(self):

        query = '''
            SELECT 
                lega as "Lega",
                COUNT(*) as "Partite",
                ROUND(AVG(gol_casa + gol_trasferta), 2) as "Media Gol",
                SUM(CASE WHEN (gol_casa + gol_trasferta) >= 3 THEN 1 ELSE 0 END) as "Over 2.5",
                ROUND(100.0 * SUM(CASE WHEN (gol_casa + gol_trasferta) >= 3 THEN 1 ELSE 0 END) / COUNT(*), 1) as "% Over 2.5",
                MAX(gol_casa + gol_trasferta) as "Max Gol",
                MIN(giornata) as "Prima Giornata",
                MAX(giornata) as "Ultima Giornata"
            FROM partite
            GROUP BY lega
            ORDER BY "% Over 2.5" DESC
        '''
        
        df = pd.read_sql_query(query, self.conn)
        return df
    
    def statistiche_halftime(self, lega):
        
        query = '''
            SELECT 
                squadra_casa as "Squadra",
                COUNT(*) as "Partite",
                ROUND(AVG(gol_casa_1t + gol_trasferta_1t), 2) as "Media Gol 1T",
                SUM(CASE WHEN (gol_casa_1t + gol_trasferta_1t) >= 2 THEN 1 ELSE 0 END) as "Over 1.5 HT",
                SUM(CASE WHEN gol_casa_1t > 0 AND gol_trasferta_1t > 0 THEN 1 ELSE 0 END) as "GG HT"
            FROM partite
            WHERE lega = ? AND gol_casa_1t IS NOT NULL
            GROUP BY squadra_casa
            ORDER BY "Media Gol 1T" DESC
        '''
        
        df = pd.read_sql_query(query, self.conn, params=(lega,))
        return df
    
    def media_gol_per_giornata(self, lega):
       
        query = '''
            SELECT 
                giornata as "Giornata",
                ROUND(AVG(gol_casa + gol_trasferta), 2) as "Media Gol",
                COUNT(*) as "Partite",
                SUM(CASE WHEN (gol_casa + gol_trasferta) >= 3 THEN 1 ELSE 0 END) as "Over 2.5"
            FROM partite
            WHERE lega = ?
            GROUP BY giornata
            ORDER BY giornata
        '''
        
        df = pd.read_sql_query(query, self.conn, params=(lega,))
        return df
    
    def squadre_gol_casa_trasferta(self, lega):
       
        query = '''
            WITH casa AS (
                SELECT 
                    squadra_casa as squadra,
                    AVG(gol_casa) as media_gol_casa,
                    SUM(gol_casa) as totale_gol_casa,
                    COUNT(*) as partite_casa
                FROM partite
                WHERE lega = ?
                GROUP BY squadra_casa
            ),
            trasferta AS (
                SELECT 
                    squadra_trasferta as squadra,
                    AVG(gol_trasferta) as media_gol_trasferta,
                    SUM(gol_trasferta) as totale_gol_trasferta,
                    COUNT(*) as partite_trasferta
                FROM partite
                WHERE lega = ?
                GROUP BY squadra_trasferta
            )
            SELECT 
                c.squadra as "Squadra",
                ROUND(c.media_gol_casa, 2) as "Media Casa",
                c.totale_gol_casa as "Tot Casa",
                ROUND(t.media_gol_trasferta, 2) as "Media Trasf",
                t.totale_gol_trasferta as "Tot Trasf",
                (c.totale_gol_casa + t.totale_gol_trasferta) as "Tot Generale"
            FROM casa c
            JOIN trasferta t ON c.squadra = t.squadra
            ORDER BY "Tot Generale" DESC
        '''
        
        df = pd.read_sql_query(query, self.conn, params=(lega, lega))
        return df
    
    def top_squadre_over_cross_lega(self, limit=20):
       
        query = '''
            WITH partite_squadra AS (
                -- Partite in casa
                SELECT 
                    lega,
                    squadra_casa AS squadra,
                    CASE WHEN (gol_casa + gol_trasferta) >= 3 THEN 1 ELSE 0 END as is_over,
                    1 as partita
                FROM partite
                UNION ALL
                -- Partite in trasferta
                SELECT 
                    lega,
                    squadra_trasferta AS squadra,
                    CASE WHEN (gol_casa + gol_trasferta) >= 3 THEN 1 ELSE 0 END as is_over,
                    1 as partita
                FROM partite
            )
            SELECT 
                lega as "Lega",
                squadra as "Squadra",
                SUM(is_over) as "Over 2.5",
                SUM(partita) as "Partite",
                ROUND(100.0 * SUM(is_over) / SUM(partita), 1) as "% Over"
            FROM partite_squadra
            GROUP BY lega, squadra
            ORDER BY "% Over" DESC
            LIMIT ?
        '''
    
        df = pd.read_sql_query(query, self.conn, params=(limit,))
        return df
    
    def top_squadre_under_cross_lega(self, limit=20):
        
        query = '''
            WITH partite_squadra AS (
                -- Partite in casa
                SELECT 
                    lega,
                    squadra_casa AS squadra,
                    CASE WHEN (gol_casa + gol_trasferta) <= 3 THEN 1 ELSE 0 END as is_under,
                    1 as partita
                FROM partite
                UNION ALL
                -- Partite in trasferta
                SELECT 
                    lega,
                    squadra_trasferta AS squadra,
                    CASE WHEN (gol_casa + gol_trasferta) <= 3 THEN 1 ELSE 0 END as is_under,
                    1 as partita
                FROM partite
            )
            SELECT 
                lega as "Lega",
                squadra as "Squadra",
                SUM(is_under) as "Under 3.5",
                SUM(partita) as "Partite",
                ROUND(100.0 * SUM(is_under) / SUM(partita), 1) as "% Under"
            FROM partite_squadra
            GROUP BY lega, squadra
            ORDER BY "% Under" DESC
            LIMIT ?
        '''
    
        df = pd.read_sql_query(query, self.conn, params=(limit,))
        return df
    def statistiche_gol(self, lega):
        
        query = '''
            WITH casa AS (
                SELECT
                    squadra_casa AS squadra,
                    SUM(gol_casa) AS gol_fatti,
                    SUM(gol_trasferta) AS gol_subiti
                FROM partite
                WHERE lega = ? AND gol_casa IS NOT NULL
                GROUP BY squadra_casa
            ),
            trasferta AS (
                SELECT
                    squadra_trasferta AS squadra,
                    SUM(gol_trasferta) AS gol_fatti,
                    SUM(gol_casa) AS gol_subiti
                FROM partite
                WHERE lega = ? AND gol_trasferta IS NOT NULL
                GROUP BY squadra_trasferta
            )
            SELECT
                squadra AS "Squadra",
                SUM(gol_fatti) AS "Gol Fatti",
                SUM(gol_subiti) AS "Gol Subiti"
            FROM (SELECT * FROM casa UNION ALL SELECT * FROM trasferta)
            GROUP BY squadra
            ORDER BY "Gol Fatti" DESC
        '''
        df = pd.read_sql_query(query, self.conn, params=(lega, lega))
        return df

    def close(self):
        self.conn.close()


def menu_interattivo():
    
    stats = StatsQuery()
    
    while True:
        print("\n" + "-"*30, flush=True)
        print("             MENU")
        print("-"*30)
        print("1. Confronto tra leghe")
        print("2. Statistiche Over 2.5 per lega")
        print("3. Media gol per giornata")
        print("4. Gol Casa vs Trasferta")
        print("5. Top 20 squadre Over 2.5 (tutte le leghe)")
        print("6. Statistiche Primo Tempo (HT)")
        print("7. Top 20 squadre Under 3.5 (tutte le leghe)")
        print("8. Statistiche gol fatti/gol subiti")
        print("0. Esci")
        
        scelta = input("\nScegli opzione: ").strip()
        
        if scelta == "0":
            print("Arrivederci!")
            break
        
        elif scelta == "1":
            print("\n" + "="*60)
            print("CONFRONTO TRA LEGHE")
            print("="*60)
            print(stats.confronto_leghe().to_string(index=False))
        
        elif scelta == "2":
            leghe = stats.get_leghe_disponibili()
            print(f"\nLeghe disponibili: {', '.join(leghe)}")
            lega = input("Scegli lega (o INVIO per tutte): ").strip()
            
            if lega and lega in leghe:
                df = stats.statistiche_over3(lega)
                df = df[df['Lega'] == lega].drop('Lega', axis=1)
            else:
                df = stats.statistiche_over3()
            
            print("\n" + "="*60)
            print("STATISTICHE OVER 2.5")
            print("="*60)
            print(df.to_string(index=False))
        
        elif scelta == "3":
            leghe = stats.get_leghe_disponibili()
            print(f"\nLeghe disponibili: {', '.join(leghe)}")
            lega = input("Scegli lega: ").strip()
            
            if lega in leghe:
                print("\n" + "="*60)
                print(f"MEDIA GOL PER GIORNATA - {lega}")
                print("="*60)
                print(stats.media_gol_per_giornata(lega).to_string(index=False))
            else:
                print("Lega non valida")
        
        elif scelta == "4":
            leghe = stats.get_leghe_disponibili()
            print(f"\nLeghe disponibili: {', '.join(leghe)}")
            lega = input("Scegli lega: ").strip()
            
            if lega in leghe:
                print("\n" + "="*60)
                print(f"GOL CASA VS TRASFERTA - {lega}")
                print("="*60)
                print(stats.squadre_gol_casa_trasferta(lega).to_string(index=False))
            else:
                print("❌ Lega non valida")
        
        elif scelta == "5":
            print("\n" + "="*60)
            print("TOP 20 SQUADRE OVER 2.5 (TUTTE LE LEGHE)")
            print("="*60)
            print(stats.top_squadre_over_cross_lega(20).to_string(index=False))
        
        elif scelta == "6":
            leghe = stats.get_leghe_disponibili()
            print(f"\nLeghe disponibili: {', '.join(leghe)}")
            lega = input("Scegli lega: ").strip()
            
            if lega in leghe:
                print("\n" + "="*60)
                print(f"STATISTICHE PRIMO TEMPO - {lega}")
                print("="*60)
                df = stats.statistiche_halftime(lega)
                if not df.empty:
                    print(df.to_string(index=False))
                else:
                    print("Nessun dato primo tempo disponibile per questa lega")
            else:
                print("Lega non valida")
        
        elif scelta == "7":
            print("\n" + "="*60)
            print("TOP 20 SQUADRE UNDER 3.5 (TUTTE LE LEGHE)")
            print("="*60)
            print(stats.top_squadre_under_cross_lega(20).to_string(index=False))
        
        elif scelta == "8":
            leghe = stats.get_leghe_disponibili()
            print(f"\nLeghe disponibili: {', '.join(leghe)}")
            lega = input("Scegli lega: ").strip()
            if lega in leghe:
                print("\n" + "="*60)
                print(f"STATISTICHE GOL FATTI/SUBITI - {lega}")
                print("="*60)
                df = stats.statistiche_gol(lega)
                if not df.empty:
                    print(df.to_string(index=False))
                else:
                    print("Nessun dato primo tempo disponibile per questa lega")
            else:
                print("Lega non valida")

        else:
            print("Opzione non valida")
    
    stats.close()


if __name__ == "__main__":
    menu_interattivo()