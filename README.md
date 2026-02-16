# stats_partite_db
raccolta e elaborazione statistiche partite leghe principali europee.

Un piccolo progetto personale di raccolta dati tramite la repsonse del sito sofascore.com

Come funziona:

Apro sito web e vado alla pagina della giornata che voglio scaricare.
Apro il dev tool e scarico la response e la salvo in un file .json.
Salvo il file nella cartella del programma.
Ripeto l'operazione per tutte le giornate che voglio insere nel mio database.
Avvio scrapplusdb.py che mi creerà un db contenente partite e gol delle giornate trovate.
Avvio query.py che mi apre un menu interattivo per poter analizzare i dati nel db tramite alcune query preimpostate.


