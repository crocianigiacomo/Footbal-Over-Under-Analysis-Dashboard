# TOP OVER GLOBALE 
TOP_OVER_SQL = """
    WITH ps AS (
        SELECT lega, squadra_casa AS squadra,
               CASE WHEN (gol_casa + gol_trasferta) > :soglia THEN 1 ELSE 0 END as ov, 1 as p
        FROM partite
        UNION ALL
        SELECT lega, squadra_trasferta,
               CASE WHEN (gol_casa + gol_trasferta) > :soglia THEN 1 ELSE 0 END, 1
        FROM partite
    )
    SELECT lega, squadra,
           SUM(ov) AS n_over, SUM(p) AS partite,
           ROUND(100.0 * SUM(ov) / SUM(p), 1) AS pct
    FROM ps GROUP BY lega, squadra
    ORDER BY pct DESC LIMIT :limit
"""

# TOP UNDER GLOBALE 
TOP_UNDER_SQL = """
    WITH ps AS (
        SELECT lega, squadra_casa AS squadra,
               CASE WHEN (gol_casa + gol_trasferta) <= :soglia THEN 1 ELSE 0 END as un, 1 as p
        FROM partite
        UNION ALL
        SELECT lega, squadra_trasferta,
               CASE WHEN (gol_casa + gol_trasferta) <= :soglia THEN 1 ELSE 0 END, 1
        FROM partite
    )
    SELECT lega, squadra,
           SUM(un) AS n_under, SUM(p) AS partite,
           ROUND(100.0 * SUM(un) / SUM(p), 1) AS pct
    FROM ps GROUP BY lega, squadra
    ORDER BY pct DESC LIMIT :limit
"""

LISTA_LEGHE_SQL = "SELECT DISTINCT lega FROM partite ORDER BY lega"

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

CALENDARIO_DETTAGLIATO_SQL = """
    WITH GiornataPrincipale AS (
        -- Identifica la giornata con il maggior numero di match futuri
        SELECT giornata 
        FROM calendario 
        WHERE lega = :lega 
        GROUP BY giornata 
        ORDER BY COUNT(*) DESC LIMIT 1
    )
    SELECT 
        giornata, squadra_casa, squadra_trasferta, data_ora,
        CASE 
            WHEN giornata < (SELECT giornata FROM GiornataPrincipale) THEN 1 
            ELSE 0 
        END AS is_recupero
    FROM calendario
    WHERE lega = :lega
    ORDER BY data_ora ASC
"""

# Dati grezzi per calcolo pesi temporali e stima rho in Python
MATCH_DATA_SQL = """
    SELECT giornata, squadra_casa, squadra_trasferta,
           gol_casa, gol_trasferta
    FROM partite
    WHERE lega = :lega
    ORDER BY giornata ASC
"""