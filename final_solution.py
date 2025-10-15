#!/usr/bin/env python3
"""Clean Enhanced Airtable Dashboard

Single-file Flask app that lists tables, shows a schema-ordered grid, and
provides a basic add-record form. The table view includes a small toolbar
with Hide fields, Filter, and Sort. Client-side JS uses JSON embedded via
Jinja to avoid fragile Python f-string/JS interactions.
"""

import os
import json
import ssl
import urllib3
import requests
from datetime import datetime
from flask import Flask, render_template_string, request, jsonify
from pyairtable import Api
from dotenv import load_dotenv

load_dotenv()

# Best-effort: relax SSL verification for corporate proxies
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
ssl._create_default_https_context = ssl._create_unverified_context
os.environ.setdefault('PYTHONHTTPSVERIFY', '0')

# Patch requests to skip verification (best-effort)
_orig_req = requests.Session.request
def _noverify(self, method, url, **kwargs):
        kwargs.setdefault('verify', False)
        return _orig_req(self, method, url, **kwargs)
requests.Session.request = _noverify

AIRTABLE_TOKEN = os.getenv('AIRTABLE_TOKEN')
AIRTABLE_BASE_ID = os.getenv('AIRTABLE_BASE_ID')
if not AIRTABLE_TOKEN or not AIRTABLE_BASE_ID:
        raise RuntimeError('Set AIRTABLE_TOKEN and AIRTABLE_BASE_ID in environment')

app = Flask(__name__)

# Initialize Airtable client
try:
        api = Api(AIRTABLE_TOKEN)
        base = api.base(AIRTABLE_BASE_ID)
        try:
                _ = base.schema()
        except Exception:
                # schema may be unavailable depending on API key permissions
                pass
        print('[+] Airtable client initialized')
except Exception as e:
        print(f'[!] Airtable init error: {e}')
        api = None
        base = None


