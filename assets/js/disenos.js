/* Diseños gallery: county-grouped grid + OpenSeadragon viewer. Lazy thumbnails for scale. */
(function () {
  'use strict';

  function esc(s) {
    return String(s == null ? '' : s).replace(/[&<>"]/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c];
    });
  }

  var data = null;
  var activeGroup = 'all';
  var query = '';

  function passes(it) {
    if (query) {
      var hay = (it.title + ' ' + it.year + ' ' + it.caption + ' ' + it.group).toLowerCase();
      if (hay.indexOf(query) === -1) return false;
    }
    return true;
  }
  function makeCard(it) {
    var card = document.createElement('a');
    card.className = 'card';
    card.href = '#' + encodeURIComponent(it.id);
    card.addEventListener('click', function (e) { e.preventDefault(); openViewer(it); });
    card.innerHTML =
      '<div class="thumb"><img loading="lazy" src="https://maps.archivesofcalifornia.com/gallery/disenos-thumb/' + esc(it.file) + '" alt=""></div>' +
      '<div class="body"><h3>' + esc(it.title) + '</h3>' +
      '<p class="meta">' + esc(it.group + (it.year ? ' · ' + it.year : '')) + '</p></div>';
    return card;
  }

  function render() {
    var root = document.getElementById('gallery-root');
    root.innerHTML = '';
    var shown = 0;
    data.groups.forEach(function (g) {
      if (activeGroup !== 'all' && activeGroup !== g.id) return;
      var items = data.items.filter(function (it) { return it.group === g.id && passes(it); });
      if (!items.length) return;
      var sec = document.createElement('section');
      sec.innerHTML = '<h2>' + esc(g.label) + ' <span class="gcount">' + items.length + '</span></h2>' +
        '<p class="prose gintro">' + esc(g.intro) + '</p>';
      var grid = document.createElement('div');
      grid.className = 'card-grid gallery-grid';
      items.forEach(function (it) { grid.appendChild(makeCard(it)); });
      sec.appendChild(grid);
      root.appendChild(sec);
      shown += items.length;
    });
    if (!shown) root.innerHTML = '<p class="prose">Nothing matches. Clear the search.</p>';
  }

  function buildTools() {
    var bar = document.getElementById('tools');
    if (!bar) return;
    var search = document.createElement('input');
    search.type = 'search';
    search.className = 'gsearch';
    search.placeholder = 'Search rancho, county, year…';
    search.setAttribute('aria-label', 'Search the diseños');
    search.addEventListener('input', function () { query = this.value.toLowerCase(); render(); });
    bar.appendChild(search);
  }

  function buildChips() {
    var bar = document.getElementById('chips');
    var chips = [{ id: 'all', label: 'All (' + data.items.length + ')' }].concat(data.groups);
    chips.forEach(function (g) {
      var b = document.createElement('button');
      b.className = 'chip' + (g.id === activeGroup ? ' active' : '');
      b.textContent = g.label;
      b.addEventListener('click', function () {
        activeGroup = g.id;
        Array.prototype.forEach.call(bar.children, function (c) { c.classList.remove('active'); });
        b.classList.add('active');
        render();
        window.scrollTo(0, 0);
      });
      bar.appendChild(b);
    });
  }

  var viewer = null;
  function openViewer(it) {
    history.replaceState(null, '', '#' + encodeURIComponent(it.id));
    var ov = document.getElementById('viewer-overlay');
    ov.style.display = 'flex';
    document.body.style.overflow = 'hidden';
    document.getElementById('viewer-title').textContent = it.title;
    document.getElementById('viewer-meta').innerHTML =
      esc(it.group + (it.year ? ' · ' + it.year : '')) +
      ' · <a href="' + esc(it.source_url) + '" target="_blank" rel="noopener">archival original →</a>';
    var hn = document.getElementById('viewer-headnote');
    hn.textContent = it.headnote || '';
    hn.style.display = it.headnote ? '' : 'none';
    var lf = document.getElementById('viewer-lookfor');
    lf.textContent = it.look_for || '';
    lf.style.display = it.look_for ? '' : 'none';
    document.getElementById('viewer-caption').textContent = it.caption;
    document.getElementById('viewer-credit').textContent = it.credit;
    if (viewer) { viewer.destroy(); viewer = null; }
    viewer = OpenSeadragon({
      id: 'seadragon',
      prefixUrl: 'https://cdn.jsdelivr.net/npm/openseadragon@4.1.1/build/openseadragon/images/',
      tileSources: { type: 'image', url: 'https://maps.archivesofcalifornia.com/gallery/disenos-img/' + it.file },
      maxZoomPixelRatio: 2.5,
      showNavigator: true,
      crossOriginPolicy: 'Anonymous'
    });
  }
  function closeViewer() {
    document.getElementById('viewer-overlay').style.display = 'none';
    document.body.style.overflow = '';
    history.replaceState(null, '', location.pathname);
    if (viewer) { viewer.destroy(); viewer = null; }
  }
  document.getElementById('viewer-close').addEventListener('click', closeViewer);
  document.addEventListener('keydown', function (e) { if (e.key === 'Escape') closeViewer(); });

  fetch('disenos-data.json').then(function (r) { return r.json(); }).then(function (d) {
    data = d;
    var noteEl = document.getElementById('gallery-note');
    if (noteEl) noteEl.textContent = d.note;
    buildTools();
    buildChips();
    render();
    var id = decodeURIComponent(location.hash.slice(1));
    if (id) {
      var it = d.items.filter(function (x) { return x.id === id; })[0];
      if (it) openViewer(it);
    }
  });
})();
