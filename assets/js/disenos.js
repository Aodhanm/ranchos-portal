/* Diseños gallery: county-grouped grid + OpenSeadragon viewer.
   Rendered NATIVELY inside the portal document (not an iframe) so image loading is
   never throttled. Thumbnails load via IntersectionObserver; rendering is deferred
   until the Diseños tab is first shown (window.__dzInit), so the portal does not
   fetch 1,800 thumbnails on load. */
(function () {
  'use strict';

  var IMG = 'https://maps.archivesofcalifornia.com/gallery/';

  function esc(s) {
    return String(s == null ? '' : s).replace(/[&<>"]/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c];
    });
  }

  var data = null;
  var activeGroup = 'all';
  var query = '';
  var inited = false;

  // Reliable lazy loading: observe intersection with the diseños scroll CONTAINER
  // (an overflow:auto panel), not the document viewport, so it fires on its scroll.
  var io = null;
  function getIO() {
    if (io) return io;
    if (!('IntersectionObserver' in window)) return null;
    io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (!e.isIntersecting) return;
        var img = e.target;
        if (img.dataset.src) { img.src = img.dataset.src; img.removeAttribute('data-src'); }
        io.unobserve(img);
      });
    }, { root: document.getElementById('dzScroll') || null, rootMargin: '1200px 0px' });
    return io;
  }

  function observeLazy(root) {
    var ob = getIO();
    var imgs = root.querySelectorAll('img[data-src]');
    for (var i = 0; i < imgs.length; i++) {
      if (ob) ob.observe(imgs[i]);
      else imgs[i].src = imgs[i].getAttribute('data-src');
    }
  }

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
      '<div class="thumb"><img src="' + IMG + 'disenos-thumb/' + esc(it.file) + '" alt="" loading="eager"></div>' +
      '<div class="body"><h3>' + esc(it.title) + '</h3>' +
      '<p class="meta">' + esc(it.group + (it.year ? ' · ' + it.year : '')) + '</p></div>';
    return card;
  }

  function render() {
    var root = document.getElementById('gallery-root');
    if (!root) return;
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
    observeLazy(root);
  }

  function buildTools() {
    var bar = document.getElementById('tools');
    if (!bar || bar.dataset.built) return;
    bar.dataset.built = '1';
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
    if (!bar || bar.dataset.built) return;
    bar.dataset.built = '1';
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
        var sc = document.getElementById('dzScroll');
        if (sc) sc.scrollTop = 0;
      });
      bar.appendChild(b);
    });
  }

  var viewer = null;
  function openViewer(it) {
    var ov = document.getElementById('viewer-overlay');
    ov.style.display = 'flex';
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
      tileSources: { type: 'image', url: IMG + 'disenos-img/' + it.file },
      maxZoomPixelRatio: 2.5,
      showNavigator: true,
      crossOriginPolicy: 'Anonymous'
    });
  }
  function closeViewer() {
    document.getElementById('viewer-overlay').style.display = 'none';
    if (viewer) { viewer.destroy(); viewer = null; }
  }

  function doInit() {
    if (inited || !data) return;
    inited = true;
    var noteEl = document.getElementById('gallery-note');
    if (noteEl) noteEl.textContent = data.note;
    var cb = document.getElementById('viewer-close');
    if (cb) cb.addEventListener('click', closeViewer);
    document.addEventListener('keydown', function (e) { if (e.key === 'Escape') closeViewer(); });
    // Open on the largest single county rather than all 1,800 at once (fast + light).
    if (data.groups && data.groups.length) activeGroup = data.groups[0].id;
    buildTools();
    buildChips();
    render();
  }

  // Portal calls this when the Diseños tab is first shown (screen already visible).
  window.__dzInit = function () {
    if (!data) { window.__dzWantInit = true; return; }
    doInit();
  };

  fetch('gallery/disenos-data.json').then(function (r) { return r.json(); }).then(function (d) {
    data = d;
    if (window.__dzWantInit) doInit();
  });
})();
