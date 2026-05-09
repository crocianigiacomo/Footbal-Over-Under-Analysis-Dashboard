# ⚽ XG Football Analytics

## Advanced Data & Predictions System

XG Football Analytics è una piattaforma di analisi predittiva progettata per analizzare i trend di rete delle principali leghe calcistiche europee. Il sistema integra uno scraper asincrono, un database SQLite ottimizzato e un motore statistico basato sulla distribuzione di Poisson con correzione Dixon-Coles.

## 🌟 Caratteristiche Principali

- 🔮 Previsioni Evolute: Calcolo delle probabilità per Over/Under 2.5 e 3.5 basato su dati storici e performance recenti.

- 📉 Calibrazione Alpha Automatica: Il modello calibra dinamicamente il parametro Alpha per ogni lega, pesando maggiormente la forma recente delle squadre tramite un'analisi della Log-Loss.

- 📅 Calendario Real-time: Visualizzazione automatica del prossimo turno di campionato con orari e accoppiamenti.

- 📊 Analisi Granulare: Statistiche dettagliate su gol fatti e subiti (casa/trasferta) con tabelle interattive e ordinabili.

- 🤖 Automazione Totale: Aggiornamento quotidiano del database tramite GitHub Actions.

## 🏗️ Architettura Tecnica

Il progetto è diviso in tre moduli principali per garantire scalabilità e manutenibilità:

- Frontend (dashboard.py): Sviluppato in Streamlit, utilizza componenti UI personalizzati (ui_components.py) e un tema Dark ottimizzato via CSS (style.css) e configurazione TOML (config.toml).

- Scraper Engine (scrapplusdb.py): Utilizza aiohttp per fetch asincroni e un APIRateLimiter custom per rispettare i limiti delle API di Football-Data.org. Il database SQLite opera in WAL Mode per consentire letture e scritture simultanee senza lock.

- Statistical Engine (stats_engine.py): Core logico che implementa la distribuzione di Poisson e la correzione di Dixon-Coles per i punteggi bassi (0-0, 1-0, 0-1, 1-1).

## 🧠 Il Modello Predittivo

Il cuore del sistema utilizza la Distribuzione di Poisson pesata nel tempo:

- Time-Decay: Le partite più recenti hanno un peso maggiore nel calcolo delle "forze" di attacco e difesa.

- Dixon-Coles: Viene applicata una correzione per mitigare la naturale tendenza della Poisson a sottostimare la probabilità di pareggi con pochi gol.

- Ottimizzazione Alpha: Per ogni lega, il sistema cerca il valore di Alpha che minimizza la Log-Loss, garantendo che il modello sia sempre tarato sulle dinamiche specifiche di quel campionato.

## 🛠️ Installazione Locale

1. Prerequisiti

Python 3.11+
Una API Key (gratuita) da Football-Data.org

2. Setup

Clona il repository
```console
git clone https://github.com/crocianigiacomo/stats_partite_db.git
cd stats_partite_db
```
Installa le dipendenze
```console
pip install -r requirements.txt
```
3. Configurazione
     Crea un file .env nella cartella principale:

Code snippet
FOOTBALL_API_KEY=il_tuo_token_qui

4. Primo avvio

Esegui lo scraper per popolare il database e calibrare i parametri:

```console
python scrapplusdb.py
```

Avvia la dashboard:
```console
python -m streamlit run dashboard.py
```

## 🚀 Deployment & Automazione

Streamlit Cloud
Il progetto è configurato per essere ospitato su Streamlit Cloud. Ricordati di aggiungere FOOTBALL_API_KEY nei "Secrets" della tua app su Streamlit Cloud.

Aggiornamento Automatico (GitHub Actions)
Il file aggiornamento.yml gestisce l'aggiornamento automatico del database ogni mattina alle 04:00 (CET).

Esegue lo scraper asincrono.

Calibra i nuovi parametri Alpha.

Effettua il commit del file calcio.db aggiornato direttamente nel repository.

## 📂 Struttura File

```console
│   .env
│   .gitignore
│   calcio.db
│   calcio.db-shm
│   calcio.db-wal
│   config.toml
│   dashboard.py
│   query.py
│   README.md
│   requirements.txt
│   scrapplusdb.py
│   stats_engine.py
│   style.css
│   ui_components.py
│
├───.github
│   └───workflows
│           aggiornamento.yml
│
└───__pycache__
        query.cpython-314.pyc
        stats_engine.cpython-314.pyc
        ui_components.cpython-314.pyc
```
- dashboard.py: Entry point dell'applicazione.

- scrapplusdb.py: Inizializzazione DB e fetching dati.

- stats_engine.py: Algoritmi statistici e calibrazione.

- ui_components.py: Componenti HTML/JS per le tabelle.

- query.py: Repository delle query SQL centralizzato.

- .github/workflows/aggiornamento.yml: Configurazione CI/CD per update dati.

## 📝 Licenza

Questo progetto è distribuito sotto licenza MIT.

Developed by Giacomo
Dati forniti da Football-Data.org
