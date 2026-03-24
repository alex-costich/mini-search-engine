// main.js — Terraria Search Engine (Wiki theme)

const input       = document.getElementById('search-input');
const searchBtn   = document.getElementById('search-btn');
const resultsGrid = document.getElementById('results-grid');
const emptyState  = document.getElementById('empty-state');
const noResults   = document.getElementById('no-results');
const metaDiv     = document.getElementById('search-meta');
const metaText    = document.getElementById('meta-text');
const suggBar     = document.getElementById('suggestion-bar');
const suggLink    = document.getElementById('suggestion-link');
const filterBtns  = document.querySelectorAll('.filter-btn');

let activeCategory = '';
let debounceTimer  = null;

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
    resultsGrid.innerHTML = '<p style="color:#888;font-style:italic;padding:1rem 0;">Search failed. Is the server running?</p>';
    return;
  }

  renderResults(data);
}

// ── Render ────────────────────────────────────────────────────────────────
function renderResults(data) {
  emptyState.style.display = 'none';
  noResults.style.display  = 'none';
  suggBar.style.display    = 'none';

  // Spell suggestion
  if (data.suggestion && data.suggestion !== data.query) {
    suggBar.style.display = 'block';
    if (data.used_suggestion) {
      suggBar.querySelector('.suggestion-text').innerHTML =
        `No results for <em>"${escHtml(data.query)}"</em> — showing results for <strong>${escHtml(data.suggestion)}</strong>`;
    } else {
      suggBar.querySelector('.suggestion-text').innerHTML =
        `Did you mean: <button class="suggestion-link" id="suggestion-link">${escHtml(data.suggestion)}</button>?`;
      document.getElementById('suggestion-link').addEventListener('click', () => {
        input.value = data.suggestion;
        doSearch(data.suggestion);
      });
    }
  }

  // Meta
  if (data.total_results > 0) {
    metaText.textContent =
      `${data.total_results} result${data.total_results !== 1 ? 's' : ''} found in ${data.search_time_ms}ms`;
    metaDiv.style.display = 'block';
  } else {
    metaDiv.style.display = 'none';
  }

  resultsGrid.innerHTML = '';

  if (!data.results || data.results.length === 0) {
    noResults.style.display = 'block';
    return;
  }

  data.results.forEach((r, i) => {
    const card = document.createElement('div');
    card.className = 'result-card';
    card.style.animationDelay = `${i * 0.03}s`;

    const snippet = r.text.length > 220 ? r.text.slice(0, 220) + '…' : r.text;

    card.innerHTML = `
      <div class="result-header">
        <span class="result-rank">${i + 1}.</span>
        <a class="result-title" href="${r.url}" target="_blank" rel="noopener">${escHtml(r.title)}</a>
        <div class="result-badges">
          <span class="badge-category ${r.category}">${r.category}</span>
          <span class="badge-score">score: ${r.score}</span>
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

function escHtml(str) {
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}