# Dashboard template (dark themed cards + banner)
_DASH = """
<!doctype html>
<html>
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Airtable Dashboard</title>
<style>
:root{--bg:#0f1724;--card:#0b1220;--muted:#9aa3b2;--accent:#7c3aed;--fg:#e6eef8;--ease: cubic-bezier(.22,.61,.36,1); --dur: 220ms}
html,body{height:100%}
html{scroll-behavior:smooth}
body{font-family:Inter,Segoe UI,Arial,Helvetica,sans-serif;margin:0;background:var(--bg);color:var(--fg);-webkit-font-smoothing:antialiased;-moz-osx-font-smoothing:grayscale}
*{-webkit-tap-highlight-color:transparent}
/* global transition defaults */
:where(a,button,input,select,textarea){transition: background-color var(--dur) var(--ease), color var(--dur) var(--ease), border-color 140ms var(--ease), box-shadow var(--dur) var(--ease), transform 120ms var(--ease)}
/* make theme toggle feel instant */
body.instant-theme *{transition: none !important}
/* custom scrollbar */
*::-webkit-scrollbar{height:10px;width:10px}
*::-webkit-scrollbar-thumb{background:rgba(255,255,255,.18);border-radius:8px}
*::-webkit-scrollbar-track{background:transparent}
/* focus visible */
:where(button,[role="button"],a,input,select,textarea):focus-visible{outline:0;box-shadow:0 0 0 2px rgba(124,58,237,.65),0 6px 18px rgba(124,58,237,.18)}
@media (prefers-reduced-motion: reduce){*,*::before,*::after{animation-duration:0.001ms !important;animation-iteration-count:1 !important;transition-duration:0.001ms !important;scroll-behavior:auto !important}}
/* light theme override */
body[data-theme="light"]{--bg:#f8fafc;--card:#ffffff;--muted:#6b7280;--accent:#7c3aed;--fg:#111827}
.banner{height:460px;background:linear-gradient(180deg,rgba(11,20,40,.95),rgba(16,24,37,.98));display:flex;align-items:center;justify-content:center;padding:32px;border-bottom:1px solid rgba(255,255,255,.03);position:relative}
.hero{max-width:1100px;width:100%;background:linear-gradient(180deg,#26343b,#222a30);padding:22px;border-radius:14px;box-shadow:0 20px 60px rgba(2,6,23,.6), 0 0 0 1px rgba(124,58,237,.22), 0 40px 120px rgba(124,58,237,.28);text-align:center;position:relative;min-height:300px;z-index:1}
.hero::after{content:"";position:absolute;inset:-44px;background:radial-gradient(ellipse at 50% -10%, rgba(124,58,237,.4), rgba(124,58,237,0) 60%), radial-gradient(ellipse at 10% 50%, rgba(59,130,246,.22), rgba(59,130,246,0) 50%), radial-gradient(ellipse at 90% 50%, rgba(234,179,8,.22), rgba(234,179,8,0) 50%);filter:blur(34px);z-index:-1;pointer-events:none}
.logo{position:absolute;left:50%;transform:translateX(-50%);top:26px;width:200px;height:200px;background-size:contain;background-repeat:no-repeat;background-position:center}
.report-title{margin-top:36px;text-align:center}
.report-title h1{font-size:40px;margin:0;color:#fff;letter-spacing:1px}
.report-title .subtitle{color:var(--muted);margin-top:10px}
/* light theme: ensure strong contrast for title area */
body[data-theme="light"] .report-title h1{color:#111827 !important}
body[data-theme="light"] .report-title .subtitle{color:#374151 !important}
/* light theme banner/hero becomes brighter */
body[data-theme="light"] .banner{background:linear-gradient(180deg,#f8fafc,#eef2ff)}
body[data-theme="light"] .hero{background:linear-gradient(180deg,#ffffff,#ffffff);box-shadow:0 12px 40px rgba(2,6,23,.08), 0 0 0 1px rgba(99,102,241,.15)}
body[data-theme="light"] .hero::after{background:radial-gradient(ellipse at 50% -10%, rgba(124,58,237,.16), rgba(124,58,237,0) 60%), radial-gradient(ellipse at 10% 50%, rgba(59,130,246,.12), rgba(59,130,246,0) 50%), radial-gradient(ellipse at 90% 50%, rgba(234,179,8,.12), rgba(234,179,8,0) 50%)}

/* responsive title and entrance animation */
@keyframes fadeScaleIn { from { opacity: 0; transform: translateY(8px) scale(.98); } to { opacity:1; transform: translateY(0) scale(1);} }
.report-title h1{animation: fadeScaleIn 420ms ease both}
@media (max-width: 800px){ .report-title h1{font-size:28px} .logo{width:130px;height:130px;top:10px} .banner{height:260px} }

/* visible count animation */
.value{transition:transform .18s ease, opacity .18s ease}
.value.anim { transform: scale(1.12); opacity: 0.9 }

/* pager */
.pager{display:flex;gap:12px;align-items:center;margin-bottom:12px}
.pager button{background:transparent;border:1px solid rgba(255,255,255,.06);color:var(--muted);padding:8px 10px;border-radius:8px;cursor:pointer}
.page-info{color:var(--muted)}
.container{max-width:1200px;margin:18px auto;padding:0 18px}
.stats{display:flex;gap:18px;margin:18px 0}
.stat{background:var(--card);padding:18px;border-radius:10px;flex:1;border:1px solid rgba(255,255,255,.03)}
.stat .label{color:var(--muted);font-size:12px}
.stat .value{font-size:22px;font-weight:700;margin-top:6px}
.search{margin:18px 0}
.search input{width:100%;padding:14px;border-radius:10px;border:1px solid rgba(255,255,255,.04);background:#071025;color:#e6eef8;transition:box-shadow .18s ease, transform .12s ease, border-color .12s ease}
.search input:focus{outline:0;box-shadow:0 8px 30px rgba(124,58,237,.12);transform:translateY(-1px);border-color:rgba(124,58,237,.6)}
body[data-theme="light"] .search input{background:#ffffff;color:#111827;border:1px solid #e5e7eb}
body[data-theme="light"] .card{color:#111827}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:18px;margin-top:18px}
.card{background:var(--card);padding:22px;border-radius:12px;min-height:140px;border:1px solid rgba(255,255,255,.03);box-shadow:0 6px 20px rgba(2,6,23,.6);color:#e6eef8}
.card h3{margin:0 0 10px 0}
.card .meta{color:var(--muted);font-size:13px;margin-top:8px}
.card .active{float:right;color:var(--accent);font-weight:600}
.footer-note{color:var(--muted);font-size:13px;margin-top:14px}
a.card{text-decoration:none}
@media(max-width:800px){.stats{flex-direction:column}}
/* subtle hover lift and smooth appearance */
.card{transition:transform var(--dur) var(--ease),opacity var(--dur) var(--ease);will-change:transform,opacity}
.card:hover{transform:translateY(-6px)}
.card[style*="opacity: 0"]{opacity:0}
.card{opacity:1}
/* small copyright/footer */
.site-footer{color:var(--muted);font-size:12px;margin-top:12px;text-align:center}
/* theme toggle */
.theme-toggle{position:fixed;top:14px;right:14px;display:flex;align-items:center;gap:8px;background:rgba(0,0,0,.25);border:1px solid rgba(255,255,255,.12);color:#fff;padding:6px 10px;border-radius:999px;cursor:pointer;backdrop-filter:blur(6px); z-index:1000; transition:transform .12s ease, box-shadow .16s ease, background .16s ease}
.theme-toggle:hover{ transform: translateY(-1px); box-shadow:0 10px 30px rgba(2,6,23,.25) }
body[data-theme="light"] .theme-toggle{ background:rgba(255,255,255,.65); color:#111827; border-color:rgba(0,0,0,.08) }
</style>
</head>
<body>
                                <div style="position:absolute;right:16px;top:16px;z-index:10">
                                        <button id="themeToggle" class="theme-toggle" title="Toggle theme" aria-label="Toggle theme">
                                                <span id="themeIcon" aria-hidden="true"></span>
                                                <span id="themeLabel" style="font-size:12px"></span>
                                        </button>
                                </div>
                        <div class="banner">
                                <div class="hero">
                                        <div class="logo" style="background-image:url('https://trojanconstruction.group/storage/subsidiaries/August2022/PG0Hzw1iVnUOQAiyYYuS.png')"></div>
                                        <!-- title moved below the banner -->
                                </div>
                        </div>

                                <div class="container">
                                        <div class="report-title" style="margin-top:18px;margin-bottom:18px;text-align:center">
                                                <h1 style="margin:0;font-size:44px;letter-spacing:1px">HSE STATISTICS REPORT</h1>
                                                <div class="subtitle" style="color:var(--muted);margin-top:8px">Streamlined Data Management Interface</div>
                                        </div>
                <div class="stats">
                        <div class="stat">
                                <div class="label">TOTAL TABLES</div>
                                <div class="value">{{ tables|length }}</div>
                        </div>
                        <div class="stat">
                                <div class="label">TOTAL RECORDS</div>
                                <div class="value">{{ total_records }}</div>
                        </div>
                        <div class="stat">
                                <div class="label">VISIBLE TABLES</div>
                                <div class="value"><span id="visibleCount">{{ tables|length }}</span></div>
                        </div>
                </div>

                <div class="search"><input id="tableSearch" placeholder="Search tables... (Press / to focus)" aria-label="Search tables"></div>

                <div class="pager" id="pagerTop" style="display:none">
                  <button id="prevPage" aria-label="Previous page">‹</button>
                  <div class="page-info" id="pageInfo">Page 1</div>
                  <button id="nextPage" aria-label="Next page">›</button>
                </div>

                <div class="grid" id="tableGrid">
                {% for t in tables %}
                        <a class="card" data-name="{{ t.name|e }}" data-count="{{ t.count }}" href="/table/{{ t.name|urlencode }}">
                                <div style="display:flex;align-items:center;gap:12px">
                                    <div class="card-icon" aria-hidden="true">
                                      <svg width="36" height="36" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><rect x="3" y="4" width="18" height="6" rx="1.5" fill="#7C5CFF"/><rect x="3" y="14" width="8" height="6" rx="1.5" fill="#5CE1E6"/><rect x="14" y="14" width="7" height="6" rx="1.5" fill="#FFD166"/></svg>
                                    </div>
                                    <div style="flex:1;min-width:0">
                                        <h3 style="margin:0;font-size:18px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">{{ t.name }}</h3>
                                        <div class="meta">{{ t.count }} records</div>
                                    </div>
                                </div>
                                <div class="footer-note">ID: {{ t.id }}</div>
                        </a>
                {% endfor %}
                </div>
                <div class="pager" id="pagerBottom" style="display:none">
                  <button id="prevPageB" aria-label="Previous page">‹</button>
                  <div class="page-info" id="pageInfoB">Page 1</div>
                  <button id="nextPageB" aria-label="Next page">›</button>
                </div>
                <div style="margin-top:10px;color:var(--muted);font-size:13px">Last updated: <strong>{{ last_updated }}</strong></div>
                <div class="site-footer">&copy; 2025 HSE TROJAN CONSTRUCTION GROUP &nbsp;&middot;&nbsp; Developed by Elius</div>
                </div>

                                                                <script>
                                                                        (function(){
                                                                                const KEY='theme';
                                                                                const saved = localStorage.getItem(KEY) || 'dark';
                                                                                document.body.dataset.theme = saved;
                                                                                const icon = document.getElementById('themeIcon');
                                                                                const label = document.getElementById('themeLabel');
                                                                                function render(){
                                                                                        const t = document.body.dataset.theme;
                                                                                        label.textContent = t==='dark'?'Dark':'Light';
                                                                                        icon.innerHTML = t==='dark'
                                                                                          ? '<svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor" xmlns="http://www.w3.org/2000/svg"><path d="M21 12.79A9 9 0 1111.21 3 7 7 0 0021 12.79z"/></svg>'
                                                                                          : '<svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor" xmlns="http://www.w3.org/2000/svg"><path d="M6.76 4.84l-1.8-1.79-1.41 1.41 1.79 1.8 1.42-1.42zM1 13h3v-2H1v2zm10-9h2V1h-2v3zm7.04 2.46l1.79-1.8-1.41-1.41-1.8 1.79 1.42 1.42zM17 13h3v-2h-3v2zm-5 8h2v-3h-2v3zm-7.66-2.34l1.41 1.41 1.8-1.79-1.42-1.42-1.79 1.8zM20 20l1.41 1.41 1.41-1.41-1.41-1.41L20 20zM12 6a6 6 0 100 12A6 6 0 0012 6z"/></svg>';
                                                                                }
                                                                                function toggleTheme(){
                                                                                        const next = document.body.dataset.theme==='dark'?'light':'dark';
                                                                                        document.body.classList.add('instant-theme');
                                                                                        document.body.dataset.theme = next;
                                                                                        try{ localStorage.setItem(KEY,next); }catch(e){}
                                                                                        render();
                                                                                        setTimeout(()=> document.body.classList.remove('instant-theme'), 120);
                                                                                }
                                                                                const btn = document.getElementById('themeToggle');
                                                                                btn?.addEventListener('pointerdown', (e)=>{ e.preventDefault(); toggleTheme(); });
                                                                                btn?.addEventListener('touchstart', (e)=>{ e.preventDefault(); toggleTheme(); }, {passive:false});
                                                                                btn?.addEventListener('click', (e)=>{ e.preventDefault(); toggleTheme(); });
                                                                                render();
                                                                        })();
                                                                        
                                                                        (function(){
                                                                                const searchEl = document.getElementById('tableSearch');
                                                                                const grid = document.getElementById('tableGrid');
                                                                                const cards = Array.from(grid.querySelectorAll('.card'));
                                                                                const visibleEl = document.getElementById('visibleCount');
                                                                                const pageSize = 24;
                                                                                let currentPage = 1;

                                                                                function animateCount(){
                                                                                        visibleEl.classList.add('anim');
                                                                                        setTimeout(()=> visibleEl.classList.remove('anim'), 350);
                                                                                }

                                                                                function setVisibleCount(n){
                                                                                        if(!visibleEl) return;
                                                                                        visibleEl.textContent = n;
                                                                                        animateCount();
                                                                                }

                                                                                function filterMatched(){
                                                                                        const q = (searchEl.value||'').toLowerCase().trim();
                                                                                        return cards.filter(c => c.dataset.name.toLowerCase().indexOf(q) !== -1);
                                                                                }

                                                                                function render(page){
                                                                                        const matched = filterMatched();
                                                                                        const total = matched.length;
                                                                                        const totalPages = Math.max(1, Math.ceil(total / pageSize));
                                                                                        currentPage = Math.min(Math.max(1, page), totalPages);
                                                                                        cards.forEach(c=> c.style.display = 'none');
                                                                                        const start = (currentPage-1)*pageSize;
                                                                                        const slice = matched.slice(start, start + pageSize);
                                                                                        slice.forEach((c,i)=>{ c.style.display='block'; c.style.opacity=0; c.style.transform='translateY(6px)'; setTimeout(()=>{ c.style.transition='transform .28s ease, opacity .28s ease'; c.style.opacity=1; c.style.transform='translateY(0)'; }, 40 + i*10); });

                                                                                        // show/hide pagers
                                                                                        const showPager = total > pageSize;
                                                                                        document.getElementById('pagerTop').style.display = showPager ? 'flex' : 'none';
                                                                                        document.getElementById('pagerBottom').style.display = showPager ? 'flex' : 'none';
                                                                                        document.getElementById('pageInfo').textContent = `Page ${currentPage} / ${totalPages}`;
                                                                                        document.getElementById('pageInfoB').textContent = `Page ${currentPage} / ${totalPages}`;

                                                                                        setVisibleCount(total);
                                                                                }

                                                                                function wire(idPrev, idNext){
                                                                                        const prev = document.getElementById(idPrev);
                                                                                        const next = document.getElementById(idNext);
                                                                                        prev?.addEventListener('click', ()=> render(currentPage-1));
                                                                                        next?.addEventListener('click', ()=> render(currentPage+1));
                                                                                }
                                                                                wire('prevPage','nextPage'); wire('prevPageB','nextPageB');

                                                                                searchEl?.addEventListener('input', ()=> render(1));
                                                                                document.addEventListener('keydown', e=>{ if(e.key==='/' && document.activeElement.tagName!=='INPUT'){ e.preventDefault(); searchEl.focus(); searchEl.select(); } });

                                                                                // initial
                                                                                render(1);
                                                                        })();
                                                                </script>
</body>
</html>
"""


