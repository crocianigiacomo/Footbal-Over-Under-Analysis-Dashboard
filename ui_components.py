from datetime import datetime

def pct_bar_html(value, color):
    return (
        f'<div class="pct-wrap">'
        f'<div class="pct-track"><div style="width:{value}%; background:{color}; height:100%; border-radius:3px;"></div></div>'
        f'<span class="pct-label" style="color:{color}">{value}%</span>'
        f'</div>'
    )

def build_stats_table(df, tipo, soglia):
    rows = ""
    is_over = (tipo == "over")
    val_col = "n_over" if is_over else "n_under"
    MEDALS = {1: "🥇", 2: "🥈", 3: "🥉"}
    ROW_CLASS = {1: "row-gold", 2: "row-silver", 3: "row-bronze"}
    

    for rank, (_, r) in enumerate(df.iterrows(), start=1):
        if rank == 6: rows += f"<tr class='sep-row'><td colspan='5'>— Altre Squadre —</td></tr>"
        pct = r["pct"]
        color = ("#FFBB00" if pct >= 75 else "#FFD667") if is_over else ("#0080FF" if pct >= 75 else "#5AAAFA")
        row_cls = ROW_CLASS.get(rank, "")
        rank_cel = MEDALS[rank] if rank <= 3 else str(rank)

        rows += (
            f"<tr class='{row_cls}'>"
            f"<td class='num'>{rank_cel}</td>"
            f"<td class='hide-mob'>{r['lega']}</td>"
            f"<td><b>{r['squadra']}</b></td>"
            f"<td class='num'>{int(r[val_col])}/{int(r['partite'])}</td>"
            f"<td>{pct_bar_html(pct, color)}</td>"
            f"</tr>"
        )
    return f"<div class='tbl-scroll'><table class='cal-table'><thead><tr class='title-row'><td colspan='5'>top {tipo}</td></tr><tr><th style='text-align:center;'>#</th><th class='hide-mob'>Lega</th><th>Squadra</th><th style='text-align:center;'>Esiti</th><th style= 'text-transform:uppercase;'>% {tipo}</th></tr></thead><tbody>{rows}</tbody></table></div>"

def build_calendario(df):
    rows = ""
    for _, r in df.iterrows():
        dt = r['data_ora'].strftime('%d/%m - %H:%M') if isinstance(r['data_ora'], datetime) else str(r['data_ora'])[:16]
        rows += (
            f"<tr>"
            f"<td class='num' style='color:#5865F2; font-weight:700'>{r['giornata']}</td>"
            f"<td style='text-align:center;'><b>{r['squadra_casa']}</b></td>"
            f"<td style='text-align:center; color:#8e9297'>vs</td>"
            f"<td style='text-align:center;'><b>{r['squadra_trasferta']}</b></td>"
            f"<td style='color:#8e9297;'>{dt}</td>"
            f"</tr>"
        )
    return f"<div class='tbl-scroll'><table class='cal-table'><thead><tr><th style='text-align:center;'>Turno</th><th style='text-align:center;'>Casa</th><th></th><th style='text-align:center;'>Trasferta</th><th>Data</th></tr></thead><tbody>{rows}</tbody></table></div>"

def build_prediction_table(df):
    rows = ""
    for _, r in df.iterrows():
        c = r["Colore"]
        rows += (
            f"<tr>"
            f"<td><b>{r['Partita']}</b></td>"
            f"<td class='num hide-mob'>{r['Gol Attesi Casa']}</td>"
            f"<td class='num hide-mob'>{r['Gol Attesi Trasferta']}</td>"
            f"<td class='num hide-mob'><b>{r['Gol Attesi Totali']}</b></td>"
            f"<td><span style='color:{c};font-weight:bold'>{r['Esito']}</span></td>"
            f"<td>{pct_bar_html(r['Prob %'], c)}</td>"
            f"</tr>"
        )
    return f"<div class='tbl-scroll'><table class='cal-table'><thead><tr><th>Match</th><th class='num hide-mob'>xG C</th><th class='num hide-mob'>xG T</th><th class='num hide-mob'>Tot</th><th>Consiglio</th><th>Affidabilità</th></tr></thead><tbody>{rows}</tbody></table></div>"

