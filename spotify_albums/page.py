import json
from collections import defaultdict
from pathlib import Path


def _esc(s):
    return str(s).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;')


def _top_genres(df, n=5):
    """Greedy set cover: pick genres that each add the most new album coverage."""
    genre_albums = defaultdict(set)
    for i, g in enumerate(df['genres'].dropna()):
        for tag in g.split(','):
            tag = tag.strip()
            if tag and tag != 'unknown':
                genre_albums[tag].add(i)

    covered = set()
    selected = []
    remaining = dict(genre_albums)

    for _ in range(n):
        if not remaining:
            break
        best = max(remaining, key=lambda g: len(remaining[g] - covered))
        if not (remaining[best] - covered):
            break
        selected.append(best.title())
        covered |= remaining[best]
        del remaining[best]

    return selected


def _table_rows(df):
    rows = []
    for _, row in df.iterrows():
        rows.append(
            f'<tr data-url="{row["url"]}">'
            f'<td>{row["artist"]}</td>'
            f'<td>{row["album"]}</td>'
            f'<td>{row["year"]}</td>'
            f'<td>{round(row["duration_min"])}</td>'
            f'<td>{row["genres"]}</td>'
            f'</tr>'
        )
    return '\n'.join(rows)


def _mosaic_items(df):
    items = []
    for _, row in df.iterrows():
        cover = row.get('cover_url', '')
        img_tag = (f'<img src="{cover}" alt="" loading="lazy">'
                   if cover else '<div class="mosaic-placeholder"></div>')
        items.append(
            f'<a class="mosaic-item" href="{row["url"]}" target="_blank" rel="noopener">'
            f'{img_tag}'
            f'<div class="mosaic-overlay">'
            f'<span class="mosaic-album">{_esc(row["album"])}</span>'
            f'<span class="mosaic-artist">{_esc(row["artist"])}</span>'
            f'</div>'
            f'</a>'
        )
    return '\n'.join(items)


def _chart_data_json(df):
    records = []
    for _, row in df.iterrows():
        try:
            year = int(str(row['year'])[:4])
        except (ValueError, TypeError):
            year = None
        records.append({
            'year': year,
            'duration_min': float(row['duration_min']),
            'genres': str(row.get('genres', '')),
        })
    return json.dumps(records)