# Table view template with toolbar and client-side behaviors
_TABLE = """
<!doctype html>
<html>
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{{ table_name }}</title>
<style>
/* Theme variables */
:root{--bg:#0f1724;--card:#0b1220;--fg:#e6eef8;--muted:#9aa3b2;--accent:#7c3aed;--border:rgba(255,255,255,.08);--ease:cubic-bezier(.22,.61,.36,1);--dur:220ms}
body[data-theme="light"]{--bg:#f3f4f6;--card:#ffffff;--fg:#111827;--muted:#6b7280;--accent:#7c3aed;--border:#e6e9ef}

/* Page layout */
html{scroll-behavior:smooth}
body{font-family:Inter,Segoe UI,Arial,Helvetica,sans-serif;margin:0;background:var(--bg);color:var(--fg);-webkit-font-smoothing:antialiased;-moz-osx-font-smoothing:grayscale}
*{-webkit-tap-highlight-color:transparent}
:where(a,button,input,select,textarea){transition: background-color var(--dur) var(--ease), color var(--dur) var(--ease), border-color 140ms var(--ease), box-shadow var(--dur) var(--ease), transform 120ms var(--ease)}
/* instant theme toggle */
body.instant-theme *{transition: none !important}
*::-webkit-scrollbar{height:10px;width:10px}
*::-webkit-scrollbar-thumb{background:rgba(0,0,0,.22);border-radius:8px}
*::-webkit-scrollbar-track{background:transparent}
:where(button,[role="button"],a,input,select,textarea):focus-visible{outline:0;box-shadow:0 0 0 2px rgba(124,58,237,.55),0 6px 18px rgba(124,58,237,.18)}
@media (prefers-reduced-motion: reduce){*,*::before,*::after{animation-duration:0.001ms !important;animation-iteration-count:1 !important;transition-duration:0.001ms !important;scroll-behavior:auto !important}}
.top-tabs{background:transparent;padding:8px 12px;border-bottom:0}
body[data-theme="light"] .top-tabs{background:transparent;border-bottom:0}
.tabs{display:flex;gap:8px;overflow:auto;padding:6px 4px}
.tab{padding:8px 14px;border-radius:6px;background:transparent;color:#6b2e8a;font-weight:600;border:1px solid rgba(107,46,138,.08)}
.tab.active{background:#f6eef8;border-color:transparent;box-shadow:inset 0 -2px 0 rgba(107,46,138,.06)}
.tab{transition:background var(--dur) var(--ease), color var(--dur) var(--ease), border-color 140ms var(--ease), box-shadow var(--dur) var(--ease)}
.tab:hover{transform:translateY(-1px)}
/* theme-aware tabs */
body[data-theme="dark"] .tab{background:transparent;color:#c4b5fd;border:1px solid rgba(124,58,237,.18)}
body[data-theme="dark"] .tab.active{background:rgba(124,58,237,.14);border-color:rgba(124,58,237,.28);box-shadow:inset 0 -2px 0 rgba(124,58,237,.22)}
body[data-theme="light"] .tab{background:#ffffff;color:#111827;border:1px solid #e5e7eb}
body[data-theme="light"] .tab.active{background:#f3f4ff;border-color:#c7d2fe;box-shadow:inset 0 -2px 0 rgba(99,102,241,.15)}
.page{padding:18px}

header{display:flex;justify-content:space-between;align-items:center;margin-bottom:8px}
header h2{margin:0;font-size:18px}
header .muted{color:var(--muted);font-size:13px}

.toolbar{display:flex;gap:10px;align-items:center;margin:10px 0;padding:10px;background:var(--card);border-radius:8px}
body[data-theme="light"] .toolbar{background:#f9fafb}
.tool{display:flex;gap:8px;align-items:center;padding:6px 10px;border-radius:8px;background:transparent;color:var(--fg);border:1px solid var(--border);cursor:pointer}
body[data-theme="light"] .tool{background:#ffffff;color:#111827;border:1px solid #e5e7eb}
body[data-theme="dark"] .tool{background:rgba(255,255,255,.02);color:var(--fg);border:1px solid rgba(255,255,255,.1)}
.tool .icon{opacity:0.8}
.tool svg path,.tool svg rect,.tool svg circle{fill:currentColor}

/* responsive heading */
@media(max-width:720px){ header h2{font-size:16px} .tool{padding:6px 8px;font-size:13px} }

/* Smooth form styles (apply to all forms) */
.form-smooth .form-row{display:flex;flex-direction:column;gap:6px}
.form-smooth .form-label{font-size:13px;color:#374151}
.form-smooth input,.form-smooth select,.form-smooth textarea{padding:10px 12px;border:1px solid var(--border);border-radius:8px;background:var(--card);color:var(--fg);transition:box-shadow .18s ease, border-color .14s ease, transform .08s ease}
.form-smooth input::placeholder,.form-smooth textarea::placeholder{color:var(--muted)}
.form-smooth input:focus,.form-smooth select:focus,.form-smooth textarea:focus{outline:0;border-color:#7c3aed;box-shadow:0 8px 30px rgba(124,58,237,.12)}
/* explicit overrides per theme for max clarity */
body[data-theme="light"] .form-smooth input, body[data-theme="light"] .form-smooth select, body[data-theme="light"] .form-smooth textarea{background:#ffffff;color:#111827;border-color:#e5e7eb}
body[data-theme="dark"] .form-smooth input, body[data-theme="dark"] .form-smooth select, body[data-theme="dark"] .form-smooth textarea{background:var(--card);color:var(--fg);border-color:rgba(255,255,255,.14)}
.form-smooth button,.tool,.add-btn{transition:background .16s ease, color .12s ease, transform .08s ease, box-shadow .16s ease}
.form-smooth button:hover,.tool:hover,.add-btn:hover{transform:translateY(-1px)}
.form-smooth button:active,.tool:active,.add-btn:active{transform:translateY(0)}
.field-error{color:#dc2626;font-size:12px;min-height:16px;margin-top:4px}

/* Density toggle */
body[data-density="compact"] th, body[data-density="compact"] td{padding:6px 10px}
body[data-density="compact"] .form-smooth input, body[data-density="compact"] .form-smooth select, body[data-density="compact"] .form-smooth textarea{padding:6px 8px;border-radius:6px}
body[data-density="compact"] .add-btn{padding:6px 10px}

.table-wrap{background:var(--card);border-radius:8px;box-shadow:0 6px 18px rgba(15,23,42,.06);overflow:auto}
body[data-theme="light"] .table-wrap{background:#ffffff;box-shadow:0 8px 24px rgba(2,6,23,.06)}
table{width:100%;border-collapse:collapse}
.hdr-sort{opacity:0.45;margin-left:8px;font-size:12px}
.cell-trunc{max-width:320px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.sort-asc .hdr-sort{color:#1f6feb}
.sort-desc .hdr-sort{color:#1f6feb}
th,td{padding:12px 16px;border-bottom:1px solid #f1f5f9;text-align:left}
thead th{position:sticky;top:0;background:var(--card);border-bottom:2px solid var(--border);color:var(--fg)}
thead.stuck th{box-shadow:0 4px 16px rgba(2,6,23,.12)}
/* lighter header surface in light mode for readability */
body[data-theme="light"] #gridTable thead th{background:#f9fafb}
.row-index{width:64px;text-align:center;color:var(--muted)}
.row-select{width:56px;text-align:center}
tbody tr:hover{background:rgba(0,0,0,.02)}

/* Inline editors inside grid cells reflect theme */
#gridBody td[data-col-index] input,
#gridBody td[data-col-index] textarea,
#gridBody td[data-col-index] select{width:100%;box-sizing:border-box;background:var(--card);color:var(--fg);border:1px solid var(--border);border-radius:6px;padding:6px 8px}
body[data-theme="light"] #gridBody td[data-col-index] input,
body[data-theme="light"] #gridBody td[data-col-index] textarea,
body[data-theme="light"] #gridBody td[data-col-index] select{background:#ffffff;color:#111827;border-color:#e5e7eb}

/* bottom add bar */
.add-bar{position:fixed;left:0;right:0;bottom:0;background:var(--card);border-top:1px solid var(--border);padding:10px 18px;display:flex;justify-content:flex-start;align-items:center;gap:10px}
.add-btn{background:var(--accent);color:#fff;padding:8px 12px;border-radius:8px;border:0;cursor:pointer;font-weight:600}

/* small modal & overlay */
.overlay{position:fixed;left:0;top:0;right:0;bottom:0;background:rgba(0,0,0,.24);display:none;opacity:0;transition:opacity .22s ease;z-index:30}
.overlay.show{display:block;opacity:1}
.modal{position:fixed;left:50%;top:48%;transform:translate(-50%,-46%);background:var(--card);color:var(--fg);padding:14px;border-radius:8px;box-shadow:0 10px 30px rgba(2,6,23,.12);display:block;opacity:0;transition:opacity .22s ease,transform .22s ease;z-index:40}
.modal.show{opacity:1;transform:translate(-50%,-50%)}

/* Banner shared styles (like dashboard) */
.banner{height:320px;background:linear-gradient(180deg,rgba(11,20,40,.95),rgba(16,24,37,.98));display:flex;align-items:center;justify-content:center;padding:24px;border-bottom:1px solid rgba(255,255,255,.03);position:relative}
.banner{transition:background 240ms var(--ease)}
.hero{max-width:1100px;width:100%;background:linear-gradient(180deg,#26343b,#222a30);padding:20px;border-radius:14px;box-shadow:0 20px 60px rgba(2,6,23,.6), 0 0 0 1px rgba(124,58,237,.18), 0 30px 100px rgba(124,58,237,.22);text-align:center;position:relative;min-height:220px;z-index:1}
body[data-theme="light"] .banner{background:linear-gradient(180deg,#f8fafc,#eef2ff)}
body[data-theme="light"] .hero{background:#ffffff;box-shadow:0 12px 40px rgba(2,6,23,.08), 0 0 0 1px rgba(99,102,241,.12)}
.hero::after{content:"";position:absolute;inset:-32px;background:radial-gradient(ellipse at 50% -10%, rgba(124,58,237,.32), rgba(124,58,237,0) 60%), radial-gradient(ellipse at 10% 50%, rgba(59,130,246,.18), rgba(59,130,246,0) 50%), radial-gradient(ellipse at 90% 50%, rgba(234,179,8,.18), rgba(234,179,8,0) 50%);filter:blur(26px);z-index:-1;pointer-events:none}
.logo{position:absolute;left:50%;transform:translateX(-50%);top:16px;width:150px;height:150px;background-size:contain;background-repeat:no-repeat;background-position:center}
@media (max-width: 800px){ .logo{width:110px;height:110px;top:8px} .banner{height:240px} }

/* theme toggle button */
.theme-toggle{position:static;display:inline-flex;align-items:center;gap:8px;background:rgba(0,0,0,.12);border:1px solid rgba(255,255,255,.12);color:#fff;padding:6px 10px;border-radius:999px;cursor:pointer; transition:transform .12s ease, box-shadow .16s ease, background .16s ease}
.theme-toggle:hover{ transform: translateY(-1px); box-shadow:0 6px 18px rgba(2,6,23,.25) }
body[data-theme="light"] .theme-toggle{ background:rgba(0,0,0,.04); color:#111827; border-color:rgba(0,0,0,.08) }

/* Tool accent hover */
.tool:hover{background:rgba(124,58,237,.08); border-color: rgba(124,58,237,.25)}
</style>
</head>
<body>
        <div class="banner">
                <div class="hero">
                        <div class="logo" style="background-image:url('https://trojanconstruction.group/storage/subsidiaries/August2022/PG0Hzw1iVnUOQAiyYYuS.png')"></div>
                </div>
        </div>
        <div class="top-tabs">
                <div style="display:flex;align-items:center;gap:8px;padding:8px 6px;">
                        <button id="tabsLeft" aria-label="Scroll tabs left" style="background:transparent;border:0;cursor:pointer">‹</button>
                        <div class="tabs-wrap" style="flex:1;overflow:hidden">
                          <div class="tabs" id="tabsList">
                          {% for t in tables %}
                                <div class="tab {% if t.name==table_name %}active{% endif %}" data-name="{{ t.name|e }}" onclick="location.href='/table/{{ t.name|urlencode }}'">
                                  <div style="display:flex;align-items:center;gap:8px;min-width:0">
                                    <div style="flex:1;min-width:0;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">{{ t.name }}</div>
                                    <div style="background:rgba(0,0,0,.06);padding:4px 8px;border-radius:999px;font-size:12px;margin-left:6px">{{ t.count if t.count is defined else '' }}</div>
                                  </div>
                                </div>
                          {% endfor %}
                          </div>
                        </div>
                        <button id="tabsRight" aria-label="Scroll tabs right" style="background:transparent;border:0;cursor:pointer">›</button>
                </div>
        </div>

        <div class="page">
                <header>
                        <div>
                                <h2>{{ table_name }}</h2>
                                <div class="muted">{{ fields|length }} columns • {{ display_records|length }} records</div>
                        </div>
                        <div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap;justify-content:flex-end">
                                <button id="themeToggle" class="theme-toggle" title="Toggle theme" aria-label="Toggle theme">
                                        <span id="themeIcon" aria-hidden="true"></span>
                                        <span id="themeLabel" style="font-size:12px"></span>
                                </button>
                                <button id="densityToggle" class="theme-toggle" title="Toggle density" aria-label="Toggle density">
                                        <span aria-hidden="true">⇅</span>
                                        <span style="font-size:12px">Density</span>
                                </button>
                                <a href="/">Back</a>
                                <button class="add-btn" id="openAddBtn">+ Add</button>
                        </div>
                </header>

                <div class="toolbar">
                        <div class="tool" id="hideFieldsBtn"><span class="icon" aria-hidden="true"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M12 5C7 5 3.2 8.4 1.5 12c1.7 3.6 5.5 7 10.5 7s8.8-3.4 10.5-7C20.8 8.4 17 5 12 5z" fill="#374151"/><circle cx="12" cy="12" r="3" fill="#fff"/></svg></span> Hide fields</div>
                        <div class="tool" id="filterBtn"><span class="icon" aria-hidden="true"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M3 5h18v2L13 14v5l-2 1v-6L3 7V5z" fill="#374151"/></svg></span> Filter</div>
                        <div class="tool" id="groupBtn"><span class="icon" aria-hidden="true"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><rect x="3" y="5" width="8" height="6" rx="1.2" fill="#374151"/><rect x="13" y="5" width="8" height="6" rx="1.2" fill="#a3a3a3"/><rect x="3" y="13" width="8" height="6" rx="1.2" fill="#a3a3a3"/></svg></span> Group</div>
                        <div class="tool" id="sortBtn"><span class="icon" aria-hidden="true"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M7 10h6v2H7v-2zM7 6h10v2H7V6zM7 14h4v2H7v-2z" fill="#374151"/></svg></span> Sort</div>
                </div>

                                <div class="overlay" id="overlay"></div>

                                <!-- Hide fields modal (persistent) -->
                                <div class="modal" id="fieldModal">
                                        <h3>Hide fields</h3>
                                        <div id="fieldList"></div>
                                        <div style="margin-top:12px"><button id="applyHide" class="tool">Apply</button> <button id="cancelHide" class="tool">Cancel</button></div>
                                </div>

                                                                   <div class="modal" id="filterModal">
                                                                           <h3>Filter</h3>
                                                                           <div style="display:flex;gap:8px;align-items:center;margin-top:8px">
                                                                                   <select id="filterFieldSelect"></select>
                                                                                   <select id="filterOpSelect"><option value="contains">contains</option><option value="equals">equals</option></select>
                                                                                   <input id="filterValueInput" placeholder="value" style="flex:1;padding:6px;border:1px solid #e6e9ef;border-radius:6px">
                                                                           </div>
                                                                           <div style="margin-top:12px"><button id="applyFilterModal" class="tool">Apply</button> <button id="clearFilterModal" class="tool">Clear</button> <button id="cancelFilter" class="tool">Cancel</button></div>
                                                                   </div>

                                <!-- Filter modal (single-condition builder) -->
                                <div class="modal" id="filterModal">
                                        <h3>Filter</h3>
                                        <div style="display:flex;gap:8px;align-items:center">
                                                <select id="filterFieldSelect"></select>
                                                <select id="filterOpSelect"><option value="contains">contains</option><option value="equals">equals</option><option value="starts">starts with</option></select>
                                                <input id="filterInput" placeholder="value">
                                        </div>
                                        <div style="margin-top:12px"><button id="applyFilterBtn" class="tool">Apply</button> <button id="cancelFilterBtn" class="tool">Cancel</button></div>
                                </div>

                                <!-- Add Record modal -->
                                                                                                                                <div class="modal" id="addRecordModal">
                                        <h3>Add record</h3>
                                                                                                                                                                <form id="addRecordForm" class="form-smooth">
                                          <div id="addFormFields" style="display:flex;flex-direction:column;gap:8px;margin-top:8px"></div>
                                          <div style="margin-top:12px;display:flex;gap:8px;justify-content:flex-end">
                                            <button type="button" id="submitAdd" class="tool">Create</button>
                                            <button type="button" id="cancelAdd" class="tool">Cancel</button>
                                          </div>
                                        </form>
                                </div>

                <div class="table-wrap">
                        <table id="gridTable">
                                <thead>
                                        <tr>
                                                <th class="row-select"><input type="checkbox" id="select-all"></th>
                                                <th class="row-index">#</th>
                                                {% for f in fields %}<th data-col-index="{{ loop.index0 }}">{{ f }} <span class="hdr-sort">⇅</span></th>{% endfor %}
                                        </tr>
                                </thead>
                                                <tbody id="gridBody">
                                                        {% if display_records %}
                                                                {% for r in display_records %}
                                                                        <tr data-id="{{ r.id }}">
                                                                                <td class="row-select"><input type="checkbox" class="row-checkbox"></td>
                                                                                <td class="row-index">{{ loop.index }}</td>
                                                                                {% for c in r.cells %}<td data-col-index="{{ loop.index0 }}">{{ c }}</td>{% endfor %}
                                                                        </tr>
                                                                {% endfor %}
                                                        {% else %}
                                                                <tr>
                                                                        <td class="row-select">&nbsp;</td>
                                                                        <td class="row-index">&nbsp;</td>
                                                                        {% for f in fields %}<td data-col-index="{{ loop.index0 }}">&nbsp;</td>{% endfor %}
                                                                </tr>
                                                        {% endif %}

                                                        <!-- inline add-row like Airtable's plus at bottom-left -->
                                                        <tr class="add-row" onclick="location.href='/add_record/{{ table_name|urlencode }}'" style="cursor:pointer">
                                                                <td class="row-select" style="text-align:center;font-size:18px;color:#6b2e8a">＋</td>
                                                                <td class="row-index">&nbsp;</td>
                                                                {% for f in fields %}<td>&nbsp;</td>{% endfor %}
                                                        </tr>
                                                </tbody>
                        </table>
                </div>

        </div>

        <div class="add-bar">
                <button class="add-btn" onclick="location.href='/add_record/{{ table_name|urlencode }}'">+ Add record</button>
                <div class="muted">Selected: <span id="selectedCount">0</span></div>
        </div>
        <div style="padding:10px 18px;text-align:center;color:#6b7280;font-size:12px">&copy; 2025 HSE TROJAN CONSTRUCTION GROUP &nbsp;·&nbsp; Developed by Elius</div>

<script>
        // Theme toggle persistence
        (function(){
                const KEY='theme';
                const saved = localStorage.getItem(KEY) || 'light';
                document.body.dataset.theme = saved;
                const icon = document.getElementById('themeIcon');
                const label = document.getElementById('themeLabel');
                function render(){
                        const t = document.body.dataset.theme;
                        label.textContent = t==='dark'?'Dark':'Light';
                        icon.innerHTML = t==='dark'
                          ? '<svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor" xmlns="http://www.w3.org/2000/svg"><path d="M21 12.79A9 9 0 1111.21 3 7 7 0 0021 12.79z"/></svg>'
                          : '<svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor" xmlns="http://www.w3.org/2000/svg"><path d="M6.76 4.84l-1.8-1.79-1.41 1.41 1.79 1.8 1.42-1.42zM1 13h3v-2H1v2zm10-9h2V1h-2v3zm7.04 2.46l1.79-1.8-1.41-1.41-1.8 1.79 1.42 1.42zM17 13h3v-2h-3v2zm-5 8h2v-3h-2v3zm-7.66-2.34l1.41 1.41 1.8-1.79-1.42-1.42-1.79 1.8zM20 20l1.41 1.41 1.41-1.41-1.41-1.41L20 20zM12 6a6 6 0 100 12A6 6 0 0012 6z"/></svg>';
                }
                function toggleTheme(){
                        const next = document.body.dataset.theme==='dark'?'light':'dark';
                        document.body.classList.add('instant-theme');
                        document.body.dataset.theme = next;
                        try{ localStorage.setItem(KEY,next); }catch(e){}
                        render();
                        setTimeout(()=> document.body.classList.remove('instant-theme'), 120);
                }
                const btn = document.getElementById('themeToggle');
                btn?.addEventListener('pointerdown', (e)=>{ e.preventDefault(); toggleTheme(); });
                btn?.addEventListener('touchstart', (e)=>{ e.preventDefault(); toggleTheme(); }, {passive:false});
                btn?.addEventListener('click', (e)=>{ e.preventDefault(); toggleTheme(); });
                render();
        })();

        // Density toggle persistence (comfortable/compact)
        (function(){
                const KEY='density';
                const saved = localStorage.getItem(KEY) || 'comfortable';
                document.body.dataset.density = saved==='compact'?'compact':'';
                document.getElementById('densityToggle')?.addEventListener('click', ()=>{
                        const curr = document.body.dataset.density==='compact'?'comfortable':'compact';
                        document.body.dataset.density = curr==='compact'?'compact':''; localStorage.setItem(KEY, curr);
                });
        })();

        const TABLE_NAME = {{ table_name|tojson | safe }};
        const FIELDS = {{ fields|tojson | safe }};
        const RECORDS = {{ display_records|tojson | safe }};
        // Field metadata from server (type, choices, required)
        window.FIELDS_META = {{ fields_meta|tojson | safe }};

        // Helper: localStorage keys per table
        const HIDDEN_KEY = 'hidden_cols_' + TABLE_NAME;

        // Apply hidden columns from storage
        function loadHidden(){
                try{ const v = JSON.parse(localStorage.getItem(HIDDEN_KEY)); return Array.isArray(v)?v:[] }catch(e){return []}
        }
        function saveHidden(arr){ localStorage.setItem(HIDDEN_KEY, JSON.stringify(arr)); }
        function applyHidden(){
                const hidden = loadHidden();
                document.querySelectorAll('thead th[data-col-index]').forEach(th=>{ const i = +th.dataset.colIndex; th.style.display = hidden.includes(i) ? 'none' : ''; });
                document.querySelectorAll('tbody td[data-col-index]').forEach(td=>{ const i = +td.dataset.colIndex; td.style.display = hidden.includes(i) ? 'none' : ''; });
        }

        // Select-all behavior + selected count
        // Add sticky header shadow on scroll
        (function(){
                const thead = document.querySelector('#gridTable thead');
                const wrap = document.querySelector('.table-wrap');
                if(!thead || !wrap) return;
                wrap.addEventListener('scroll', ()=>{
                        if(wrap.scrollTop>4) thead.classList.add('stuck'); else thead.classList.remove('stuck');
                });
        })();
        document.getElementById('select-all')?.addEventListener('change', (e)=>{
                const checked = e.target.checked;
                document.querySelectorAll('.row-checkbox').forEach(cb=>cb.checked = checked);
                updateSelectedCount();
        });
        function updateSelectedCount(){ document.getElementById('selectedCount').textContent = document.querySelectorAll('.row-checkbox:checked').length; }
        document.addEventListener('change', (e)=>{ if(e.target && e.target.classList && e.target.classList.contains('row-checkbox')) updateSelectedCount(); });

        // Field modal: persist hidden columns
        const overlayEl = document.getElementById('overlay');
        const fieldModal = document.getElementById('fieldModal');
        const fieldList = document.getElementById('fieldList');
        document.getElementById('hideFieldsBtn')?.addEventListener('click', ()=>{
                fieldList.innerHTML = '';
                const hidden = loadHidden();
                FIELDS.forEach((f,i)=>{
                        const id = 'chk_'+i;
                        const div = document.createElement('div');
                        div.innerHTML = `<label style="font-size:14px"><input type="checkbox" id="${id}" data-idx="${i}" ${hidden.includes(i)?'':''}> ${f}</label>`;
                        fieldList.appendChild(div);
                });
                overlayEl.classList.add('show'); fieldModal.classList.add('show');
        });
        document.getElementById('cancelHide')?.addEventListener('click', ()=>{ overlayEl.classList.remove('show'); fieldModal.classList.remove('show'); });
        document.getElementById('applyHide')?.addEventListener('click', ()=>{
                const checks = Array.from(fieldList.querySelectorAll('input[type=checkbox]'));
                const hidden = [];
                checks.forEach(ch=>{ const idx = +ch.dataset.idx; if(!ch.checked) hidden.push(idx); });
                saveHidden(hidden);
                applyHidden();
                overlayEl.classList.remove('show'); fieldModal.classList.remove('show');
        });

        // Filter modal
        const filterModal = document.getElementById('filterModal');
        const filterFieldSelect = document.getElementById('filterFieldSelect');
        const filterOpSelect = document.getElementById('filterOpSelect') || document.getElementById('filterOpSelect');
        const filterValueInput = document.getElementById('filterValueInput') || document.getElementById('filterInput');
        document.getElementById('filterBtn')?.addEventListener('click', ()=>{
                filterFieldSelect.innerHTML = '';
                FIELDS.forEach((f,i)=>{ const opt = document.createElement('option'); opt.value = i; opt.textContent = f; filterFieldSelect.appendChild(opt); });
                overlayEl.classList.add('show'); filterModal.classList.add('show');
        });
        document.getElementById('cancelFilter')?.addEventListener('click', ()=>{ overlayEl.classList.remove('show'); filterModal.classList.remove('show'); });
        document.getElementById('applyFilterModal')?.addEventListener('click', ()=>{
                const idx = +filterFieldSelect.value; const op = filterOpSelect.value; const val = (filterValueInput.value||'').toLowerCase();
                if(val===''){ alert('Enter a value'); return; }
                document.querySelectorAll('#gridBody tr').forEach(tr=>{
                        if(tr.classList.contains('add-row')) return; // keep add row
                        const cell = tr.querySelector('[data-col-index="'+idx+'"]'); const txt = (cell?.textContent||'').toLowerCase();
                        let ok = false;
                        if(op==='contains') ok = txt.indexOf(val)!==-1;
                        else if(op==='equals') ok = txt === val;
                        else if(op==='starts') ok = txt.startsWith(val);
                        tr.style.display = ok ? '' : 'none';
                });
                overlayEl.classList.remove('show'); filterModal.classList.remove('show');
        });
        document.getElementById('clearFilterModal')?.addEventListener('click', ()=>{ document.querySelectorAll('#gridBody tr').forEach(tr=>tr.style.display=''); overlayEl.classList.remove('show'); filterModal.classList.remove('show'); });

        // Sortable headers (click header to toggle asc/desc)
        let sortState = {idx:null, dir:1};
        function clearSortIndicators(){ document.querySelectorAll('.hdr-sort').forEach(s=>s.textContent='⇅'); document.querySelectorAll('thead th').forEach(th=>th.classList.remove('sort-asc','sort-desc')); }
        document.querySelectorAll('thead th[data-col-index]').forEach(th=>{
                th.style.cursor = 'pointer';
                th.addEventListener('click', ()=>{
                        const idx = +th.dataset.colIndex;
                        if(sortState.idx===idx) sortState.dir = -sortState.dir; else { sortState.idx=idx; sortState.dir=1; }
                        const tbody = document.getElementById('gridBody');
                        const rows = Array.from(tbody.querySelectorAll('tr')).filter(r=>r.style.display!=='none' && !r.classList.contains('add-row'));
                        rows.sort((a,b)=>{
                                const av = (a.querySelector('[data-col-index="'+idx+'"]')?.textContent||'').toLowerCase();
                                const bv = (b.querySelector('[data-col-index="'+idx+'"]')?.textContent||'').toLowerCase();
                                if(av<bv) return -1*sortState.dir; if(av>bv) return 1*sortState.dir; return 0;
                        });
                        rows.forEach(r=>tbody.appendChild(r));
                        // renumber
                        document.querySelectorAll('.row-index').forEach((td,i)=>td.textContent = i+1);
                        clearSortIndicators();
                        const s = th.querySelector('.hdr-sort'); if(s) s.textContent = sortState.dir===1 ? '↑' : '↓';
                        th.classList.add(sortState.dir===1 ? 'sort-asc' : 'sort-desc');
                });
        });

        // tooltips + truncation
        document.querySelectorAll('tbody td').forEach(td=>{
                if(td.classList.contains('row-select') || td.classList.contains('row-index')) return;
                const txt = (td.textContent||'').trim(); td.title = txt;
                td.classList.add('cell-trunc');
        });

        // Inline editing: click a cell to edit
        (function(){
                const meta = window.FIELDS_META || [];
                function fieldMetaByIndex(i){ return meta[i] || {name: window.FIELDS[i]||('', type:'text')}; }
                document.querySelectorAll('#gridBody tr').forEach(tr=>{
                        const rid = tr.dataset.id;
                        if(!rid) return;
                        Array.from(tr.querySelectorAll('td[data-col-index]')).forEach(td=>{
                                td.addEventListener('click', (e)=>{
                                        // avoid editing if click on a checkbox or selection
                                        if(e.target && (e.target.tagName==='INPUT' || e.target.tagName==='BUTTON' || e.target.tagName==='A')) return;
                                        const idx = +td.dataset.colIndex;
                                        const fm = meta[idx] || {name: window.FIELDS[idx], type:'text'};
                                        // create editor
                                        let editor;
                                        const cur = td.textContent.trim();
                                        if(fm.type && fm.type.indexOf('date')!==-1){
                                                editor = document.createElement('input'); editor.type='date'; editor.value = cur;
                                        }else if(fm.type && (fm.type.indexOf('number')!==-1 || fm.type==='integer' || fm.type==='decimal')){
                                                editor = document.createElement('input'); editor.type='number'; editor.value = cur;
                                        }else if(fm.choices && fm.choices.length){
                                                editor = document.createElement('select'); const empty = document.createElement('option'); empty.value=''; empty.textContent='--'; editor.appendChild(empty); fm.choices.forEach(c=>{ const o=document.createElement('option'); o.value=c; o.textContent=c; if(c===cur) o.selected=true; editor.appendChild(o); });
                                        }else if(fm.type && (fm.type.toLowerCase().indexOf('multiline')!==-1 || fm.type.toLowerCase().indexOf('long')!==-1 || fm.type.toLowerCase().indexOf('rich')!==-1)){
                                                // prefer textarea for long/multiline fields
                                                editor = document.createElement('textarea'); editor.rows = 3; editor.value = cur; editor.style.resize='vertical';
                                        }else{
                                                editor = document.createElement('input'); editor.type='text'; editor.value = cur;
                                        }
                                        editor.style.width='100%'; editor.style.boxSizing='border-box';
                                        td.innerHTML=''; td.appendChild(editor); editor.focus();
                                        function finish(save){
                                                const newVal = editor.value;
                                                if(!save){ td.textContent = cur; return; }
                                                const payload = {fields: {}}; payload.fields[fm.name] = newVal;
                                                fetch(`/update_record_ajax/${encodeURIComponent(TABLE_NAME)}/${encodeURIComponent(rid)}`, {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(payload)})
                                                .then(r=>r.json()).then(data=>{
                                                        if(data.ok){ td.textContent = newVal; showToast('Saved', 'success'); }
                                                        else{ td.textContent = cur; showToast('Save failed', 'error'); }
                                                }).catch(err=>{ console.error(err); td.textContent = cur; showToast('Save failed', 'error'); });
                                        }
                                        editor.addEventListener('blur', ()=> finish(true));
                                        editor.addEventListener('keydown', (ev)=>{ if(ev.key==='Enter'){ ev.preventDefault(); editor.blur(); } else if(ev.key==='Escape'){ ev.preventDefault(); td.textContent = cur; } });
                                });
                        });
                });
        })();

        // apply persisted hidden columns on load
        applyHidden();
        updateSelectedCount();

        // Tabs scroll controls
        (function(){
                const tabsList = document.getElementById('tabsList');
                const left = document.getElementById('tabsLeft');
                const right = document.getElementById('tabsRight');
                left?.addEventListener('click', ()=>{ tabsList.scrollBy({left:-220, behavior:'smooth'}); });
                right?.addEventListener('click', ()=>{ tabsList.scrollBy({left:220, behavior:'smooth'}); });
        })();

        // Add-record modal wiring
        (function(){
                const openBtn = document.getElementById('openAddBtn');
                const addModal = document.getElementById('addRecordModal');
                const overlay = document.getElementById('overlay');
                const addForm = document.getElementById('addRecordForm');
                const fieldsContainer = document.getElementById('addFormFields');
                const submitBtn = document.getElementById('submitAdd');
                const cancelBtn = document.getElementById('cancelAdd');

                function buildForm(){
                        fieldsContainer.innerHTML = '';
                        // fields_meta provided by server for type mapping
                        const meta = window.FIELDS_META || [];
                        FIELDS.forEach((f,i)=>{
                                const m = meta.find(x=>x.name===f) || {name:f,type:'text',choices:null,required:false};
                                const wrapper = document.createElement('div');
                                wrapper.style.display = 'flex'; wrapper.style.flexDirection='column'; wrapper.style.gap='6px'; wrapper.dataset.field = f;
                                const label = document.createElement('label'); label.textContent = f + (m.required ? ' *' : ''); label.style.fontSize='13px';
                                let input;
                                if(m.type && (m.type.indexOf('date')!==-1)){
                                        input = document.createElement('input'); input.type='date';
                                }else if(m.type && (m.type.indexOf('time')!==-1)){
                                        input = document.createElement('input'); input.type='time';
                                }else if(m.type && (m.type.indexOf('number')!==-1 || m.type==='integer' || m.type==='decimal')){
                                        input = document.createElement('input'); input.type='number';
                                }else if(m.choices && m.choices.length && (m.type && (m.type.indexOf('multi')!==-1 || m.type==='multiSelect'))){
                                        // multi-select -> allow multiple checkboxes
                                        input = document.createElement('div'); input.className='multi-select';
                                        m.choices.forEach(ch=>{ const cb = document.createElement('label'); cb.style.display='inline-flex'; cb.style.alignItems='center'; cb.style.gap='6px'; cb.innerHTML = `<input type="checkbox" name="${f}" value="${ch}"> ${ch}`; input.appendChild(cb); });
                                }else if(m.choices && m.choices.length){
                                        input = document.createElement('select'); const emptyOpt = document.createElement('option'); emptyOpt.value=''; emptyOpt.textContent='-- choose --'; input.appendChild(emptyOpt); m.choices.forEach(ch=>{ const o = document.createElement('option'); o.value = ch; o.textContent = ch; input.appendChild(o); });
                                }else if(m.type && (m.type.indexOf('attach')!==-1 || m.type.indexOf('file')!==-1)){
                                        input = document.createElement('input'); input.type='file'; input.multiple = false;
                                }else if(m.type && (m.type==='checkbox' || m.type==='boolean')){
                                        input = document.createElement('input'); input.type='checkbox';
                                }else if(m.type && (m.type.toLowerCase().indexOf('multiline')!==-1 || m.type.toLowerCase().indexOf('long')!==-1 || m.type.toLowerCase().indexOf('rich')!==-1)){
                                        input = document.createElement('textarea'); input.rows = 4; input.style.resize='vertical';
                                }else{
                                        input = document.createElement('input'); input.type='text';
                                }
                                input.name = f;
                                input.style.padding='8px'; input.style.border='1px solid #e6e9ef'; input.style.borderRadius='6px';
                                const err = document.createElement('div'); err.className='field-error'; err.style.color='crimson'; err.style.fontSize='12px'; err.style.minHeight='16px'; err.style.marginTop='4px';
                                wrapper.appendChild(label); wrapper.appendChild(input); wrapper.appendChild(err);
                                fieldsContainer.appendChild(wrapper);
                        });
                        // small helper to trap focus inside modal
                        trapFocus(addModal);
                }

                openBtn?.addEventListener('click', ()=>{
                        // expose fields_meta to client JS
                        window.FIELDS_META = {{ fields_meta|tojson | safe }};
                        buildForm(); overlay.classList.add('show'); addModal.classList.add('show');
                        // focus first input
                        setTimeout(()=>{ const first = addModal.querySelector('input,select,textarea'); if(first) first.focus(); }, 60);
                });
                cancelBtn?.addEventListener('click', ()=>{ overlay.classList.remove('show'); addModal.classList.remove('show'); });

                // Escape closes modal and returns focus
                document.addEventListener('keydown', (e)=>{
                        if(e.key==='Escape'){
                                if(addModal.classList.contains('show')){ overlay.classList.remove('show'); addModal.classList.remove('show'); openBtn?.focus(); }
                        }
                });

                submitBtn?.addEventListener('click', async ()=>{
                        const formData = {};
                        Array.from(addForm.elements).forEach(el=>{ if(el.name) formData[el.name]=el.value; });
                        submitBtn.disabled = true; submitBtn.textContent = 'Creating...';
                        try{
                                // clear previous field errors
                                Array.from(addForm.querySelectorAll('.field-error')).forEach(d=>d.textContent='');
                                const res = await fetch(`/add_record_ajax/${encodeURIComponent(TABLE_NAME)}`, {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(formData)});
                                const data = await res.json();
                                if(data.ok){
                                        // optimistic insert row at top
                                        const tbody = document.getElementById('gridBody');
                                        const tr = document.createElement('tr'); tr.dataset.id = data.id;
                                        tr.innerHTML = `<td class="row-select"><input type="checkbox" class="row-checkbox"></td><td class="row-index">1</td>` + FIELDS.map((f,i)=>`<td data-col-index="${i}">${(formData[f]||'')}</td>`).join('');
                                        const first = tbody.querySelector('tr'); tbody.insertBefore(tr, first);
                                        document.querySelectorAll('.row-index').forEach((td,i)=>td.textContent = i+1);
                                        overlay.classList.remove('show'); addModal.classList.remove('show');
                                        openBtn?.focus();
                                        showToast('Record created', 'success');
                                }else if(data.errors){
                                        // show field-level errors
                                        Object.entries(data.errors).forEach(([k,msg])=>{
                                                const wrapper = fieldsContainer.querySelector(`div[data-field] [name='${CSS.escape(k)}']`)?.parentElement || fieldsContainer.querySelector(`div[data-field='${k}'] .field-error`);
                                                if(wrapper){
                                                        const errEl = wrapper.querySelector ? wrapper.querySelector('.field-error') : null;
                                                        if(errEl) errEl.textContent = msg;
                                                }
                                        });
                                        showToast('Validation failed', 'error');
                                }else{
                                        showToast('Error creating record', 'error');
                                }
                        }catch(err){ console.error(err); showToast('Request failed', 'error'); }
                        submitBtn.disabled=false; submitBtn.textContent='Create';
                });
        })();

        // Simple toast helper
        function showToast(msg, level){
                let t = document.getElementById('__toast');
                if(!t){ t = document.createElement('div'); t.id='__toast'; t.style.position='fixed'; t.style.right='18px'; t.style.bottom='18px'; t.style.padding='12px 16px'; t.style.borderRadius='8px'; t.style.boxShadow='0 6px 18px rgba(0,0,0,.18)'; t.style.color='#fff'; t.style.zIndex=9999; document.body.appendChild(t); }
                t.style.background = level==='success' ? '#16a34a' : '#dc2626'; t.textContent = msg; t.style.opacity=0; t.style.transform='translateY(8px)';
                requestAnimationFrame(()=>{ t.style.transition='transform .28s ease, opacity .28s ease'; t.style.opacity=1; t.style.transform='translateY(0)'; });
                setTimeout(()=>{ t.style.opacity=0; t.style.transform='translateY(8px)'; }, 2400);
        }

        // Focus trap helper (simple)
        function trapFocus(modal){
                if(!modal) return;
                const focusable = 'a[href], area[href], input:not([disabled]), select:not([disabled]), textarea:not([disabled]), button:not([disabled]), [tabindex]';
                const nodes = Array.from(modal.querySelectorAll(focusable));
                if(!nodes.length) return;
                const first = nodes[0], last = nodes[nodes.length-1];
                modal.addEventListener('keydown', (e)=>{
                        if(e.key !== 'Tab') return;
                        if(e.shiftKey){ if(document.activeElement === first){ e.preventDefault(); last.focus(); } }
                        else { if(document.activeElement === last){ e.preventDefault(); first.focus(); } }
                });
        }
</script>
</body>
</html>
"""