def build_gol_table(df):
    rows = ""
    for _, r in df.iterrows():
        rows += (
            f"<tr>"
            f"<td><b>{r['squadra']}</b></td>"
            f"<td style='color:#1DB954; text-align:center'>{int(r['gfc'])}</td>"
            f"<td style='color:#ED4245; text-align:center'>{int(r['gsc'])}</td>"
            f"<td class='hide-mob' style='color:#1DB954; text-align:center'>{round(r['mgfc'], 2)}</td>"
            f"<td class='hide-mob' style='color:#ED4245; text-align:center'>{round(r['mgsc'], 2)}</td>"
            f"<td style='color:#5865F2; text-align:center'>{int(r['gft'])}</td>"
            f"<td style='color:#FEE75C; text-align:center'>{int(r['gst'])}</td>"
            f"<td class='hide-mob' style='color:#5865F2; text-align:center'>{round(r['mgft'], 2)}</td>"
            f"<td class='hide-mob' style='color:#FEE75C; text-align:center'>{round(r['mgst'], 2)}</td>"
            f"<td style='text-align:center'><b>{int(r['totgf'])}</b></td>"
            f"<td style='text-align:center'><b>{int(r['totgs'])}</b></td>"
            f"</tr>"
        )
    
    th_html = """
        <th style='text-align:left;' onclick="srt(0,false)">Squadra</th>
        <th style='color:#1DB954; text-align:center' onclick="srt(1,true)">GFC</th>
        <th style='color:#ED4245; text-align:center' onclick="srt(2,true)">GSC</th>
        <th class='hide-mob' style='color:#1DB954; text-align:center' onclick="srt(3,true)">Med GFC</th>
        <th class='hide-mob' style='color:#ED4245; text-align:center' onclick="srt(4,true)">Med GSC</th>
        <th style='color:#5865F2; text-align:center' onclick="srt(5,true)">GFT</th>
        <th style='color:#FEE75C; text-align:center' onclick="srt(6,true)">GST</th>
        <th class='hide-mob' style='color:#5865F2; text-align:center' onclick="srt(7,true)">Med GFT</th>
        <th class='hide-mob' style='color:#FEE75C; text-align:center' onclick="srt(8,true)">Med GST</th>
        <th style='text-align:center' onclick="srt(9,true)">Tot GF</th>
        <th style='text-align:center' onclick="srt(10,true)">Tot GS</th>
    """
    
    return f"""
    <div id="gol-table-container">
    <style>
      #gol-table-container .wrap {{ width:100%; overflow-x:auto; border-radius:8px; background:#181818; }}
      #gol-table-container table {{ width:100%; border-collapse:collapse; white-space:nowrap; font-size:13px; table-layout:fixed; }}
      #gol-table-container th, #gol-table-container td {{ word-break:break-word; }}
      #gol-table-container th {{ background:#202225; padding:12px; border-bottom:2px solid #2f3136; cursor:pointer; user-select:none; }}
      #gol-table-container td {{ padding:10px; border-bottom:1px solid #282828; color:#dcddde; }}
      #gol-table-container tr:hover td {{ background:#2f3136; }}
      @media screen and (max-width: 768px) {{
        #gol-table-container .wrap {{ overflow-x:auto; -webkit-overflow-scrolling:touch; }}
        #gol-table-container table {{ white-space:normal !important; table-layout:auto !important; }}
      }}
    </style>
    <div class="wrap">
      <table id="gol-tbl"><thead><tr>{th_html}</tr></thead><tbody>{rows}</tbody></table>
    </div>
    <script>
    (function(){{
      var d = {{}};
      window.srt = function(col, num) {{
        var tbl = document.getElementById('gol-tbl'), tbody = tbl.querySelector('tbody'),
            rows = Array.from(tbody.querySelectorAll('tr'));
        d[col] = !d[col]; var asc = d[col];
        rows.sort(function(a, b){{
          var va = a.cells[col].innerText.trim(), vb = b.cells[col].innerText.trim();
          if(num){{ va = parseFloat(va) || 0; vb = parseFloat(vb) || 0; }}
          return asc ? (va < vb ? -1 : va > vb ? 1 : 0) : (va > vb ? -1 : va < vb ? 1 : 0);
        }});
        rows.forEach(function(r){{ tbody.appendChild(r); }});
      }};
    }})();
    </script>
    </div>
    """

def build_empty_state(icon: str, title: str, subtitle: str) -> str:
    return (
        f"<div style='display:flex;flex-direction:column;align-items:center;justify-content:center;"
        f"padding:3rem 2rem;border-radius:12px;background:#181818;border:1px dashed #2f3136;"
        f"text-align:center;gap:0.75rem;'>"
        f"<div style='font-size:2.5rem;opacity:0.5'>{icon}</div>"
        f"<div style='color:#ffffff;font-weight:700;font-size:1rem'>{title}</div>"
        f"<div style='color:#8e9297;font-size:0.85rem;max-width:320px;line-height:1.5'>{subtitle}</div>"
        f"</div>"
    )

def build_bottom_nav():
    return """
    <div class="bottom-nav">
        <a href="#statistiche" class="nav-item"><span class="nav-icon">📊</span><span class="nav-label">Rank</span></a>
        <a href="#reti" class="nav-item"><span class="nav-icon">🎯</span><span class="nav-label">Gol Stats</span></a>
        <a href="#calendario" class="nav-item"><span class="nav-icon">📅</span><span class="nav-label">Calendario</span></a>
        <a href="#previsioni" class="nav-item"><span class="nav-icon">🔮</span><span class="nav-label">Predict</span></a>
    </div>
    """