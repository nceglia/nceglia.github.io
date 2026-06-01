/* Renders the full publication list from assets/publications.json
   (refreshed weekly by the update-stats GitHub Action). Falls back silently
   to whatever static markup is already in #pub-list if the file is missing. */
(async function () {
  const list = document.getElementById('pub-list');
  if (!list) return;

  let data;
  try {
    const res = await fetch('/assets/publications.json', { cache: 'no-cache' });
    if (!res.ok) return;
    data = await res.json();
  } catch (e) {
    return;
  }

  const papers = (data.papers || []).filter((p) => p.title);
  if (!papers.length) return;

  const fmt = (n) => (typeof n === 'number' ? n.toLocaleString('en-US') : n);
  const esc = (s) =>
    (s || '').replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
  // Bold the site owner's name within the author list
  const boldName = (s) => esc(s).replace(/((?:[A-Z]\.?\s?){0,3}Ceglia)/g, '<strong>$1</strong>');

  let sortMode = 'citations';
  const sorters = {
    year: (a, b) => (b.year || 0) - (a.year || 0) || (b.citations || 0) - (a.citations || 0),
    citations: (a, b) => (b.citations || 0) - (a.citations || 0) || (b.year || 0) - (a.year || 0),
  };

  function render() {
    list.innerHTML = papers
      .slice()
      .sort(sorters[sortMode])
      .map((p) => {
        const title = p.url
          ? `<a class="publication-title" href="${esc(p.url)}" target="_blank" rel="noopener">${esc(p.title)}</a>`
          : `<div class="publication-title">${esc(p.title)}</div>`;
        const cites =
          p.citations > 0
            ? `<a class="pub-cites" href="${esc(p.url)}" target="_blank" rel="noopener">Cited by ${fmt(p.citations)}</a>`
            : '';
        return (
          `<div class="publication">${title}` +
          `<div class="publication-authors">${boldName(p.authors)}</div>` +
          `<div class="publication-venue">${esc(p.venue)}</div>${cites}</div>`
        );
      })
      .join('');
  }

  const controls = document.getElementById('pub-controls');
  if (controls) {
    controls.innerHTML =
      `<span class="pub-count">${papers.length} publications</span>` +
      `<span class="pub-sort">Sort:` +
      ` <button type="button" data-sort="citations" class="active">Most cited</button>` +
      ` <button type="button" data-sort="year">Newest</button></span>`;
    controls.addEventListener('click', (e) => {
      const btn = e.target.closest('button[data-sort]');
      if (!btn) return;
      sortMode = btn.getAttribute('data-sort');
      controls.querySelectorAll('button').forEach((b) => b.classList.toggle('active', b === btn));
      render();
    });
  }

  render();
})();