@app.route('/')
def dashboard():
        if api is None:
                return 'Airtable API not initialized', 500
        try:
                meta = api.base(AIRTABLE_BASE_ID).schema()
                tables = []
                total_records = 0
                for t in meta.tables:
                        name = t.name
                        try:
                                count = len(base.table(name).all())
                        except Exception:
                                count = 0
                        tables.append({'name': name, 'id': t.id, 'count': count})
                        total_records += count
                last_updated = datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')
                return render_template_string(_DASH, tables=tables, total_records=total_records, last_updated=last_updated)
        except Exception as e:
                return f'Error enumerating tables: {e}', 500


@app.route('/table/<path:table_name>')
def view_table(table_name):
        if api is None:
                return 'Airtable API not initialized', 500
        try:
                table = base.table(table_name)
                records = table.all()
        except Exception as e:
                return f'Error fetching records for {table_name}: {e}', 500

        # Determine ordered fields from schema and build metadata per field
        fields = []
        fields_meta = []
        try:
                meta = api.base(AIRTABLE_BASE_ID).schema()
                t = next((x for x in meta.tables if x.name == table_name), None)
                if t and hasattr(t, 'fields'):
                        for f in t.fields:
                                # field object may contain name, type, required, options/choices
                                fname = getattr(f, 'name', None) or getattr(f, 'id', '')
                                ftype = getattr(f, 'type', None) or getattr(f, 'typeName', None) or 'text'
                                # choices / options
                                choices = None
                                if hasattr(f, 'options') and f.options:
                                        # options may have choices or choices list
                                        choices = []
                                        opts = getattr(f, 'options')
                                        for c in getattr(opts, 'choices', []) or []:
                                                # each c may have name
                                                choices.append(getattr(c, 'name', c if isinstance(c, str) else ''))
                                # required flag
                                required = bool(getattr(f, 'required', False) or getattr(f, 'isRequired', False))
                                fields.append(fname)
                                fields_meta.append({'name': fname, 'type': ftype, 'choices': choices, 'required': required})
        except Exception:
                pass

        if not fields:
                seen = []
                for r in records:
                        for k in r.get('fields', {}).keys():
                                if k not in seen:
                                        seen.append(k)
                fields = seen
                # fallback metadata: text inputs
                fields_meta = [{'name': n, 'type': 'text', 'choices': None, 'required': False} for n in fields]

        display_records = []
        for r in records:
                cells = []
                for f in fields:
                        v = r.get('fields', {}).get(f, '')
                        if isinstance(v, list):
                                cells.append(', '.join(str(x) for x in v))
                        elif isinstance(v, dict):
                                cells.append(json.dumps(v))
                        else:
                                cells.append(str(v))
                display_records.append({'id': r.get('id'), 'cells': cells})

        # build lightweight table list for the top tab strip (names + ids)
        tables = []
        try:
                meta = api.base(AIRTABLE_BASE_ID).schema()
                for t in meta.tables:
                        tables.append({'name': t.name, 'id': t.id})
        except Exception:
                pass

        return render_template_string(_TABLE, table_name=table_name, fields=fields, fields_meta=fields_meta, display_records=display_records, tables=tables)