def build_page(df, img_path: Path, output_path: Path, formspree_url: str = '', footer_name: str = '', footer_url: str = ''):
    albums = len(df)
    total_hours = round(df['duration_min'].sum() / 60, 1)
    remaining = max(0, 365 - albums)
    progress_pct = round(albums / 365 * 100, 1)
    genres = _top_genres(df)
    img_rel = img_path.relative_to(output_path.parent)
    rows = _table_rows(df)
    mosaic = _mosaic_items(df)
    chart_data = _chart_data_json(df)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>365 Albums 2026</title>
  <script src="https://cdn.jsdelivr.net/npm/chart.js@4/dist/chart.umd.min.js"></script>
  <style>
    *, *::before, *::after {{ margin: 0; padding: 0; box-sizing: border-box; }}

    body {{
      background: #08080f;
      color: #ddddf0;
      font-family: system-ui, -apple-system, sans-serif;
      font-weight: 300;
    }}

    /* ── Hero ── */
    .hero {{
      position: relative;
      min-height: 100vh;
      background: url('{img_rel}') center center / cover no-repeat;
      display: flex;
      align-items: flex-start;
      justify-content: center;
      padding: 5% 5% 5%;
    }}

    .hero-content {{
      position: relative;
      width: 100%;
      padding: 3rem 2.5rem;
      text-align: left;
      background: rgba(8, 8, 15, 0.8);
      border-radius: 16px;
      backdrop-filter: blur(2px);
    }}

    .eyebrow {{
      font-size: 0.7rem;
      letter-spacing: 0.25em;
      text-transform: uppercase;
      color: rgba(220,220,255,0.5);
      margin-bottom: 0.75rem;
    }}

    .mission {{
      font-size: 2.8rem;
      font-weight: 200;
      line-height: 1.2;
      margin-bottom: 3rem;
      color: #f0f0ff;
      text-shadow: 0 2px 24px rgba(0,0,0,0.6);
    }}

    .stats {{
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 1.5rem;
      margin-bottom: 2.5rem;
    }}

    .stat-value {{
      font-size: 2.4rem;
      font-weight: 200;
      color: #c084fc;
      line-height: 1;
      text-shadow: 0 0 32px rgba(192,132,252,0.4);
    }}

    .stat-label {{
      font-size: 0.62rem;
      letter-spacing: 0.2em;
      text-transform: uppercase;
      color: rgba(200,200,230,0.45);
      margin-top: 0.4rem;
    }}

    .tags {{
      display: flex;
      flex-wrap: wrap;
      gap: 0.4rem;
      margin-bottom: 2.5rem;
    }}

    .tag {{
      padding: 0.25rem 0.7rem;
      border: 1px solid rgba(160,100,230,0.3);
      font-size: 0.75rem;
      color: #a78bfa;
      backdrop-filter: blur(4px);
      background: rgba(8,8,15,0.3);
    }}

    .progress-row {{
      display: flex;
      justify-content: space-between;
      font-size: 0.62rem;
      letter-spacing: 0.2em;
      text-transform: uppercase;
      color: rgba(200,200,230,0.45);
      margin-bottom: 0.6rem;
    }}

    .bar-track {{
      height: 1px;
      background: rgba(255,255,255,0.1);
    }}

    .bar-fill {{
      height: 1px;
      background: linear-gradient(90deg, #7c3aed, #d4622a);
      width: {progress_pct}%;
    }}

    /* ── Content section ── */
    .content-section {{
      padding: 2rem 2rem 5rem;
      max-width: 900px;
      margin: 0 auto;
    }}

    /* ── Tab nav ── */
    .tab-nav {{
      display: flex;
      margin-bottom: 2.5rem;
      border-bottom: 1px solid #1a1a2e;
    }}

    .tab-btn {{
      background: none;
      border: none;
      border-bottom: 2px solid transparent;
      padding: 0.5rem 1.4rem 0.5rem 0;
      font-family: inherit;
      font-size: 0.62rem;
      letter-spacing: 0.2em;
      text-transform: uppercase;
      color: #55556a;
      cursor: pointer;
      margin-bottom: -1px;
      transition: color 0.15s, border-color 0.15s;
    }}

    .tab-btn:hover {{ color: #a78bfa; }}
    .tab-btn.active {{ color: #a78bfa; border-bottom-color: #7c3aed; }}

    .tab-panel {{ display: none; }}
    .tab-panel.active {{ display: block; }}

    /* ── Table ── */
    .section-label {{
      font-size: 0.65rem;
      letter-spacing: 0.25em;
      text-transform: uppercase;
      color: #55556a;
      margin-bottom: 1.5rem;
    }}

    .table-scroll {{
      overflow-x: auto;
      -webkit-overflow-scrolling: touch;
    }}

    table {{
      width: 100%;
      min-width: 600px;
      border-collapse: collapse;
      font-size: 0.85rem;
    }}

    thead th {{
      text-align: left;
      font-size: 0.62rem;
      letter-spacing: 0.15em;
      text-transform: uppercase;
      color: #55556a;
      padding: 0.5rem 1rem 0.5rem 0;
      border-bottom: 1px solid #1a1a2e;
      cursor: pointer;
      user-select: none;
      white-space: nowrap;
    }}

    thead th:hover {{ color: #a78bfa; }}

    thead th.sortable::after {{ content: ' ↕'; opacity: 0.3; }}
    thead th.sortable.asc::after  {{ content: ' ↑'; opacity: 1; color: #a78bfa; }}
    thead th.sortable.desc::after {{ content: ' ↓'; opacity: 1; color: #a78bfa; }}

    tbody tr {{
      border-bottom: 1px solid #0f0f1a;
      transition: background 0.1s;
      cursor: pointer;
    }}

    tbody tr:hover {{ background: #0f0f1e; }}

    tbody td {{
      padding: 0.6rem 1rem 0.6rem 0;
      color: #c0c0d8;
      vertical-align: top;
    }}

    tbody td:nth-child(3),
    tbody td:nth-child(4) {{ color: #55556a; }}

    /* ── Mosaic ── */
    .mosaic-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
      gap: 4px;
    }}

    @media (max-width: 480px) {{
      .mosaic-grid {{ grid-template-columns: repeat(auto-fill, minmax(90px, 1fr)); }}
    }}

    .mosaic-item {{
      position: relative;
      aspect-ratio: 1;
      overflow: hidden;
      display: block;
      text-decoration: none;
    }}

    .mosaic-item img {{
      width: 100%;
      height: 100%;
      object-fit: cover;
      display: block;
      transition: transform 0.3s;
    }}

    .mosaic-placeholder {{
      width: 100%;
      height: 100%;
      background: #0f0f1a;
    }}

    .mosaic-item:hover img {{ transform: scale(1.06); }}

    .mosaic-overlay {{
      position: absolute;
      inset: 0;
      background: rgba(8, 8, 15, 0.85);
      display: flex;
      flex-direction: column;
      justify-content: flex-end;
      padding: 0.75rem;
      opacity: 0;
      transition: opacity 0.2s;
    }}

    .mosaic-item:hover .mosaic-overlay {{ opacity: 1; }}

    .mosaic-album {{
      font-size: 0.8rem;
      color: #f0f0ff;
      font-weight: 400;
      line-height: 1.3;
    }}

    .mosaic-artist {{
      font-size: 0.7rem;
      color: #a78bfa;
      margin-top: 0.2rem;
    }}

    /* ── Charts ── */
    .charts-grid {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 2rem;
    }}

    @media (max-width: 640px) {{
      .charts-grid {{ grid-template-columns: 1fr; }}
      .content-section {{ padding: 1.5rem 1rem 4rem; }}
    }}

    .chart-box {{
      background: rgba(255,255,255,0.02);
      border: 1px solid #0f0f1a;
      padding: 1.5rem;
      min-width: 0;
      overflow: hidden;
    }}

    .chart-box canvas {{ max-width: 100%; }}

    .chart-label {{
      font-size: 0.62rem;
      letter-spacing: 0.2em;
      text-transform: uppercase;
      color: #55556a;
      margin-bottom: 1rem;
    }}

    /* ── Footer ── */
    footer {{
      text-align: center;
      padding: 2rem;
      font-size: 0.75rem;
      color: #35354a;
      border-top: 1px solid #0f0f1a;
    }}

    footer a {{
      color: #55556a;
      text-decoration: underline;
      transition: color 0.15s;
    }}

    footer a:hover {{ color: #a78bfa; }}

    /* ── Suggest form ── */
    .suggest-form {{
      display: flex;
      flex-direction: column;
      gap: 0.75rem;
      max-width: 480px;
    }}

    .suggest-form input {{
      background: rgba(8, 8, 15, 0.5);
      border: 1px solid rgba(255,255,255,0.08);
      border-radius: 6px;
      padding: 0.65rem 1rem;
      color: #ddddf0;
      font-family: inherit;
      font-size: 0.85rem;
      font-weight: 300;
      outline: none;
      transition: border-color 0.15s;
    }}

    .suggest-form input:focus {{ border-color: #7c3aed; }}
    .suggest-form input::placeholder {{ color: #35354a; }}

    .suggest-form button {{
      align-self: flex-start;
      padding: 0.6rem 1.4rem;
      background: transparent;
      border: 1px solid #7c3aed;
      border-radius: 6px;
      color: #a78bfa;
      font-family: inherit;
      font-size: 0.8rem;
      letter-spacing: 0.1em;
      cursor: pointer;
      transition: background 0.15s, color 0.15s;
    }}

    .suggest-form button:hover {{ background: #7c3aed; color: #fff; }}

    .suggest-thanks {{
      display: none;
      font-size: 0.85rem;
      color: #a78bfa;
      margin-top: 0.5rem;
    }}
  </style>
</head>
<body>

  <section class="hero">
    <div class="hero-content">

      <p class="eyebrow">New Year's Resolution 2026</p>
      <p class="mission">Listen to<br>365 albums.</p>

      <div class="stats">
        <div>
          <div class="stat-value">{albums}</div>
          <div class="stat-label">Listened</div>
        </div>
        <div>
          <div class="stat-value">{total_hours}</div>
          <div class="stat-label">Hours</div>
        </div>
        <div>
          <div class="stat-value">{remaining}</div>
          <div class="stat-label">To go</div>
        </div>
      </div>

      <div class="tags">
        {"".join(f'<span class="tag">{g}</span>' for g in genres)}
      </div>

      <div class="progress-row">
        <span>Progress</span>
        <span>{albums} / 365</span>
      </div>
      <div class="bar-track">
        <div class="bar-fill"></div>
      </div>

      <p class="section-label" style="margin-top:2rem;">Suggest an album</p>
      <form class="suggest-form" id="suggest-form">
        <input type="text" name="name" placeholder="Your name" required>
        <input type="text" name="album" placeholder="Album name or Spotify link" required>
        <button type="submit">Send suggestion</button>
      </form>
      <p class="suggest-thanks" id="suggest-thanks">Thanks for the suggestion!</p>

    </div>
  </section>

  <section class="content-section">

    <nav class="tab-nav">
      <button class="tab-btn active" data-tab="mosaic" onclick="showTab('mosaic')">Mosaic</button>
      <button class="tab-btn" data-tab="list" onclick="showTab('list')">List</button>
      <button class="tab-btn" data-tab="visualizations" onclick="showTab('visualizations')">Visualizations</button>
    </nav>

    <div id="panel-mosaic" class="tab-panel active">
      <div class="mosaic-grid">
        {mosaic}
      </div>
    </div>

    <div id="panel-list" class="tab-panel">
      <div class="table-scroll">
      <table id="albums-table">
        <thead>
          <tr>
            <th class="sortable" onclick="sortTable(0)">Artist</th>
            <th class="sortable" onclick="sortTable(1)">Album</th>
            <th class="sortable" onclick="sortTable(2)">Year</th>
            <th class="sortable" onclick="sortTable(3)">Duration (min)</th>
            <th class="sortable" onclick="sortTable(4)">Genres</th>
          </tr>
        </thead>
        <tbody>
          {rows}
        </tbody>
      </table>
      </div>
    </div>

    <div id="panel-visualizations" class="tab-panel">
      <div class="charts-grid">
        <div class="chart-box">
          <p class="chart-label">Release years</p>
          <canvas id="chart-year"></canvas>
        </div>
        <div class="chart-box">
          <p class="chart-label">Top genres</p>
          <canvas id="chart-genres"></canvas>
        </div>
      </div>
    </div>

  </section>

  <script>
    const FORMSPREE = '{formspree_url}';
    const ALBUMS = {chart_data};

    document.getElementById('suggest-form').addEventListener('submit', async (e) => {{
      e.preventDefault();
      const form = e.target;
      const data = new FormData(form);
      try {{
        const res = await fetch(FORMSPREE, {{ method: 'POST', body: data, headers: {{ 'Accept': 'application/json' }} }});
        if (res.ok) {{
          form.style.display = 'none';
          document.getElementById('suggest-thanks').style.display = 'block';
        }}
      }} catch (_) {{}}
    }});

    document.getElementById('albums-table').querySelector('tbody').addEventListener('click', (e) => {{
      const row = e.target.closest('tr');
      if (row && row.dataset.url) window.open(row.dataset.url, '_blank', 'noopener');
    }});

    function showTab(name) {{
      document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
      document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
      document.getElementById('panel-' + name).classList.add('active');
      document.querySelector('[data-tab="' + name + '"]').classList.add('active');
      if (name === 'visualizations' && !chartsRendered) {{
        chartsRendered = true;
        renderCharts();
      }}
    }}

    let sortCol = -1;
    let sortAsc = true;

    function sortTable(col) {{
      const table = document.getElementById('albums-table');
      const tbody = table.querySelector('tbody');
      const headers = table.querySelectorAll('thead th');
      const rows = Array.from(tbody.querySelectorAll('tr'));

      if (sortCol === col) {{
        sortAsc = !sortAsc;
      }} else {{
        sortCol = col;
        sortAsc = true;
      }}

      headers.forEach((th, i) => {{
        th.classList.remove('asc', 'desc');
        if (i === col && th.classList.contains('sortable')) th.classList.add(sortAsc ? 'asc' : 'desc');
      }});

      rows.sort((a, b) => {{
        const aText = a.cells[col].textContent.trim();
        const bText = b.cells[col].textContent.trim();
        const aNum = parseFloat(aText);
        const bNum = parseFloat(bText);
        const cmp = (!isNaN(aNum) && !isNaN(bNum))
          ? aNum - bNum
          : aText.localeCompare(bText);
        return sortAsc ? cmp : -cmp;
      }});

      rows.forEach(r => tbody.appendChild(r));
    }}

    let chartsRendered = false;

    function renderCharts() {{
      const years = ALBUMS.map(a => a.year).filter(y => y !== null);
      const minY = Math.min(...years) - 3;
      const maxY = Math.max(...years) + 3;
      const bw = 3;
      const xPoints = [];
      for (let x = minY; x <= maxY; x++) xPoints.push(x);

      const kdeVals = xPoints.map(x => {{
        const sum = years.reduce((s, y) => {{
          const u = (x - y) / bw;
          return s + Math.exp(-0.5 * u * u);
        }}, 0);
        return sum / (years.length * bw * Math.sqrt(2 * Math.PI));
      }});

      new Chart(document.getElementById('chart-year'), {{
        type: 'line',
        data: {{
          labels: xPoints,
          datasets: [{{
            data: kdeVals,
            borderColor: '#a78bfa',
            borderWidth: 2,
            pointRadius: 0,
            fill: true,
            backgroundColor: 'rgba(124, 58, 237, 0.12)',
            tension: 0.4,
          }}],
        }},
        options: {{
          responsive: true,
          maintainAspectRatio: true,
          aspectRatio: 2,
          plugins: {{ legend: {{ display: false }} }},
          scales: {{
            x: {{
              grid: {{ color: 'rgba(255,255,255,0.04)' }},
              border: {{ color: 'rgba(255,255,255,0.08)' }},
              ticks: {{
                color: '#55556a',
                font: {{ size: 10 }},
                maxRotation: 0,
                callback: (val, i) => xPoints[i] % 10 === 0 ? String(xPoints[i]) : '',
              }},
            }},
            y: {{ display: false }},
          }},
        }},
      }});

      const counts = {{}};
      ALBUMS.forEach(a => {{
        if (!a.genres || a.genres === 'unknown') return;
        a.genres.split(',').forEach(g => {{
          g = g.trim();
          if (g) counts[g] = (counts[g] || 0) + 1;
        }});
      }});
      const top = Object.entries(counts).sort((a, b) => b[1] - a[1]).slice(0, 10);

      new Chart(document.getElementById('chart-genres'), {{
        type: 'bar',
        data: {{
          labels: top.map(([g]) => g),
          datasets: [{{
            data: top.map(([, c]) => c),
            backgroundColor: 'rgba(124, 58, 237, 0.5)',
            borderColor: '#7c3aed',
            borderWidth: 1,
            borderRadius: 2,
          }}],
        }},
        options: {{
          indexAxis: 'y',
          responsive: true,
          maintainAspectRatio: true,
          aspectRatio: 1.2,
          plugins: {{ legend: {{ display: false }} }},
          scales: {{
            x: {{ display: false }},
            y: {{
              grid: {{ display: false }},
              border: {{ display: false }},
              ticks: {{ color: '#55556a', font: {{ size: 10 }} }},
            }},
          }},
        }},
      }});
    }}
  </script>

  <footer>
    <p>© 2026 <a href="{footer_url}" target="_blank" rel="noopener">{footer_name}</a></p>
  </footer>

</body>
</html>"""

    output_path.write_text(html, encoding='utf-8')
