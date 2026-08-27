/* California History Maps — shared map engine (v2, 2026-07-14)
   Renders a map page from a data/*.json file. See data/schema.md.
   Vanilla JS + Leaflet (pinned CDN, loaded by the shell page). */
(function () {
  'use strict';

  var MAP_ID = document.body.getAttribute('data-map');
  var DATA_URL = '../data/' + MAP_ID + '.json?t=' + Date.now();  // cache-bust so data edits show
  var CLUSTER_THRESHOLD = 75;

  var state = {
    data: null, map: null, allMarkers: [],  // {feature, marker, layerId}
    layerGroups: {}, routeLines: [],
    yearMin: null, yearMax: null, query: ''
  };

  // ---------- helpers ----------
  function el(tag, cls, html) {
    var e = document.createElement(tag);
    if (cls) e.className = cls;
    if (html !== undefined) e.innerHTML = html;
    return e;
  }
  function esc(s) {
    return String(s == null ? '' : s).replace(/[&<>"]/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c];
    });
  }
  function featureYear(f) {
    var m = /^(\d{4})/.exec(f.date && f.date.iso || '');
    return m ? +m[1] : null;
  }

  // ---------- markers ----------
  var PRECISION_LABEL = {
    exact: 'located precisely',
    place: 'place-level precision',
    area: 'approximate location within the district',
    conjectural: 'CONJECTURAL location'
  };

  function markerFor(f, color) {
    var precision = f.coord_precision || 'place';
    var perm = !(state.data && state.data.hover_labels);  // dense maps: hover labels instead of permanent
    if (f.polygon) {
      // territory polygon (rings of [lat,lng]) with a plain-text label at the anchor
      var approxPoly = precision === 'conjectural';  // reconstructed/inferred outline -> dashed, faint
      var poly = L.polygon(f.polygon, {
        color: color, weight: approxPoly ? 1.6 : 1.4,
        dashArray: approxPoly ? '5 5' : null,
        fillColor: color, fillOpacity: approxPoly ? 0.07 : 0.16
      });
      poly.bindPopup(popupHtml(f), { maxWidth: 380 });
      poly.bindTooltip(f.name.split(' (')[0], {
        permanent: perm, direction: 'center', className: 'homeland-label'
      });
      poly.on('popupopen', function () {
        poly.setStyle({ color: '#3b82f6', weight: 3.5, fillOpacity: 0.28 });
        poly.bringToFront();
        if (poly._path) poly._path.classList.add('rancho-selected');
      });
      poly.on('popupclose', function () {
        poly.setStyle({ color: color, weight: approxPoly ? 1.6 : 1.4, fillOpacity: approxPoly ? 0.07 : 0.16 });
        if (poly._path) poly._path.classList.remove('rancho-selected');
      });
      return poly;
    }
    if (f.label_only) {
      var anchor = L.circleMarker(f.coords, { radius: 3, weight: 1, color: color,
        fillColor: color, fillOpacity: 0.5, opacity: 0.6 });
      anchor.bindPopup(popupHtml(f), { maxWidth: 380 });
      anchor.bindTooltip(f.name.split(' (')[0], {
        permanent: perm, direction: 'top', offset: [0, -2], className: 'homeland-label sub'
      });
      return anchor;
    }
    if (f.area_radius_km) {
      // soft approximate-homeland circle with a permanent label
      var circ = L.circle(f.coords, {
        radius: f.area_radius_km * 1000, color: color, weight: 1.5,
        dashArray: '6 5', fillColor: color, fillOpacity: 0.13
      });
      circ.bindPopup(popupHtml(f), { maxWidth: 380 });
      circ.bindTooltip(f.name.split(' (')[0], {
        permanent: perm, direction: 'center', className: 'homeland-label'
      });
      return circ;
    }
    var opts = {
      radius: 7, weight: 2, color: color, fillColor: color, fillOpacity: 0.85
    };
    if (precision === 'area') { opts.fillOpacity = 0.4; opts.dashArray = '2 2'; opts.radius = 3.5; opts.weight = 1; }
    if (precision === 'conjectural') { opts.fillOpacity = 0; opts.dashArray = '4 3'; }
    if (f.type === 'settlement' || f.type === 'mission' || f.type === 'presidio' || f.type === 'pueblo') {
      opts.radius = 4; opts.weight = 1.2; opts.fillOpacity = 0.9;   // small fixed dot, not enlarged at any zoom
    }
    opts.pane = 'markerTop';
    var m = L.circleMarker(f.coords, opts);
    m.bindPopup(popupHtml(f), { maxWidth: 380 });
    return m;
  }

  function popupHtml(f) {
    var h = '<div class="popup">';
    h += '<h3>' + esc(f.name) + '</h3>';
    var badges = [];
    if (f.register_no) badges.push('<span class="badge reg" title="Military-register number">#' + esc(f.register_no) + '</span>');
    if (f.type) badges.push('<span class="badge type">' + esc(f.type) + '</span>');
    if (f.date && f.date.display) badges.push('<span class="badge date">' + esc(f.date.display) +
      (f.date.confidence && f.date.confidence !== 'exact' ? ' <em>(' + esc(f.date.confidence) + ')</em>' : '') + '</span>');
    if (f.outcome) {
      var rej = /reject|dismiss/i.test(f.outcome) && !/patent|confirmed by the (district|u\.? ?s)/i.test(f.outcome);
      badges.push('<span class="badge oc ' + (rej ? 'rej' : 'conf') + '">US: ' + (rej ? 'rejected' : 'confirmed') + '</span>');
    }
    if (badges.length) h += '<p class="badges">' + badges.join(' ') + '</p>';
    if (f.summary) h += '<p>' + esc(f.summary) + '</p>';
    if (f.rank_note) h += '<p class="rank-note" style="font-size:.82rem;opacity:.8">\ud83d\udccf ' + esc(f.rank_note) + '</p>';
    if (f.disenos && f.disenos.length) {
      h += '<div class="diseno-strip">';
      f.disenos.forEach(function (d) {
        h += '<img class="popup-diseno" src="' + esc(d.thumb) + '" data-full="' + esc(d.img) + '" title="' + esc(d.title || '') + '" loading="lazy" alt="Diseño (land-case map)" onclick="window.__disenoLB(this)">';
      });
      h += '</div><span class="diseno-cap">' + f.disenos.length + ' diseño' + (f.disenos.length > 1 ? 's' : '')
         + ' \u2014 the grant\u2019s original hand-drawn map' + (f.disenos.length > 1 ? 's' : '') + ' (click to enlarge)</span>';
    }
    if (f.series && f.series.length) {
      h += '<details class="series-box"><summary>' + esc(f.series_label || 'Dated series') +
           ' (' + f.series.length + ' entries)</summary>';
      h += '<table class="series"><tbody>';
      f.series.forEach(function (row) {
        var srec = row[3] || citeToRecord(row[2], f.ca_volume);
        var scite = row[2]
          ? ' <span class="cite">' + (srec
              ? '<a href="' + caUrl(srec) + '" target="_blank" rel="noopener">' + esc(row[2]) + '</a>'
              : esc(row[2])) + '</span>'
          : '';
        h += '<tr><td>' + esc(row[0]) + '</td><td>' + esc(row[1]) + scite + '</td></tr>';
      });
      h += '</tbody></table></details>';
    }
    if (f.result) h += '<p class="result"><strong>' + esc(f.result) + '</strong></p>';
    if (f.quote && f.quote.es) {
      h += '<blockquote lang="es">' + esc(f.quote.es) + '</blockquote>';
      if (f.quote.en) h += '<p class="quote-en">(' + esc(f.quote.en) + ')</p>';
    }
    if (f.native_groups && f.native_groups.length)
      h += '<p class="native">Native peoples named in the sources: ' + esc(f.native_groups.join(', ')) + '</p>';
    (f.sources || []).forEach(function (s) {
      h += '<p class="source">' + esc(s.citation);
      var rec = s.ca_record || citeToRecord(s.citation, f.ca_volume);
      if (rec) h += ' \u2014' + recordLink(rec);
      if (s.ia_leaf_url) h += ' \u2014 <a href="' + esc(s.ia_leaf_url) + '" target="_blank" rel="noopener">the manuscript leaf \u2192</a>';
      if (s.url && !rec) h += ' \u2014 <a href="' + esc(s.url) + '" target="_blank" rel="noopener">source \u2192</a>';
      h += '</p>';
    });
    var pl = PRECISION_LABEL[f.coord_precision || 'place'];
    if (f.coord_precision && f.coord_precision !== 'exact')
      h += '<p class="precision">📍 ' + esc(pl) + '</p>';
    if (f.notes) h += '<p class="notes">' + esc(f.notes) + '</p>';
    h += '<p class="permalink"><a href="#' + encodeURIComponent(f.id) + '" onclick="navigator.clipboard&&navigator.clipboard.writeText(location.href.split(\'#\')[0]+\'#' + esc(f.id) + '\');return false;" title="Copy permalink">🔗 permalink</a></p>';
    return h + '</div>';
  }


  // ---------- C-A deep links ----------
  // The Archives of California catalog resolves #caN-dM to a single record.
  var CA_BASE = 'https://archivesofcalifornia.com/#';
  function caUrl(rec) { return CA_BASE + encodeURIComponent(rec); }
  // Parse a human citation into a record id. Handles "C-A 50 Doc 32",
  // "Dep. Rec. (C-A 48) Doc 29", and a bare "Doc 10" when the feature
  // declares a default volume. Returns null when nothing is resolvable.
  function citeToRecord(text, defaultVol) {
    if (!text) return null;
    var m = /C-A\s*(\d{1,2})\D{0,14}?Docs?\.?\s*(\d{1,4})/i.exec(text);
    if (m) return 'ca' + m[1] + '-d' + m[2];
    if (defaultVol) {
      var b = /^\s*Docs?\.?\s*(\d{1,4})/i.exec(text);
      if (b) return 'ca' + defaultVol + '-d' + b[1];
    }
    return null;
  }
  function recordLink(rec, label) {
    return ' <a class="ca-link" href="' + caUrl(rec) + '" target="_blank" rel="noopener">' +
           (label || 'View the record') + ' \u2192</a>';
  }

  // ---------- filtering ----------
  function applyFilters() {
    var q = state.query.toLowerCase();
    var shown = 0;
    var pts = [];
    state.allMarkers.forEach(function (rec) {
      var f = rec.feature;
      var y = featureYear(f);
      var okYear = y == null || (y >= state.yearMin && y <= state.yearMax);
      var hay = (f.name + ' ' + (f.summary || '') + ' ' + (f.owner || '') + ' ' + (f.land_case || '') + ' ' +
                 (f.tags || []).join(' ') + ' ' + (f.native_groups || []).join(' ')).toLowerCase();
      var okQuery = !q || hay.indexOf(q) !== -1;
      var group = state.layerGroups[rec.layerId];
      var on = okYear && okQuery;
      if (group) {
        if (on && !group.hasLayer(rec.marker)) group.addLayer(rec.marker);
        if (!on && group.hasLayer(rec.marker)) group.removeLayer(rec.marker);
      }
      if (on) { shown++; if (rec.feature.coords) pts.push(rec.feature.coords); }
    });
    state.matchPts = pts;
    var c = document.getElementById('feature-count');
    if (c) c.textContent = q ? (shown + ' grant' + (shown === 1 ? '' : 's') + ' match \u201c' + state.query + '\u201d')
                             : (shown + ' of ' + state.allMarkers.length + ' features shown');
  }

  // ---------- controls ----------
  function buildControls(data) {
    var bar = document.getElementById('controls');
    if (!bar) return;

    // search
    var search = el('input', 'search');
    search.type = 'search';
    search.placeholder = 'Search a rancho, owner, or family name…  (Enter to zoom)';
    search.setAttribute('aria-label', 'Search features');
    search.addEventListener('input', function () { state.query = this.value; applyFilters(); });
    search.addEventListener('keydown', function (e) {
      if (e.key === 'Enter' && state.query && state.matchPts && state.matchPts.length) {
        try { map.fitBounds(L.latLngBounds(state.matchPts), { padding: [50, 50], maxZoom: 12 }); } catch (err) {}
      }
    });
    bar.appendChild(search);

    // timeline slider (dual range via two inputs)
    var years = state.allMarkers.map(function (r) { return featureYear(r.feature); })
      .filter(function (y) { return y != null; });
    var lo = data.date_range ? data.date_range[0] : Math.min.apply(null, years);
    var hi = data.date_range ? data.date_range[1] : Math.max.apply(null, years);
    state.yearMin = lo; state.yearMax = hi;
    var wrap = el('div', 'timeline');
    var lbl = el('span', 'timeline-label', lo + '–' + hi);
    function slider(val) {
      var s = el('input');
      s.type = 'range'; s.min = lo; s.max = hi; s.value = val;
      s.setAttribute('aria-label', 'Year filter');
      return s;
    }
    var s1 = slider(lo), s2 = slider(hi);
    function upd() {
      state.yearMin = Math.min(+s1.value, +s2.value);
      state.yearMax = Math.max(+s1.value, +s2.value);
      lbl.textContent = state.yearMin + '–' + state.yearMax;
      applyFilters();
    }
    s1.addEventListener('input', upd); s2.addEventListener('input', upd);
    wrap.appendChild(s1); wrap.appendChild(s2); wrap.appendChild(lbl);
    bar.appendChild(wrap);

    // count + cite
    bar.appendChild(el('span', 'count', '<span id="feature-count"></span>'));
    var cite = el('button', 'cite-btn', 'Cite this map');
    cite.addEventListener('click', function () { showCite(data); });
    bar.appendChild(cite);
  }

  function showCite(data) {
    var today = new Date().toISOString().slice(0, 10);
    var url = location.href.split('#')[0];
    var txt = 'Coyne, Aodhan. “' + data.title + '.” California History Maps. ' +
      'Interactive map. Last updated ' + (data.last_updated || today) + '. ' + url +
      ' (accessed ' + today + ').';
    var box = document.getElementById('cite-box');
    if (!box) {
      box = el('div', 'cite-box'); box.id = 'cite-box';
      document.body.appendChild(box);
    }
    // The citation text is bound with addEventListener, never spliced into an
    // onclick attribute: JSON.stringify() output always begins with a double
    // quote, which closed the attribute and left a truncated, dead handler.
    box.innerHTML = '<p>' + esc(txt) + '</p>';
    var copyBtn = el('button'); copyBtn.textContent = 'Copy';
    copyBtn.addEventListener('click', function () {
      if (navigator.clipboard) { navigator.clipboard.writeText(txt); }
      copyBtn.textContent = 'Copied';
    });
    var closeBtn = el('button'); closeBtn.textContent = 'Close';
    closeBtn.addEventListener('click', function () { box.style.display = 'none'; });
    box.appendChild(copyBtn); box.appendChild(closeBtn);
    box.style.display = 'block';
  }

  // ---------- init ----------
  function init(data) {
    state.data = data;
    document.title = data.title + ' · California History Maps';
    var h = document.getElementById('map-title');
    if (h) h.textContent = data.title;
    var sub = document.getElementById('map-subtitle');
    if (sub) sub.textContent = data.subtitle || '';
    var ab = document.getElementById('map-abstract');
    if (ab && data.abstract) ab.textContent = data.abstract;

    var map = L.map('map', { center: data.center || [36.5, -120.5], zoom: data.zoom || 6 });
    state.map = map;
    map.createPane('markerTop'); map.getPane('markerTop').style.zIndex = 460;
    // Keyless Esri basemaps (no API key). Topographic is the default; users can switch via the layers control.
    var esriTopoAttr = 'Tiles &copy; <a href="https://www.esri.com/">Esri</a>, HERE, Garmin, USGS, NGA, EPA, USDA, NPS';
    var baseTopo = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}',
      { maxZoom: 17, maxNativeZoom: 17, attribution: esriTopoAttr });
    var baseSatellite = L.layerGroup([
      L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
        { maxZoom: 17, maxNativeZoom: 17, attribution: 'Imagery &copy; <a href="https://www.esri.com/">Esri</a>, Maxar, Earthstar Geographics' }),
      L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}',
        { maxZoom: 17, maxNativeZoom: 16, pane: 'shadowPane' })
    ]);
    baseTopo.addTo(map);
    var baseLayers = { 'Topographic': baseTopo, 'Satellite': baseSatellite };

    var layerColors = {};
    var overlays = {};

    // optional georeferenced period chart (approximate corner-pin); off until toggled
    var histOverlay = null, histSliderEl = null;
    if (data.historical_overlay && data.historical_overlay.image && data.historical_overlay.bounds) {
      var ov = data.historical_overlay;
      histOverlay = L.imageOverlay(ov.image, ov.bounds, {
        opacity: ov.opacity != null ? ov.opacity : 0.7,
        attribution: ov.attribution || '',
        interactive: false
      });
      overlays['<span class="swatch hist"></span> ' + esc(ov.name) +
        (ov.note ? ' <em>(' + esc(ov.note) + ')</em>' : '')] = histOverlay;
    }

    var useCluster = (data.cluster !== false) && (data.features || []).length > CLUSTER_THRESHOLD && window.L.markerClusterGroup;
    (data.layers || []).forEach(function (ly) {
      layerColors[ly.id] = ly.color;
      var g = useCluster
        ? L.markerClusterGroup({ maxClusterRadius: 36, disableClusteringAtZoom: 9 })
        : L.layerGroup();
      state.layerGroups[ly.id] = g;
      if (!ly.default_off) g.addTo(map);
      overlays['<span class="swatch" style="background:' + ly.color + '"></span> ' + esc(ly.label)] = g;
    });

    (data.features || []).forEach(function (f) {
      var color = layerColors[f.layer] || '#555';
      var m = markerFor(f, color);
      state.allMarkers.push({ feature: f, marker: m, layerId: f.layer });
      var g = state.layerGroups[f.layer];
      if (g) g.addLayer(m);
    });

    (data.routes || []).forEach(function (r) {
      var coords = (r.stops || []).map(function (s) { return s.coords; });
      var line = L.polyline(coords, {
        color: r.color || '#444', weight: 3, opacity: 0.8,
        dashArray: (r.path_confidence && r.path_confidence !== 'documented') ? '8 6' : (r.dash || null)
      });
      // A route carries its own citation; show it, and link it to the record.
      if (r.label || r.citation) {
        var rh = '<div class="popup route-popup"><h3>' + esc(r.label || 'Route') + '</h3>';
        if (r.path_confidence && r.path_confidence !== 'documented')
          rh += '<p class="precision">\u2014 reconstructed route: he passed roughly this way, not a surveyed track</p>';
        if (r.citation) {
          var rrec = r.ca_record || citeToRecord(r.citation);
          rh += '<p class="source">' + esc(r.citation) + (rrec ? ' \u2014' + recordLink(rrec) : '') + '</p>';
        }
        line.bindPopup(rh + '</div>');
      }
      var g = state.layerGroups[r.layer];
      (g || map).addLayer ? (g ? g.addLayer(line) : line.addTo(map)) : line.addTo(map);
      state.routeLines.push(line);
      (r.stops || []).forEach(function (s) {
        var m = markerFor(s, r.color || '#444');
        state.allMarkers.push({ feature: s, marker: m, layerId: r.layer });
        if (g) g.addLayer(m); else m.addTo(map);
      });
    });

    var lc = L.control.layers(baseLayers, overlays, { collapsed: true }).addTo(map);
    if (window.innerWidth >= 700) lc.expand();

    // opacity slider for the period chart — visible only while the chart layer is on
    if (histOverlay) {
      var startOp = data.historical_overlay.opacity != null ? data.historical_overlay.opacity : 0.7;
      var opCtl = L.control({ position: 'bottomright' });
      opCtl.onAdd = function () {
        var box = el('div', 'hist-opacity');
        box.innerHTML = '<label>Chart opacity</label>';
        var s = el('input'); s.type = 'range'; s.min = 0; s.max = 1; s.step = 0.05; s.value = startOp;
        s.setAttribute('aria-label', 'Historical chart opacity');
        s.addEventListener('input', function () { histOverlay.setOpacity(+this.value); });
        box.appendChild(s);
        box.style.display = 'none';
        L.DomEvent.disableClickPropagation(box);
        histSliderEl = box;
        return box;
      };
      opCtl.addTo(map);
      map.on('overlayadd', function (e) { if (e.layer === histOverlay && histSliderEl) histSliderEl.style.display = 'block'; });
      map.on('overlayremove', function (e) { if (e.layer === histOverlay && histSliderEl) histSliderEl.style.display = 'none'; });
    }

    buildControls(data);
    applyFilters();

    // permalink: #feature-id opens + pans
    function openHash() {
      var id = decodeURIComponent(location.hash.slice(1));
      if (!id) return;
      state.allMarkers.some(function (rec) {
        if (rec.feature.id === id) {
          // zoom past the clustering cutoff so the marker stands alone, then open
          var open = function () { setTimeout(function () { rec.marker.openPopup(); }, 150); };
          if (map.getZoom() >= 10) { open(); }
          else { map.once('moveend zoomend', open); }
          map.setView(rec.feature.coords, Math.max(map.getZoom(), 10));
          return true;
        }
      });
    }
    window.addEventListener('hashchange', openHash);
    openHash();
  }

  fetch(DATA_URL).then(function (r) {
    if (!r.ok) throw new Error(r.status);
    return r.json();
  }).then(init).catch(function (e) {
    document.getElementById('map').innerHTML =
      '<p class="load-error">Could not load map data (' + esc(e.message) + ').</p>';
  });
})();


// --- diseño lightbox (in-page overlay, closeable) ---
window.__disenoLB = function (imgEl) {
  var src = imgEl.getAttribute('data-full') || imgEl.src;
  var cap = imgEl.getAttribute('title') || '';
  var ov = document.getElementById('diseno-lightbox');
  if (!ov) {
    ov = document.createElement('div'); ov.id = 'diseno-lightbox';
    ov.innerHTML = '<button id="dlb-x" aria-label="Close (Esc)" title="Close">\u00d7</button>' +
                   '<img id="dlb-img" alt="Diseño"><div id="dlb-cap"></div>';
    document.body.appendChild(ov);
    var hide = function () { ov.style.display = 'none'; };
    ov.addEventListener('click', function (e) { if (e.target === ov || e.target.id === 'dlb-x') hide(); });
    document.addEventListener('keydown', function (e) { if (e.key === 'Escape') hide(); });
  }
  document.getElementById('dlb-img').src = src;
  document.getElementById('dlb-cap').textContent = cap;
  ov.style.display = 'flex';
};