@app.route('/add_record/<path:table_name>', methods=['GET', 'POST'])
def add_record(table_name):
        if api is None:
                return 'Airtable API not initialized', 500
        table = base.table(table_name)

        if request.method == 'POST':
                payload = {}
                for k, v in request.form.items():
                        if not v:
                                continue
                        payload[k] = v
                try:
                        new = table.create(payload)
                        return f'Record created: {new.get("id")} - <a href="/table/{table_name}">Back</a>'
                except Exception as e:
                        return f'Error creating record: {e}', 500

        # Build best-effort form fields
        form_fields = []
        try:
                meta = api.base(AIRTABLE_BASE_ID).schema()
                t = next((x for x in meta.tables if x.name == table_name), None)
                if t and hasattr(t, 'fields'):
                        for f in t.fields:
                                form_fields.append({'name': f.name, 'type': 'text'})
        except Exception:
                try:
                        sample = table.all(max_records=10)
                        names = set()
                        for r in sample:
                                names.update(r.get('fields', {}).keys())
                        form_fields = [{'name': n, 'type': 'text'} for n in sorted(names)]
                except Exception:
                        form_fields = [{'name': 'Name', 'type': 'text'}, {'name': 'Description', 'type': 'text'}]

        form_html = ['<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Add Record</title>\n<style>\n:root{--bg:#0f1724;--fg:#e6eef8;--card:#0b1220;--muted:#9aa3b2;--border:rgba(255,255,255,.14)}\nbody[data-theme="light"]{--bg:#f8fafc;--fg:#111827;--card:#ffffff;--muted:#6b7280;--border:#e5e7eb}\nbody{font-family:Inter,Segoe UI,Arial,Helvetica,sans-serif;margin:0;background:var(--bg);color:var(--fg);padding:18px}\n.container{max-width:800px;margin:0 auto}\n.h1{font-size:22px;margin-bottom:12px}\n.form-smooth .form-row{display:flex;flex-direction:column;gap:6px;margin-bottom:10px}\n.form-smooth label{font-size:13px;color:var(--muted)}\n.form-smooth input,.form-smooth select,.form-smooth textarea{padding:10px 12px;border:1px solid var(--border);border-radius:8px;background:var(--card);color:var(--fg);transition:box-shadow .18s ease, border-color .14s ease, transform .08s ease}\n.form-smooth input:focus,.form-smooth select:focus,.form-smooth textarea:focus{outline:0;border-color:#7c3aed;box-shadow:0 8px 30px rgba(124,58,237,.18)}\n.btn{background:#7c3aed;color:#fff;padding:8px 12px;border-radius:8px;border:0;cursor:pointer;transition:transform .1s ease, box-shadow .16s ease}\n.btn:hover{transform:translateY(-1px);box-shadow:0 8px 20px rgba(124,58,237,.22)}\n.btn:disabled{opacity:.6;cursor:not-allowed}\n.link{color:#7c3aed}\n</style>\n</head><body><div class="container">']
        form_html.append(f'<h1 class="h1">Add Record to {table_name}</h1>')
        form_html.append('<form method="post" class="form-smooth">')
        for f in form_fields:
                form_html.append(f'<div class="form-row"><label>{f["name"]}</label><input name="{f["name"]}" /></div>')
        form_html.append(f'<p><button type="submit" class="btn">Create</button> <a class="link" href="/table/{table_name}">Cancel</a></p>')
        form_html.append('</form></div><script>try{var t=localStorage.getItem("theme")||"dark";document.body.dataset.theme=t;}catch(e){}</script></body></html>')

        return '\n'.join(form_html)


