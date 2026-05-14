# TOP OVER GLOBALE (Resta invariata, ottima per i ranking)
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

# TOP UNDER GLOBALE (Resta invariata)
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

# ── NUOVA LOGICA CALENDARIO E TARGET ──
CALENDARIO_DETTAGLIATO_SQL = """
    WITH Target AS (
        -- Recuperiamo la GT ufficiale salvata dallo scraper
        SELECT giornata_target FROM parametri_leghe WHERE lega = :lega
    )
    -- 1. Match dal calendario (solo se non ancora presenti in 'partite')
    SELECT 
        c.giornata, c.squadra_casa, c.squadra_trasferta, c.data_ora,
        NULL as gol_casa, NULL as gol_trasferta,
        CASE WHEN c.giornata < (SELECT giornata_target FROM Target) THEN 1 ELSE 0 END AS is_recupero,
        'SCHEDULED' as match_status
    FROM calendario c
    WHERE c.lega = :lega
      AND NOT EXISTS (
          SELECT 1 FROM partite p 
          WHERE p.lega = c.lega
    
    UNION ALL

   -- 2. Match già conclusi (Status dedicato, data_ora a NULL)
    SELECT 
        giornata, squadra_casa, squadra_trasferta, NULL as data_ora,
        gol_casa, gol_trasferta,
        0 AS is_recupero,
        'FINISHED' as match_status
    FROM partite
    WHERE lega = :lega AND giornata = (SELECT giornata_target FROM Target)
    
    ORDER BY is_recupero DESC, data_ora ASC
"""

# Query per i risultati recenti (Game Center)
ULTIMI_RISULTATI_SQL = """
    SELECT giornata, squadra_casa, squadra_trasferta, gol_casa, gol_trasferta
    FROM partite
    WHERE lega = :lega
    ORDER BY id DESC LIMIT 10
"""

MATCH_DATA_SQL = """
    SELECT giornata, squadra_casa, squadra_trasferta,
           gol_casa, gol_trasferta
    FROM partite
    WHERE lega = :lega
    ORDER BY giornata ASC
"""

# PULIZIA CALENDARIO
CLEANUP_CALENDARIO_SQL = """
    DELETE FROM calendario
    WHERE EXISTS (
        SELECT 1 FROM partite p
        WHERE p.lega = calendario.lega
          AND p.squadra_casa = calendario.squadra_casa
          AND p.squadra_trasferta = calendario.squadra_trasferta
          AND p.giornata = calendario.giornata
    )
"""