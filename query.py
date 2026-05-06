# query.py

# Query per le squadre con più Over 2.5
TOP_OVER_SQL = """
    WITH ps AS (
        SELECT lega, squadra_casa AS squadra,
               CASE WHEN (gol_casa + gol_trasferta) >= 3 THEN 1 ELSE 0 END as ov, 1 as p
        FROM partite
        UNION ALL
        SELECT lega, squadra_trasferta,
               CASE WHEN (gol_casa + gol_trasferta) >= 3 THEN 1 ELSE 0 END, 1
        FROM partite
    )
    SELECT lega, squadra,
           SUM(ov) AS over25, SUM(p) AS partite,
           ROUND(100.0 * SUM(ov) / SUM(p), 1) AS pct
    FROM ps GROUP BY lega, squadra
    ORDER BY pct DESC LIMIT :limit
"""

# Query per le squadre con più Under 3.5
TOP_UNDER_SQL = """
    WITH ps AS (
        SELECT lega, squadra_casa AS squadra,
               CASE WHEN (gol_casa + gol_trasferta) < 4 THEN 1 ELSE 0 END as un, 1 as p
        FROM partite
        UNION ALL
        SELECT lega, squadra_trasferta,
               CASE WHEN (gol_casa + gol_trasferta) < 4 THEN 1 ELSE 0 END, 1
        FROM partite
    )
    SELECT lega, squadra,
           SUM(un) AS under35, SUM(p) AS partite,
           ROUND(100.0 * SUM(un) / SUM(p), 1) AS pct
    FROM ps GROUP BY lega, squadra
    ORDER BY pct DESC LIMIT :limit
"""

# Query per ottenere la lista delle leghe disponibili
LISTA_LEGHE_SQL = "SELECT DISTINCT lega FROM partite ORDER BY lega"

# Query dettagliata gol fatti/subiti per lega
GOL_LEGA_SQL = """
    WITH casa AS (
        SELECT squadra_casa AS squadra,
               SUM(gol_casa) AS gfc, SUM(gol_trasferta) AS gsc, COUNT(*) AS pc
        FROM partite WHERE lega = :lega GROUP BY squadra_casa
    ),
    trasf AS (
        SELECT squadra_trasferta AS squadra,
               SUM(gol_trasferta) AS gft, SUM(gol_casa) AS gst, COUNT(*) AS pt
        FROM partite WHERE lega = :lega GROUP BY squadra_trasferta
    )
    SELECT c.squadra,
           c.pc, c.gfc, c.gsc,
           ROUND(1.0 * c.gfc / c.pc, 2) AS mgfc, ROUND(1.0 * c.gsc / c.pc, 2) AS mgsc,
           t.pt, t.gft, t.gst,
           ROUND(1.0 * t.gft / t.pt, 2) AS mgft, ROUND(1.0 * t.gst / t.pt, 2) AS mgst,
           (c.gfc + t.gft) AS totgf, (c.gsc + t.gst) AS totgs
    FROM casa c JOIN trasf t ON c.squadra = t.squadra
    ORDER BY totgf DESC
"""
# Query per il calendario di una lega
CALENDARIO_LEGA_SQL = """
    SELECT giornata, squadra_casa, squadra_trasferta, data_ora 
    FROM calendario 
    WHERE lega = :lega 
    ORDER BY giornata ASC, data_ora ASC
"""