/* Reads assets/stats.json (refreshed weekly by the update-stats GitHub Action)
   and fills in: citation stats, per-paper "Cited by N", and project badges.
   Fails silently if the file is missing so the page never breaks. */
(async function () {
  let s;
  try {
    const res = await fetch('/assets/stats.json', { cache: 'no-cache' });
    if (!res.ok) return;
    s = await res.json();
  } catch (e) {
    return;
  }

  const fmt = (n) => (typeof n === 'number' ? n.toLocaleString('en-US') : n);
  const dig = (path) => path.split('.').reduce((o, k) => (o == null ? undefined : o[k]), s);

  // Headline stats — e.g. data-stat="scholar.citations", data-stat="updated"
  document.querySelectorAll('[data-stat]').forEach((el) => {
    const v = dig(el.getAttribute('data-stat'));
    if (v != null && v !== '') el.textContent = fmt(v);
  });

  // Per-paper "Cited by N" — e.g. <div class="publication" data-paper="genevector">
  const papers = s.papers || {};
  const sid = (s.scholar || {}).id;
  document.querySelectorAll('[data-paper]').forEach((el) => {
    const n = papers[el.getAttribute('data-paper')];
    if (n == null) return;
    let b = el.querySelector('.pub-cites');
    if (!b) {
      b = document.createElement(sid ? 'a' : 'span');
      b.className = 'pub-cites';
      if (sid) {
        b.href = 'https://scholar.google.com/citations?user=' + sid;
        b.target = '_blank';
        b.rel = 'noopener';
      }
      el.appendChild(b);
    }
    b.textContent = 'Cited by ' + fmt(n);
  });

  // Project badges — e.g. <div class="project-badges" data-repo="nceglia/genevector" data-pypi="genevector">
  const gh = s.github || {};
  const pypi = s.pypi || {};
  document.querySelectorAll('[data-repo], [data-pypi]').forEach((el) => {
    const repo = el.getAttribute('data-repo');
    const pkg = el.getAttribute('data-pypi');
    let html = '';
    if (repo && gh[repo] != null) {
      html += '<a class="badge" href="https://github.com/' + repo + '" target="_blank" rel="noopener" title="GitHub stars">★ ' + fmt(gh[repo]) + '</a>';
    }
    if (pkg && pypi[pkg] != null) {
      html += '<a class="badge" href="https://pypi.org/project/' + pkg + '/" target="_blank" rel="noopener" title="PyPI downloads in the last month">⬇ ' + fmt(pypi[pkg]) + '/mo</a>';
    }
    if (html) el.innerHTML = html;
  });
})();
