#!/usr/bin/env python3
"""Generate the static, crawlable layer of the ranchos portal.

WHY THIS EXISTS. index.html is a hash-routed single-page app: its six tabs all
live at one URL, so 673 ranchos, 27 dynasties and 38 brands are invisible to
search engines (a fragment is not an address). This script emits real pages at
real URLs alongside the app. It never modifies index.html; it only reads the
DATA / GEN / BRANDS objects out of it, so the static pages can never drift from
what the app shows. Re-run after any data change, then run verify-links.sh.

Usage:
    python3 build_pages.py            # write into the repo
    python3 build_pages.py /tmp/out   # dry run into a scratch dir
"""
import datetime
import html
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else ROOT
SITE = 'https://ranchos.archivesofcalifornia.com'
TODAY = datetime.date.today().isoformat()

CITE = ('Coyne, Aodhan. <i>Ranchos of California: the Spanish and Mexican land grants '
        'of Alta California</i>. archivesofcalifornia.com, ' + TODAY[:4] + '.')


def esc(s):
    return html.escape(str(s if s is not None else ''), quote=True)


def load():
    """Read the three data objects out of the app. Single source of truth."""
    s = open(os.path.join(ROOT, 'index.html'), encoding='utf-8').read()

    def grab(name):
        m = re.search(r'(?:const|var|let)\s+%s\s*=\s*' % name, s)
        i = s.index('{' if s[m.end()] == '{' else '[', m.end())
        return json.JSONDecoder().raw_decode(s[i:])[0]

    return grab('DATA'), grab('GEN'), grab('BRANDS')


def write(relpath, text):
    p = os.path.join(OUT, relpath)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    if '—' in text:
        raise SystemExit('REFUSING to write an em dash into ' + relpath)
    with open(p, 'w', encoding='utf-8') as f:
        f.write(text)
    return p


def page(title, desc, canon, body, ld=None):
    ldtag = ''
    if ld:
        ldtag = ('<script type="application/ld+json">'
                 + json.dumps(ld, ensure_ascii=False).replace('</', '<\\/') + '</script>\n')
    return (
        '<!DOCTYPE html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        f'<title>{esc(title)}</title>\n'
        f'<meta name="description" content="{esc(desc)}">\n'
        f'<link rel="canonical" href="{canon}">\n'
        '<meta property="og:type" content="article">\n'
        f'<meta property="og:title" content="{esc(title)}">\n'
        f'<meta property="og:description" content="{esc(desc)}">\n'
        f'<meta property="og:url" content="{canon}">\n'
        '<link rel="icon" href="/assets/favicon.svg" type="image/svg+xml">\n'
        '<link rel="stylesheet" href="/assets/css/pages.css">\n'
        + ldtag +
        '</head>\n<body>\n'
        '<header class="top"><a class="seal" href="/"><img src="/assets/ranchos-brand.svg" alt="" width="34" height="34"></a>'
        '<a class="wordmark" href="/">Ranchos de Alta California</a>'
        '<nav><a href="/#map">Map</a><a href="/register/">Register</a><a href="/dynasties/">Dynasties</a>'
        '<a href="/brands/">Brands</a><a href="/#dz">Dise&ntilde;os</a><a href="/#data">Sources</a></nav></header>\n'
        '<main>\n' + body + '\n</main>\n'
        '<footer><p>' + CITE + '</p>'
        '<p>Catalog data CC BY 4.0. Boundaries and land-case data from the ECAI/UCSD Spanish and Mexican '
        'Land Grants dataset; dise&ntilde;os from the Bancroft Library. Always verify a grant against the '
        'cited record before relying on it. Generated ' + TODAY + '.</p>'
        '<p><a href="/">Return to the interactive portal</a></p></footer>\n</body>\n</html>\n')