@app.route('/add_record_ajax/<path:table_name>', methods=['POST'])
def add_record_ajax(table_name):
        if api is None:
                return jsonify({'ok': False, 'error': 'Airtable API not initialized'}), 500
        payload = request.get_json(force=True) or {}
        # Load schema metadata for this table to validate; best-effort
        try:
                meta = api.base(AIRTABLE_BASE_ID).schema()
                tmeta = next((x for x in meta.tables if x.name == table_name), None)
                meta_fields = []
                if tmeta and hasattr(tmeta, 'fields'):
                        for f in tmeta.fields:
                                fname = getattr(f, 'name', None) or getattr(f, 'id', '')
                                ftype = getattr(f, 'type', None) or getattr(f, 'typeName', None) or 'text'
                                required = bool(getattr(f, 'required', False) or getattr(f, 'isRequired', False))
                                choices = None
                                if hasattr(f, 'options') and f.options:
                                        choices = [getattr(c, 'name', c if isinstance(c, str) else '') for c in getattr(f.options, 'choices', []) or []]
                                meta_fields.append({'name': fname, 'type': ftype, 'required': required, 'choices': choices})
                else:
                        meta_fields = []
        except Exception:
                meta_fields = []

        errors = {}
        body = {}
        # Validate and coerce
        for mf in meta_fields:
                key = mf['name']
                val = payload.get(key)
                if mf.get('required') and (val is None or (isinstance(val, str) and val.strip()=='')):
                        errors[key] = 'This field is required'
                        continue
                ftype = mf.get('type','text')
                if val is None or val == '':
                        continue
                try:
                        if ftype in ('number','integer','decimal'):
                                # coerce numeric
                                body[key] = float(val)
                        elif ftype in ('date','datetime'):
                                # keep as ISO-like string, server trusts format client sends
                                body[key] = val
                        elif ftype in ('singleSelect','select'):
                                # expect single string matching a choice
                                if mf.get('choices') and val not in mf['choices']:
                                        errors[key] = 'Invalid choice'
                                else:
                                        body[key] = val
                        elif ftype in ('multiSelect','multiple'):
                                # accept comma-separated values or array
                                if isinstance(val, list):
                                        body[key] = val
                                else:
                                        body[key] = [s.strip() for s in val.split(',') if s.strip()]
                        elif ftype in ('checkbox','boolean'):
                                body[key] = bool(val in (True,'true','1','on','yes'))
                        else:
                                # default to string
                                body[key] = str(val)
                except Exception as e:
                        errors[key] = 'Invalid value'

        # For any payload fields not in meta, include them as strings (best-effort)
        for k,v in payload.items():
                if k not in body and k not in errors:
                        body[k] = v

        if errors:
                return jsonify({'ok': False, 'errors': errors}), 400

        try:
                new = base.table(table_name).create(body)
                return jsonify({'ok': True, 'id': new.get('id')})
        except Exception as e:
                return jsonify({'ok': False, 'error': str(e)}), 500


@app.route('/update_record_ajax/<path:table_name>/<record_id>', methods=['POST'])
def update_record_ajax(table_name, record_id):
        if api is None:
                return jsonify({'ok': False, 'error': 'Airtable API not initialized'}), 500
        payload = request.get_json(force=True) or {}
        fields = payload.get('fields') if isinstance(payload, dict) else None
        if not fields or not isinstance(fields, dict):
                return jsonify({'ok': False, 'error': 'Invalid payload, missing fields'}), 400
        try:
                updated = base.table(table_name).update(record_id, {'fields': fields})
                return jsonify({'ok': True, 'record': updated})
        except Exception as e:
                return jsonify({'ok': False, 'error': str(e)}), 500


@app.route('/favicon.ico')
def favicon():
        return '', 204


if __name__ == '__main__':
        # Local development
        port = int(os.environ.get('PORT', 8080))
        print(f'[*] Starting Enhanced Airtable Dashboard on http://localhost:{port}')
        app.run(debug=True, host='0.0.0.0', port=port)