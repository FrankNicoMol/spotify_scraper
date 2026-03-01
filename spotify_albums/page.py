from collections import defaultdict
from pathlib import Path


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
            f'<tr>'
            f'<td><a href="{row["url"]}" target="_blank" rel="noopener">↗</a></td>'
            f'<td>{row["artist"]}</td>'
            f'<td>{row["album"]}</td>'
            f'<td>{row["year"]}</td>'
            f'<td>{row["duration_min"]}</td>'
            f'<td>{row["genres"]}</td>'
            f'</tr>'
        )
    return '\n'.join(rows)


def build_page(df, img_path: Path, output_path: Path, formspree_url: str = '', footer_name: str = '', footer_url: str = ''):
    albums = len(df)
    total_min = int(df['duration_min'].sum())
    remaining = max(0, 365 - albums)
    progress_pct = round(albums / 365 * 100, 1)
    genres = _top_genres(df)
    img_rel = img_path.relative_to(output_path.parent)
    rows = _table_rows(df)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>365 Albums 2026</title>
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

    /* ── Table section ── */
    .table-section {{
      padding: 5rem 2rem;
      max-width: 900px;
      margin: 0 auto;
    }}

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

    thead th.sortable::after {{
      content: ' ↕';
      opacity: 0.3;
    }}

    thead th.sortable.asc::after  {{ content: ' ↑'; opacity: 1; color: #a78bfa; }}
    thead th.sortable.desc::after {{ content: ' ↓'; opacity: 1; color: #a78bfa; }}

    tbody tr {{
      border-bottom: 1px solid #0f0f1a;
      transition: background 0.1s;
    }}

    tbody tr:hover {{ background: #0f0f1e; }}

    tbody td {{
      padding: 0.6rem 1rem 0.6rem 0;
      color: #c0c0d8;
      vertical-align: top;
    }}

    tbody td:nth-child(4),
    tbody td:nth-child(5) {{ color: #55556a; }}

    tbody td:nth-child(1) {{ text-align: center; }}

    tbody td a {{
      color: #55556a;
      text-decoration: none;
      font-size: 0.9rem;
      transition: color 0.15s;
    }}

    tbody td a:hover {{ color: #a78bfa; }}

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

    /* ── Suggest form (inside hero box) ── */
    .hero-divider {{
      border: none;
      border-top: 1px solid rgba(255,255,255,0.08);
      margin: 2rem 0;
    }}

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
          <div class="stat-value">{total_min:,}</div>
          <div class="stat-label">Minutes</div>
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

      <hr class="hero-divider">

      <p class="section-label">Suggest an album</p>
      <form class="suggest-form" id="suggest-form">
        <input type="text" name="name" placeholder="Your name" required>
        <input type="text" name="album" placeholder="Album name or Spotify link" required>
        <button type="submit">Send suggestion</button>
      </form>
      <p class="suggest-thanks" id="suggest-thanks">Thanks for the suggestion!</p>

    </div>
  </section>

  <section class="table-section">
    <p class="section-label">All albums</p>
    <div class="table-scroll">
    <table id="albums-table">
      <thead>
        <tr>
          <th></th>
          <th class="sortable" onclick="sortTable(1)">Artist</th>
          <th class="sortable" onclick="sortTable(2)">Album</th>
          <th class="sortable" onclick="sortTable(3)">Year</th>
          <th class="sortable" onclick="sortTable(4)">Duration (min)</th>
          <th class="sortable" onclick="sortTable(5)">Genres</th>
        </tr>
      </thead>
      <tbody>
        {rows}
      </tbody>
    </table>
    </div>
  </section>

  <script>
    const FORMSPREE = '{formspree_url}';

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
  </script>

  <footer>
    <p>© 2026 <a href="{footer_url}" target="_blank" rel="noopener">{footer_name}</a></p>
  </footer>

</body>
</html>"""

    output_path.write_text(html, encoding='utf-8')