CSS = """/* Static-page layer for the ranchos portal. Tokens copied verbatim from the
   app's inline theme so the generated pages match it. Do not edit by hand:
   this file is emitted by build_pages.py. */
:root{
  --ground:#141009; --top:#0E0A05; --card:#1A130B; --card-2:#20180E; --stripe:#181109;
  --ink:#EEE3CB; --ink-soft:#B9AC8C; --ink-faint:#8B7E60;
  --rule:#39301E; --rule-2:#2A2214;
  --gold:#D6A64E; --gold-deep:#E8C77B; --verm:#C24A34; --oak:#8FA06A;
  --disp:"Baskerville","Hoefler Text","Palatino Linotype",Palatino,Georgia,serif;
  --serif:"Iowan Old Style","Palatino Linotype",Palatino,"Book Antiqua",Georgia,serif;
  --body:Charter,"Iowan Old Style",Georgia,Cambria,serif;
  --mono:ui-monospace,"SF Mono",Menlo,Consolas,monospace;
}
*{box-sizing:border-box}
body{margin:0;background:var(--ground);color:var(--ink);font-family:var(--body);font-size:17px;line-height:1.6}
a{color:var(--gold)}
a:hover{color:var(--gold-deep)}
.top{display:flex;align-items:center;gap:0 16px;flex-wrap:wrap;padding:9px 22px;
  background:var(--top);border-bottom:1px solid var(--rule)}
.top .seal{display:flex;line-height:0}
.wordmark{font-family:var(--disp);font-size:19px;color:var(--gold);text-decoration:none;letter-spacing:.02em}
.top nav{display:flex;flex-wrap:wrap;margin-left:auto}
.top nav a{font-family:var(--mono);font-size:10px;letter-spacing:.1em;text-transform:uppercase;
  color:var(--ink-faint);text-decoration:none;padding:8px 11px}
.top nav a:hover{color:var(--gold)}
main{max-width:900px;margin:0 auto;padding:26px 22px 40px}
h1{font-family:var(--disp);font-size:33px;line-height:1.15;color:var(--gold);margin:0 0 6px}
h2{font-family:var(--disp);font-size:22px;color:var(--gold-deep);margin:30px 0 8px;
  border-bottom:1px solid var(--rule-2);padding-bottom:5px}
.kicker{font-family:var(--mono);font-size:11px;letter-spacing:.12em;text-transform:uppercase;
  color:var(--ink-faint);margin:0 0 16px}
.summ{font-size:18px;color:var(--ink)}
dl.facts{display:grid;grid-template-columns:auto 1fr;gap:0;margin:18px 0;
  border-top:1px solid var(--rule-2)}
dl.facts dt{font-family:var(--mono);font-size:10.5px;letter-spacing:.1em;text-transform:uppercase;
  color:var(--ink-faint);padding:10px 18px 10px 0;border-bottom:1px solid var(--rule-2);white-space:nowrap}
dl.facts dd{margin:0;padding:10px 0;border-bottom:1px solid var(--rule-2);color:var(--ink)}
.ok{color:var(--oak);font-weight:700}
.no{color:var(--verm);font-weight:700}
.disenos{display:flex;flex-wrap:wrap;gap:10px;margin:12px 0}
.disenos a{display:block;line-height:0;border:1px solid var(--rule);background:var(--card)}
.disenos img{height:132px;width:auto;display:block}
ul.plain{list-style:none;padding:0}
ul.plain li{padding:7px 0;border-bottom:1px solid var(--rule-2)}
ul.src li{font-size:15px;color:var(--ink-soft)}
table{border-collapse:collapse;width:100%;font-size:15px;margin-top:10px}
th{font-family:var(--mono);font-size:10px;letter-spacing:.1em;text-transform:uppercase;
  color:var(--ink-faint);text-align:left;padding:9px 10px;border-bottom:1px solid var(--rule)}
td{padding:9px 10px;border-bottom:1px solid var(--rule-2);vertical-align:top}
tr:nth-child(even) td{background:var(--stripe)}
.cols{columns:2;column-gap:26px}
@media(max-width:640px){.cols{columns:1}h1{font-size:26px}dl.facts{grid-template-columns:1fr}
  dl.facts dt{padding-bottom:0;border-bottom:none}}
.brandgrid{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:14px}
.brandcard{background:#fff;border:1px solid var(--rule);padding:12px;text-align:center}
.brandcard img{width:100%;height:96px;object-fit:contain}
.brandcard .cap{font-size:12px;color:#222;margin-top:7px;line-height:1.35}
footer{max-width:900px;margin:0 auto;padding:18px 22px 50px;border-top:1px solid var(--rule);
  font-size:13px;color:var(--ink-faint)}
footer p{margin:5px 0}
"""


def slug(s):
    s = re.sub(r'[^A-Za-z0-9]+', '-', s.strip().lower()).strip('-')
    return s or 'x'


