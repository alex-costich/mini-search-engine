// main.js — Terraria Search Engine frontend

// ── DOM refs ──────────────────────────────────────────────────────────────
const input        = document.getElementById('search-input');
const searchBtn    = document.getElementById('search-btn');
const resultsGrid  = document.getElementById('results-grid');
const emptyState   = document.getElementById('empty-state');
const noResults    = document.getElementById('no-results');
const metaDiv      = document.getElementById('search-meta');
const metaText     = document.getElementById('meta-text');
const suggBar      = document.getElementById('suggestion-bar');
const suggLink     = document.getElementById('suggestion-link');
const filterBtns   = document.querySelectorAll('.filter-btn');

let activeCategory = '';
let debounceTimer  = null;

// ── Pixel background canvas ───────────────────────────────────────────────
(function initCanvas() {
  const canvas = document.getElementById('bg-canvas');
  const ctx    = canvas.getContext('2d');
  const TILE   = 18;
  const COLORS = ['#1a2a1a', '#0d1a0d', '#142014', '#0a140a', '#1e2e1e'];
  let cols, rows, tiles;

  function resize() {
    canvas.width  = window.innerWidth;
    canvas.height = window.innerHeight;
    cols  = Math.ceil(canvas.width  / TILE) + 1;
    rows  = Math.ceil(canvas.height / TILE) + 1;
    tiles = Array.from({ length: cols * rows }, () =>
      Math.random() < 0.3 ? COLORS[Math.floor(Math.random() * COLORS.length)] : null
    );
  }

  function draw() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    tiles.forEach((color, i) => {
      if (!color) return;
      const x = (i % cols) * TILE;
      const y = Math.floor(i / cols) * TILE;
      ctx.fillStyle = color;
      ctx.fillRect(x, y, TILE - 1, TILE - 1);
    });
  }

  // Slowly shimmer random tiles
  setInterval(() => {
    const idx = Math.floor(Math.random() * tiles.length);
    tiles[idx] = Math.random() < 0.3
      ? COLORS[Math.floor(Math.random() * COLORS.length)]
      : null;
    draw();
  }, 120);

  window.addEventListener('resize', () => { resize(); draw(); });
  resize();
  draw();
})();

// ── Category filters ──────────────────────────────────────────────────────
filterBtns.forEach(btn => {
  btn.addEventListener('click', () => {
    filterBtns.forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    activeCategory = btn.dataset.cat;
    const q = input.value.trim();
    if (q) doSearch(q);
  });
});

// ── Search triggers ───────────────────────────────────────────────────────
searchBtn.addEventListener('click', () => doSearch(input.value.trim()));

input.addEventListener('keydown', e => {
  if (e.key === 'Enter') {
    clearTimeout(debounceTimer);
    doSearch(input.value.trim());
  }
});

input.addEventListener('input', () => {
  clearTimeout(debounceTimer);
  debounceTimer = setTimeout(() => {
    const q = input.value.trim();
    if (q.length >= 2) doSearch(q);
    else if (q.length === 0) resetUI();
  }, 350);
});

// Spell suggestion click
suggLink.addEventListener('click', () => {
  input.value = suggLink.textContent;
  doSearch(suggLink.textContent);
});

// ── Core search ───────────────────────────────────────────────────────────
async function doSearch(query) {
  if (!query) { resetUI(); return; }

  const params = new URLSearchParams({ q: query, top_k: 10 });
  if (activeCategory) params.set('category', activeCategory);

  let data;
  try {
    const res = await fetch(`/search?${params}`);
    data = await res.json();
  } catch (err) {
    showError();
    return;
  }

  renderResults(data);
}

// ── Render ────────────────────────────────────────────────────────────────
function renderResults(data) {
  // Hide all states first
  emptyState.style.display  = 'none';
  noResults.style.display   = 'none';
  suggBar.style.display     = 'none';

  // Spell suggestion
  if (data.suggestion && data.suggestion !== data.query) {
    suggLink.textContent  = data.suggestion;
    suggBar.style.display = 'block';
    if (data.used_suggestion) {
      suggBar.querySelector('.suggestion-text').innerHTML =
        `🔮 No results for <em>"${data.query}"</em> — showing results for <strong>${data.suggestion}</strong>`;
    } else {
      suggBar.querySelector('.suggestion-text').innerHTML =
        `Did you mean: <button class="suggestion-link" id="suggestion-link">${data.suggestion}</button>?`;
      // re-bind since innerHTML replaced it
      document.getElementById('suggestion-link').addEventListener('click', () => {
        input.value = data.suggestion;
        doSearch(data.suggestion);
      });
    }
  }

  // Meta line
  if (data.total_results > 0) {
    metaText.textContent =
      `${data.total_results} result${data.total_results !== 1 ? 's' : ''} ` +
      `— ${data.search_time_ms}ms`;
    metaDiv.style.display = 'block';
  } else {
    metaDiv.style.display = 'none';
  }

  // Results
  resultsGrid.innerHTML = '';

  if (!data.results || data.results.length === 0) {
    noResults.style.display = 'flex';
    noResults.style.flexDirection = 'column';
    noResults.style.alignItems = 'center';
    return;
  }

  data.results.forEach((r, i) => {
    const card = document.createElement('div');
    card.className = 'result-card';
    card.style.animationDelay = `${i * 0.04}s`;

    const snippet = r.text.length > 200 ? r.text.slice(0, 200) + '…' : r.text;

    card.innerHTML = `
      <div class="result-header">
        <span class="result-rank">#${i + 1}</span>
        <a class="result-title" href="${r.url}" target="_blank" rel="noopener">
          ${escHtml(r.title)}
        </a>
        <div class="result-badges">
          <span class="badge-category ${r.category}">${r.category.toUpperCase()}</span>
          <span class="badge-score">⭐ ${r.score}</span>
        </div>
      </div>
      <p class="result-snippet">${escHtml(snippet)}</p>
      <div class="result-url"><a href="${r.url}" target="_blank" rel="noopener">${r.url}</a></div>
    `;
    resultsGrid.appendChild(card);
  });
}

// ── Helpers ───────────────────────────────────────────────────────────────
function resetUI() {
  resultsGrid.innerHTML    = '';
  emptyState.style.display = 'block';
  noResults.style.display  = 'none';
  suggBar.style.display    = 'none';
  metaDiv.style.display    = 'none';
}

function showError() {
  resultsGrid.innerHTML = `
    <div class="empty-state">
      <div class="empty-icon">⚠️</div>
      <p>Search failed. Is the server running?</p>
    </div>`;
}

function escHtml(str) {
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}