def main():
    D, G, B = load()
    recs = D['records']
    eras = {l['id']: l['label'] for l in D['legend']}
    mapped = [r for r in recs if r.get('mapped')]
    by_county = {}
    for r in mapped:
        by_county.setdefault(r.get('county') or '', []).append(r)

    fam_slug = {f: slug(f) for f in G}
    fams_by_len = sorted(G, key=len, reverse=True)
    brand_by_search = {}
    for b in B['brands']:
        brand_by_search.setdefault((b.get('search') or '').lower(), b)

    urls = [SITE + '/', SITE + '/register/', SITE + '/dynasties/', SITE + '/brands/']

    # ---------- per-rancho pages ----------
    for r in mapped:
        name, rid = r['name'], r['id']
        county = r.get('county') or ''
        year = str(r.get('year') or '')
        gov, grantee = r.get('governor') or '', r.get('grantee') or ''
        canon = f'{SITE}/r/{rid}.html'
        # Only private grants take the "Rancho" prefix. Pueblo commons, ex-mission
        # lands, presidios and city lands were not ranchos and must not be labelled as one.
        is_grant = r.get('era') not in ('pueblo', 'mission', 'presidio')
        already = name.lower().startswith(('rancho', 'mission', 'pueblo', 'presidio',
                                           'ex-mission', 'city lands', 'ex mission'))
        title = f'Rancho {name}' if (is_grant and not already) else name
        headline = f'{title}{" (" + year + ")" if year else ""}'
        desc = (r.get('summary') or
                f'{title}, a land grant of {county or "Alta California"}'
                + (f' granted {year}' if year else '')
                + (f' by Governor {gov}' if gov else '')
                + (f' to {grantee}' if grantee else '') + '.')[:300]

        facts = []
        if year:
            facts.append(('Granted', esc(year) + (f' by Governor {esc(gov)}' if gov else '')))
        if grantee:
            facts.append(('Grantee', esc(grantee)))
        size = []
        if r.get('acres'):
            size.append(f'{r["acres"]:,} acres' if isinstance(r['acres'], (int, float)) else esc(r['acres']) + ' acres')
        if r.get('leagues'):
            size.append(esc(r['leagues']) + ' square leagues')
        if size:
            facts.append(('Size', ', '.join(size)))
        if county:
            facts.append(('County', esc(county) + ' County, California'))
        if r.get('era') in eras:
            facts.append(('Period', esc(eras[r['era']])))
        if r.get('land_case'):
            facts.append(('U.S. land case', esc(r['land_case']) + ', Board of Land Commissioners, 1852'))
        if r.get('outcome'):
            cls = 'no' if re.search(r'reject', r['outcome'], re.I) else 'ok'
            facts.append(('Adjudication', f'<span class="{cls}">{esc(r["outcome"])}</span>'))

        body = [f'<p class="kicker">{esc(county + " County" if county else "Alta California")}'
                f'{" &middot; " + esc(eras.get(r.get("era"), "")) if r.get("era") in eras else ""}</p>',
                f'<h1>{esc(headline)}</h1>']
        if r.get('summary'):
            body.append(f'<p class="summ">{esc(r["summary"])}</p>')
        body.append('<dl class="facts">' + ''.join(
            f'<dt>{k}</dt><dd>{v}</dd>' for k, v in facts) + '</dl>')

        if r.get('mapped'):
            body.append(f'<p><a href="/#map">Open {esc(name)} on the interactive boundary map</a>, '
                        'where the grant is drawn against its neighbours.</p>')

        ds = r.get('disenos') or []
        if ds:
            body.append(f'<h2>Dise&ntilde;os</h2><p>The hand-drawn grant maps filed with this claim '
                        f'({len(ds)} held).</p><div class="disenos">')
            for d in ds[:24]:
                body.append(f'<a href="{esc(d.get("img"))}"><img src="{esc(d.get("thumb"))}" '
                            f'alt="Dise&ntilde;o of {esc(name)}" loading="eager"></a>')
            body.append('</div>')

        bsearch = (name or '').lower()
        br = brand_by_search.get(bsearch)
        if br:
            body.append('<h2>Cattle brand</h2><div class="brandgrid"><div class="brandcard">'
                        f'<img src="/{esc(br["file"])}" alt="Cattle brand of {esc(br.get("owner"))}">'
                        f'<div class="cap">{esc(br.get("owner"))}'
                        f'{", " + esc(br.get("year")) if br.get("year") else ""}<br>{esc(br.get("src"))}</div>'
                        '</div></div>')

        fam = next((f for f in fams_by_len if grantee and f.lower() in grantee.lower()), None)
        if fam:
            body.append(f'<h2>Family</h2><p>The grantee belongs to the '
                        f'<a href="/dynasties/{fam_slug[fam]}.html">{esc(fam)} family</a>, one of the '
                        'landholding dynasties of Mexican California.</p>')

        srcs = r.get('sources') or []
        if srcs:
            body.append('<h2>Sources</h2><ul class="plain src">')
            for s_ in srcs:
                c = esc(s_.get('c'))
                body.append(f'<li><a href="{esc(s_["u"])}">{c}</a></li>' if s_.get('u') else f'<li>{c}</li>')
            body.append('</ul>')

        sib = [x for x in by_county.get(county, []) if x['id'] != rid][:14]
        if sib:
            body.append(f'<h2>Other grants in {esc(county)} County</h2><ul class="plain cols">')
            for x in sib:
                body.append(f'<li><a href="/r/{x["id"]}.html">{esc(x["name"])}</a>'
                            f'{" (" + esc(str(x["year"])) + ")" if x.get("year") else ""}</li>')
            body.append('</ul>')
        body.append('<p><a href="/register/">Back to the full register of 673 grants and claims</a></p>')

        ld = {'@context': 'https://schema.org', '@type': 'Place', 'name': title,
              'description': desc, 'url': canon,
              'additionalType': 'https://www.wikidata.org/wiki/Q1080794'}
        if county:
            ld['containedInPlace'] = {'@type': 'AdministrativeArea', 'name': county + ' County, California'}
        if r.get('coords'):
            ld['geo'] = {'@type': 'GeoCoordinates', 'latitude': r['coords'][0], 'longitude': r['coords'][1]}
        write(f'r/{rid}.html', page(f'{headline} | Ranchos of California', desc, canon, '\n'.join(body), ld))
        urls.append(canon)

    # ---------- register ----------
    rows = []
    for r in sorted(recs, key=lambda x: (x.get('county') or 'zz', x['name'])):
        nm = esc(r['name'])
        cell = f'<a href="/r/{r["id"]}.html">{nm}</a>' if r.get('mapped') else nm
        oc = r.get('outcome') or ''
        ocls = 'no' if re.search(r'reject', oc, re.I) else ('ok' if oc else '')
        rows.append(f'<tr id="{esc(r["id"])}"><td>{cell}</td><td>{esc(r.get("year"))}</td>'
                    f'<td>{esc(r.get("governor"))}</td><td>{esc(r.get("grantee"))}</td>'
                    f'<td>{esc(r.get("county"))}</td><td>{esc(r.get("land_case"))}</td>'
                    f'<td class="{ocls}">{esc(oc)}</td></tr>')
    c = D['counts']
    rdesc = (f'The full register of {c["total"]} Spanish and Mexican land grants and claims of Alta '
             f'California, 1769 to 1846: grant year, granting governor, grantee, county, United States '
             f'land case number and outcome, across {c["counties"]} counties.')
    rbody = ('<h1>Register of the ranchos</h1>'
             f'<p class="summ">Every grant and claim we hold: <b>{c["total"]}</b> records across '
             f'{c["counties"]} counties, of which <b>{c["mapped"]}</b> have a mapped boundary and their own '
             'page. The remaining ' + str(c['unmapped']) + ' are claims recorded in the United States land '
             'case files for which no surveyed boundary survives.</p>'
             '<table><thead><tr><th>Grant</th><th>Year</th><th>Governor</th><th>Grantee</th>'
             '<th>County</th><th>Land case</th><th>Outcome</th></tr></thead><tbody>'
             + ''.join(rows) + '</tbody></table>')
    write('register/index.html', page('Register of the ranchos | Ranchos of California', rdesc,
                                      SITE + '/register/', rbody,
                                      {'@context': 'https://schema.org', '@type': 'Dataset',
                                       'name': 'Register of the Spanish and Mexican land grants of Alta California',
                                       'description': rdesc, 'url': SITE + '/register/',
                                       'license': 'https://creativecommons.org/licenses/by/4.0/'}))

    # ---------- dynasties ----------
    dlinks = []
    for fam, f in sorted(G.items()):
        sl = fam_slug[fam]
        canon = f'{SITE}/dynasties/{sl}.html'
        mem = f.get('members') or []
        desc = (f.get('summary') or '')[:300]
        body = [f'<p class="kicker">Californio landholding families</p><h1>The {esc(fam)} family</h1>']
        if f.get('patriarch'):
            body.append(f'<p class="kicker">Patriarch: {esc(f["patriarch"])}</p>')
        if f.get('summary'):
            body.append(f'<p class="summ">{esc(f["summary"])}</p>')
        if f.get('origin'):
            body.append(f'<h2>Origin</h2><p>{esc(f["origin"])}</p>')
        if mem:
            body.append('<h2>Members</h2><table><thead><tr><th>Name</th><th>Relation</th>'
                        '<th>Ranchos</th></tr></thead><tbody>')
            for m in mem:
                body.append(f'<tr><td>{esc(m.get("name"))}</td><td>{esc(m.get("relation"))}</td>'
                            f'<td>{esc(m.get("ranchos"))}</td></tr>')
            body.append('</tbody></table>')
        if f.get('confidence'):
            body.append(f'<p class="kicker">Genealogical confidence: {esc(f["confidence"])}</p>')
        if f.get('sources'):
            src = f['sources']
            body.append('<h2>Sources</h2><ul class="plain src">' + ''.join(
                f'<li>{esc(x if isinstance(x, str) else x.get("c"))}</li>' for x in src) + '</ul>')
        body.append('<p><a href="/dynasties/">All families</a> &middot; '
                    '<a href="/register/">The full register</a></p>')
        write(f'dynasties/{sl}.html',
              page(f'The {fam} family | Ranchos of California', desc or f'The {fam} family of Mexican California.',
                   canon, '\n'.join(body),
                   {'@context': 'https://schema.org', '@type': 'Article',
                    'headline': f'The {fam} family of Mexican California',
                    'description': desc, 'url': canon,
                    'author': {'@type': 'Person', 'name': 'Aodhan Coyne'}}))
        urls.append(canon)
        dlinks.append(f'<li><a href="/dynasties/{sl}.html">{esc(fam)}</a> '
                      f'<span class="kicker" style="display:inline">{len(mem)} members</span></li>')
    ddesc = (f'The {len(G)} landholding families of Spanish and Mexican California: patriarchs, members, '
             'the ranchos they held, and the sources behind each line.')
    write('dynasties/index.html', page('Californio dynasties | Ranchos of California', ddesc,
                                       SITE + '/dynasties/',
                                       f'<h1>Californio dynasties</h1><p class="summ">{ddesc}</p>'
                                       '<ul class="plain cols">' + ''.join(dlinks) + '</ul>'))

    # ---------- brands ----------
    cards = []
    for b in B['brands']:
        cap = esc(b.get('owner') or b.get('rancho'))
        sub = ', '.join(x for x in [esc(b.get('rancho')), esc(b.get('year'))] if x)
        cards.append(f'<div class="brandcard"><img src="/{esc(b["file"])}" alt="Cattle brand, {cap}">'
                     f'<div class="cap"><b>{cap}</b><br>{sub}<br>{esc(b.get("src"))}</div></div>')
    bdesc = (f'The {len(B["brands"])} surviving cattle brands of the California ranchos and missions, '
             'traced from the county brand registers and the mission brand chart.')
    write('brands/index.html', page('Cattle brands of the ranchos | Ranchos of California', bdesc,
                                    SITE + '/brands/',
                                    f'<h1>Cattle brands</h1><p class="summ">{bdesc}</p>'
                                    '<div class="brandgrid">' + ''.join(cards) + '</div>'
                                    f'<h2>Source</h2><p>{esc(B.get("source"))}</p>'))

    write('assets/css/pages.css', CSS)
    write('sitemap.xml',
          '<?xml version="1.0" encoding="UTF-8"?>\n'
          '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
          + ''.join(f'<url><loc>{u}</loc><lastmod>{TODAY}</lastmod></url>\n' for u in urls)
          + '</urlset>\n')

    print(f'wrote into {OUT}:')
    print(f'  {len(mapped)} rancho pages, 1 register ({len(recs)} rows), '
          f'{len(G)} dynasty pages + index, 1 brands page, pages.css, sitemap.xml ({len(urls)} urls)')


if __name__ == '__main__':
    main()
