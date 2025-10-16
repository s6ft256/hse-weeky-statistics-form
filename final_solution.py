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
import re
import unicodedata
import re
from airtable_helpers import normalize_field_name, coerce_payload_to_body

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

# Use shared helpers from airtable_helpers.py (imported above)

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
<title>hse_statistics_report</title>
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
: 
<script>
        (function(){
                try{
                        const t = localStorage.getItem('theme') || 'light';
                        // set on documentElement and body (if available) so CSS selectors for body[data-theme] apply early
                        document.documentElement.dataset.theme = t;
                        if(document.body) document.body.dataset.theme = t; else document.addEventListener('DOMContentLoaded', ()=> document.body.dataset.theme = t);
                }catch(e){}
        })();
: </script>
<script>try{document.title = 'hse_statistics_report'}catch(e){}</script>
<style>
:root{--bg:#f8fafc;--card:#ffffff;--muted:#6b7280;--accent:#7c3aed;--fg:#111827;--ease: cubic-bezier(.22,.61,.36,1); --dur: 220ms}
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
/* Dark theme variables */
html[data-theme="dark"], body[data-theme="dark"]{--bg:#0b1028;--card:#0f1724;--muted:#94a3b8;--accent:#7c3aed;--fg:#e6eef8}

/* Smooth theme transitions */
body{transition: background-color .28s var(--ease), color .28s var(--ease)}
/* helper class for a fuller transition effect */
.theme-transition *{transition: background-color .35s var(--ease), color .35s var(--ease), border-color .28s var(--ease), box-shadow .28s var(--ease) !important}
/* Theme toggle button */
.theme-toggle{display:inline-flex;align-items:center;gap:8px;padding:10px 12px;border-radius:999px;border:0;background:var(--card);color:var(--fg);cursor:pointer;box-shadow:0 8px 26px rgba(2,6,23,.12);position:fixed;right:18px;bottom:18px;z-index:999;transition:transform .18s ease, box-shadow .18s ease}
.theme-toggle:hover{transform:translateY(-4px);box-shadow:0 18px 40px rgba(2,6,23,.18)}
.theme-toggle .theme-icon{display:inline-flex;width:18px;height:18px}
.theme-toggle .theme-label{font-size:13px}
/* About floating button */
.about-btn{display:inline-flex;align-items:center;gap:8px;padding:10px 12px;border-radius:999px;border:0;background:var(--card);color:var(--fg);cursor:pointer;box-shadow:0 8px 26px rgba(2,6,23,.08);position:fixed;right:120px;bottom:18px;z-index:999;transition:transform .18s ease, box-shadow .18s ease}
.about-btn:hover{transform:translateY(-4px);box-shadow:0 18px 40px rgba(2,6,23,.12)}
.banner{height:460px;background:linear-gradient(180deg,rgba(11,20,40,.95),rgba(16,24,37,.98));display:flex;align-items:center;justify-content:center;padding:32px 18px;border-bottom:1px solid rgba(255,255,255,.03);position:relative;box-sizing:border-box}
.hero{max-width:1100px;width:100%;background:linear-gradient(180deg,var(--card),rgba(0,0,0,.04));padding:22px;border-radius:14px;box-shadow:0 20px 60px rgba(0,0,0,.12), 0 0 0 1px var(--border);text-align:center;position:relative;min-height:300px;z-index:1;display:flex;flex-direction:column;align-items:center;justify-content:center;margin:0 auto}
.hero::after{content:"";position:absolute;inset:-44px;background:radial-gradient(ellipse at 50% -10%, rgba(124,58,237,.4), rgba(124,58,237,0) 60%), radial-gradient(ellipse at 10% 50%, rgba(59,130,246,.22), rgba(59,130,246,0) 50%), radial-gradient(ellipse at 90% 50%, rgba(234,179,8,.22), rgba(234,179,8,0) 50%);filter:blur(34px);z-index:-1;pointer-events:none}
.logo{width:260px;height:260px;background-size:contain;background-repeat:no-repeat;background-position:center;margin:0 auto 12px;flex:0 0 auto}
.report-title{margin-top:36px;text-align:center}
.report-title h1{font-size:48px;margin:0;color:var(--fg);letter-spacing:1px;font-weight:700}
.report-title .subtitle{color:var(--muted);margin-top:10px}
/* light theme: ensure strong contrast for title area */
body[data-theme="light"] .report-title h1{color:var(--fg) !important}
body[data-theme="light"] .report-title .subtitle{color:var(--muted) !important}
/* light theme banner/hero becomes brighter */
body[data-theme="light"] .banner{background:linear-gradient(180deg,var(--bg),var(--card))}
body[data-theme="light"] .hero{background:linear-gradient(180deg,#ffffff,#ffffff);box-shadow:0 12px 40px rgba(2,6,23,.08), 0 0 0 1px rgba(99,102,241,.15)}
body[data-theme="light"] .hero::after{background:radial-gradient(ellipse at 50% -10%, rgba(124,58,237,.16), rgba(124,58,237,0) 60%), radial-gradient(ellipse at 10% 50%, rgba(59,130,246,.12), rgba(59,130,246,0) 50%), radial-gradient(ellipse at 90% 50%, rgba(234,179,8,.12), rgba(234,179,8,0) 50%)}

/* responsive title and entrance animation */
@keyframes fadeScaleIn { from { opacity: 0; transform: translateY(8px) scale(.98); } to { opacity:1; transform: translateY(0) scale(1);} }
.report-title h1{animation: fadeScaleIn 420ms ease both}
@media (max-width: 800px){ .report-title h1{font-size:28px} .logo{width:160px;height:160px} .banner{height:260px} }

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
.search input{width:100%;padding:14px;border-radius:10px;border:1px solid rgba(0,0,0,.06);background:var(--card);color:var(--fg);transition:box-shadow .18s ease, transform .12s ease, border-color .12s ease}
.search input:focus{outline:0;box-shadow:0 8px 30px rgba(124,58,237,.12);transform:translateY(-1px);border-color:rgba(124,58,237,.6)}
html[data-theme="light"] body .search input{background:var(--card);color:var(--fg);border:1px solid var(--border)}
html[data-theme="light"], body[data-theme="light"] .card{color:#111827}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:18px;margin-top:18px}
.card{background:var(--card);padding:22px;border-radius:12px;min-height:140px;border:1px solid rgba(255,255,255,.03);box-shadow:0 6px 20px rgba(2,6,23,.6);color:var(--fg)}
.card h3{margin:0 0 10px 0;font-size:20px;font-weight:600}
.card .meta{color:var(--muted);font-size:13px;margin-top:8px}
.card .active{float:right;color:var(--accent);font-weight:600}
.footer-note{color:var(--muted);font-size:13px;margin-top:14px}
a.card{text-decoration:none}
/* hide decorative svg icons inside card/tool areas for a cleaner toolbar look */
.card .card-icon svg, .toolbar .card-icon svg{display:none}
@media(max-width:800px){.stats{flex-direction:column}}
/* subtle hover lift and smooth appearance */
.card{transition:transform var(--dur) var(--ease),opacity var(--dur) var(--ease);will-change:transform,opacity}
.card:hover{transform:translateY(-6px)}
.card[style*="opacity: 0"]{opacity:0}
.card{opacity:1}
/* small copyright/footer */
.site-footer{color:var(--muted);font-size:12px;margin-top:12px;text-align:center;font-weight:700}
/* About modal and overlay */
.overlay{position:fixed;inset:0;background:rgba(2,6,23,.48);backdrop-filter:blur(2px);display:none;opacity:0;transition:opacity .18s linear;z-index:998}
.overlay.show{display:block;opacity:1}
.modal{position:fixed;left:50%;top:50%;transform:translate(-50%,-50%) scale(.98);background:var(--card);color:var(--fg);padding:18px;border-radius:12px;box-shadow:0 20px 60px rgba(2,6,23,.4);max-width:720px;width:calc(100% - 48px);z-index:999;opacity:0;transition:opacity .18s var(--ease),transform .18s var(--ease)}
.modal.show{opacity:1;transform:translate(-50%,-50%) scale(1)}
.modal h3{margin:0 0 8px 0;font-size:18px}
.modal a{color:var(--accent);font-weight:600}
</style>
</head>
<body>
                        <div class="banner">
                                <div class="hero">
                                        <div class="logo" style="background-image:url('https://trojanconstruction.group/storage/subsidiaries/August2022/PG0Hzw1iVnUOQAiyYYuS.png')"></div>
                                        <!-- title moved below the banner -->
                                </div>
                        </div>

                                <div class="container">
                                        <div style="display:flex;justify-content:flex-end;margin-top:8px">
                                                <button class="about-btn" aria-label="About">About</button>
                                                <button class="theme-toggle" aria-label="Toggle theme"><span id="themeIcon" class="theme-icon"></span><span id="themeLabel" class="theme-label"></span></button>
                                        </div>
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
                                      <svg width="36" height="36" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><rect x="3" y="4" width="18" height="6" rx="1.5" fill="var(--accent)"/><rect x="3" y="14" width="8" height="6" rx="1.5" fill="var(--accent2)"/><rect x="14" y="14" width="7" height="6" rx="1.5" fill="var(--accent3)"/></svg>
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
                                                                                const saved = localStorage.getItem(KEY) || 'light';
                                                                                document.body.dataset.theme = saved;
                                                                                const toggles = Array.from(document.querySelectorAll('.theme-toggle'));
                                                                                function iconSvg(t){
                                                                                    return t==='dark'
                                                                                      ? '<svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor" xmlns="http://www.w3.org/2000/svg"><path d="M21 12.79A9 9 0 1111.21 3 7 7 0 0021 12.79z"/></svg>'
                                                                                      : '<svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor" xmlns="http://www.w3.org/2000/svg"><path d="M6.76 4.84l-1.8-1.79-1.41 1.41 1.79 1.8 1.42-1.42zM1 13h3v-2H1v2zm10-9h2V1h-2v3zm7.04 2.46l1.79-1.8-1.41-1.41-1.8 1.79 1.42 1.42zM17 13h3v-2h-3v2zm-5 8h2v-3h-2v3zm-7.66-2.34l1.41 1.41 1.8-1.79-1.42-1.42-1.79 1.8zM20 20l1.41 1.41 1.41-1.41-1.41-1.41L20 20zM12 6a6 6 0 100 12A6 6 0 0012 6z"/></svg>';
                                                                                }
                                                                                function render(){
                                                                                        const t = document.body.dataset.theme;
                                                                                        toggles.forEach(btn=>{
                                                                                            const label = btn.querySelector('#themeLabel, [data-role="themeLabel"], .theme-label');
                                                                                            const icon = btn.querySelector('#themeIcon, [data-role="themeIcon"], .theme-icon');
                                                                                            if(label) label.textContent = t==='dark'?'Dark':'Light';
                                                                                            if(icon) icon.innerHTML = iconSvg(t);
                                                                                        });
                                                                                }
                                                                                function toggleTheme(){
                                                                                        const next = document.body.dataset.theme==='dark'?'light':'dark';
                                                                                        // animate theme transition by toggling a helper class
                                                                                        document.body.classList.add('theme-transition');
                                                                                        document.body.dataset.theme = next;
                                                                                        try{ localStorage.setItem(KEY,next); }catch(e){}
                                                                                        render();
                                                                                        // remove transition class after animation completes
                                                                                        setTimeout(()=> document.body.classList.remove('theme-transition'), 350);
                                                                                }
                                                                                toggles.forEach(btn=>{
                                                                                    btn.addEventListener('pointerdown', (e)=>{ e.preventDefault(); toggleTheme(); });
                                                                                    btn.addEventListener('touchstart', (e)=>{ e.preventDefault(); toggleTheme(); }, {passive:false});
                                                                                    btn.addEventListener('click', (e)=>{ e.preventDefault(); toggleTheme(); });
                                                                                });
                                                                                render();
                                                                        })();
                                                                        
                                                                                                                                                                                                                                                                                                // About modal (dashboard)
                                                                                                                                                                                                                                                                                                (function(){
                                                                                                                                                                                                                                                                                                                                const aboutBtn = document.querySelector('.about-btn');
                                                                                                                                                                                                                                                                                                                                if(!aboutBtn) return;
                                                                                                                                                                                                                                                                                                                                const overlay = document.createElement('div'); overlay.className='overlay'; overlay.id='aboutOverlay';
                                                                                                                                                                                                                                                                                                                                const modal = document.createElement('div'); modal.className='modal'; modal.id='aboutModal';
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                modal.innerHTML = `
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        <h3>About this website</h3>
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        <div style="max-width:520px;line-height:1.4;color:var(--muted)">
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                <p>It’s a Flask-based web server that provides a REST API + interactive UI for managing Airtable data.</p>

                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                <p>The UI is a dashboard where users can create, read, update, delete (CRUD) records in Airtable tables, with an emphasis on protecting the schema (i.e. users cannot modify table structures or change fields).</p>

                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                <p>It uses an Airtable Personal Access Token (PAT) + Base ID to connect to Airtable.</p>

                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                <p>It has a permissions model: allowed operations include viewing tables, creating/editing/deleting records; disallowed are creating/deleting tables or altering schema.</p>

                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                <p>It has a REST API (endpoints GET /api/tables, etc.) and a web frontend.</p>

                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                <p>It is designed with production considerations in mind (SSL support, error handling).</p>

                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                <p>The tech stack: Python (3.13.8), Flask, uses pyairtable library to interface with Airtable REST API.</p>

                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                <p>Visit the repository that includes documentation: Quickstart, server guide, permissions.</p>

                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                <p><a href="https://github.com/s6ft256/hse-weeky-statistics-form.git" target="_blank" rel="noopener" style="color:var(--accent);font-weight:600">Source code</a></p>
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        </div>
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        <div style="margin-top:10px;color:var(--muted);font-size:12px">developed by Elius @2025 HSE TROJAN CONTRACTING GROUP</div>
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        <div style="margin-top:12px;text-align:right"><button class="tool" id="closeAbout">Close</button></div>
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                `;
                                                                                                                                                                                                                                                                                                                                document.body.appendChild(overlay); document.body.appendChild(modal);
                                                                                                                                                                                                                                                                                                                                aboutBtn.addEventListener('click', ()=>{ overlay.classList.add('show'); modal.classList.add('show'); });
                                                                                                                                                                                                                                                                                                                                document.getElementById('closeAbout')?.addEventListener('click', ()=>{ overlay.classList.remove('show'); modal.classList.remove('show'); });
                                                                                                                                                                                                                                                                                                                                overlay.addEventListener('click', ()=>{ overlay.classList.remove('show'); modal.classList.remove('show'); });
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
<title>hse_statistics_report</title>
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<style>
/* Theme variables */
:root{--bg:#f3f4f6;--card:#ffffff;--fg:#111827;--muted:#6b7280;--accent:#7c3aed;--accent2:#5ce1e6;--accent3:#ffd166;--danger:#dc2626;--border:#e6e9ef;--ease:cubic-bezier(.22,.61,.36,1);--dur:220ms}

/* Dark theme overrides for table views and forms */
html[data-theme="dark"], body[data-theme="dark"]{
        --bg:#0b1028;
        --card:#0f1724;
        --fg:#e6eef8;
        --muted:#94a3b8;
        --accent:#7c3aed;
        --accent2:#5ce1e6;
        --accent3:#ffd166;
        --danger:#f87171;
        --border: rgba(255,255,255,0.06);
        --shadow: rgba(0,0,0,0.6);
}

/* Specific element overrides so forms, modals, tables and overlays match dark theme */
html[data-theme="dark"], body[data-theme="dark"] .form-smooth input,
html[data-theme="dark"], body[data-theme="dark"] .form-smooth select,
html[data-theme="dark"], body[data-theme="dark"] .form-smooth textarea{
        background: var(--card);
        color: var(--fg);
        border: 1px solid var(--border);
}
html[data-theme="dark"], body[data-theme="dark"] .modal{
        background: var(--card);
        color: var(--fg);
        box-shadow: 0 10px 30px rgba(0,0,0,.6);
}
html[data-theme="dark"], body[data-theme="dark"] .overlay{
        background: rgba(0,0,0,.6);
}
html[data-theme="dark"], body[data-theme="dark"] .table-wrap{
        background: var(--card);
        border-color: var(--border);
        box-shadow: 0 8px 24px rgba(0,0,0,.5);
}
html[data-theme="dark"], body[data-theme="dark"] table thead th{ background: var(--card); color: var(--fg); border-bottom-color: var(--border); }
html[data-theme="dark"], body[data-theme="dark"] tbody tr:hover{ background: rgba(255,255,255,0.03); }
html[data-theme="dark"], body[data-theme="dark"] .add-bar{ background: var(--card); border-top-color: var(--border); color: var(--fg); }
html[data-theme="dark"], body[data-theme="dark"] .theme-toggle{ background: var(--card); color: var(--fg); }

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
.tabs{display:flex;gap:8px;overflow:auto;padding:6px 4px}
.tab{padding:8px 14px;border-radius:6px;background:var(--card);color:var(--fg);font-weight:600;border:1px solid var(--border)}
.tab.active{background:linear-gradient(180deg,color-mix(in srgb, var(--accent) 14%, var(--card) 86%), var(--card));border-color:rgba(124,58,237,.12);box-shadow:inset 0 -2px 0 rgba(124,58,237,.12)}
.tab{transition:background var(--dur) var(--ease), color var(--dur) var(--ease), border-color 140ms var(--ease), box-shadow var(--dur) var(--ease)}
.tab:hover{transform:translateY(-1px)}
.page{padding:18px}

header{display:flex;justify-content:space-between;align-items:center;margin-bottom:8px}
header h2{margin:0;font-size:20px;font-weight:600}
header .muted{color:var(--muted);font-size:13px}
/* Back link styling */
.back-link{color:var(--accent);text-decoration:underline;margin:0 8px;padding:6px 8px;border-radius:6px}
.back-link:hover{background:rgba(124,58,237,0.06);text-decoration:none}

.toolbar{display:flex;gap:8px;align-items:center;margin:8px 0;padding:6px 0;background:transparent;border-radius:0}
.tool{display:inline-flex;align-items:center;justify-content:center;padding:6px;width:36px;height:36px;border-radius:8px;background:transparent;color:var(--fg);border:0;cursor:pointer;font-size:0}
        /* visually remove icon glyphs in toolbar so only the compact action controls remain */
        .toolbar .tool .icon, .toolbar .tool svg{display:none !important}
        /* keep hidden labels for screen-readers/fallback, but keep them visually hidden */
        .tool .tool-label{display:none}
body[data-theme="light"] .tool{background:transparent;color:var(--fg);border:0}
html[data-theme="dark"], body[data-theme="dark"] .tool{background:transparent;color:var(--fg);border:0}
.tool .icon{opacity:0.8}
.tool svg path,.tool svg rect,.tool svg circle{fill:currentColor}

/* responsive heading */
@media(max-width:720px){ header h2{font-size:16px} .tool{padding:6px 8px} }

/* Smooth form styles (apply to all forms) */
.form-smooth .form-row{display:flex;flex-direction:column;gap:6px}
.form-smooth .form-label{font-size:13px;color:var(--muted)}
.form-smooth input,.form-smooth select,.form-smooth textarea{padding:10px 12px;border:1px solid var(--border);border-radius:8px;background:var(--card);color:var(--fg);transition:box-shadow .18s ease, border-color .14s ease, transform .08s ease}
.form-smooth input::placeholder,.form-smooth textarea::placeholder{color:var(--muted)}
.form-smooth input:focus,.form-smooth select:focus,.form-smooth textarea:focus{outline:0;border-color:var(--accent);box-shadow:0 8px 30px rgba(124,58,237,.12)}
.form-smooth button,.tool,.add-btn{transition:background .16s ease, color .12s ease, transform .08s ease, box-shadow .16s ease}
.form-smooth button:hover,.tool:hover,.add-btn:hover{transform:translateY(-1px)}
.form-smooth button:active,.tool:active,.add-btn:active{transform:translateY(0)}
.field-error{color:var(--danger);font-size:12px;min-height:16px;margin-top:4px}

/* Density toggle */
body[data-density="compact"] th, body[data-density="compact"] td{padding:6px 10px}
body[data-density="compact"] .form-smooth input, body[data-density="compact"] .form-smooth select, body[data-density="compact"] .form-smooth textarea{padding:6px 8px;border-radius:6px}
body[data-density="compact"] .add-btn{padding:6px 10px}

.table-wrap{background:var(--card);border-radius:8px;box-shadow:0 8px 24px rgba(2,6,23,.06);overflow:auto}
table{width:100%;border-collapse:collapse}
.hdr-sort{opacity:0.45;margin-left:8px;font-size:12px}
.cell-trunc{max-width:none;white-space:normal;overflow:visible;text-overflow:clip;word-break:break-word;position:relative}
/* collapsed preview for long text in cells */
.cell-content{transition: max-height .18s ease, box-shadow .18s ease}
.cell-content.collapsed{max-height:4.5em;overflow:hidden}
.cell-content.expanded{max-height:none}
.expand-btn{position:absolute;right:8px;bottom:6px;background:rgba(0,0,0,.06);border-radius:6px;padding:4px 6px;font-size:12px;cursor:pointer;color:var(--muted);border:1px solid rgba(0,0,0,.06)}
.cell-trunc .expand-btn{background:rgba(255,255,255,0.9)}
/* theme-aware expand button */
html[data-theme="dark"], body[data-theme="dark"] .expand-btn{background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.06);color:var(--muted)}
.sort-asc .hdr-sort{color:var(--accent)}
.sort-desc .hdr-sort{color:var(--accent)}
th,td{padding:12px 16px;border-bottom:1px solid var(--border);text-align:left;font-size:15px}
thead th{position:sticky;top:0;background:var(--card);border-bottom:2px solid var(--border);color:var(--fg)}
.row-index{width:64px;text-align:center;color:var(--muted)}
.row-select{width:56px;text-align:center}
tbody tr:hover{background:rgba(0,0,0,.02)}
html[data-theme="dark"], body[data-theme="dark"] tbody tr:hover{background:rgba(255,255,255,0.02)}

/* Inline editors inside grid cells reflect theme */
#gridBody td[data-col-index] input,
#gridBody td[data-col-index] textarea,
#gridBody td[data-col-index] select{width:100%;box-sizing:border-box;background:var(--card);color:var(--fg);border:1px solid var(--border);border-radius:6px;padding:6px 8px}

/* bottom add bar */
.add-bar{position:fixed;left:0;right:0;bottom:0;background:var(--card);border-top:1px solid var(--border);padding:10px 18px;display:flex;justify-content:flex-start;align-items:center;gap:10px}
.add-btn{background:var(--accent);color:var(--card);padding:8px 12px;border-radius:8px;border:0;cursor:pointer;font-weight:600}

/* small modal & overlay */
.overlay{position:fixed;left:0;top:0;right:0;bottom:0;background:rgba(0,0,0,.24);display:none;opacity:0;transition:opacity .22s ease;z-index:30}
.overlay.show{display:block;opacity:1}
.modal{position:fixed;left:50%;top:48%;transform:translate(-50%,-46%);background:var(--card);color:var(--fg);padding:14px;border-radius:8px;box-shadow:0 10px 30px rgba(2,6,23,.12);display:block;opacity:0;transition:opacity .22s ease,transform .22s ease;z-index:40}
.modal.show{opacity:1;transform:translate(-50%,-50%)}

./* Banner shared styles (like dashboard) */
.banner{height:320px;background:linear-gradient(180deg,var(--bg),var(--card));display:flex;align-items:center;justify-content:center;padding:24px 18px;border-bottom:1px solid rgba(255,255,255,.03);position:relative;box-sizing:border-box}
.banner{transition:background 240ms var(--ease)}
.hero{max-width:1100px;width:100%;background:var(--card);padding:20px;border-radius:14px;box-shadow:0 12px 40px var(--shadow), 0 0 0 1px var(--border);text-align:center;position:relative;min-height:220px;z-index:1;display:flex;flex-direction:column;align-items:center;justify-content:center;margin:0 auto}
.hero::after{content:"";position:absolute;inset:-32px;background:radial-gradient(ellipse at 50% -10%, rgba(124,58,237,.16), rgba(124,58,237,0) 60%), radial-gradient(ellipse at 10% 50%, rgba(59,130,246,.12), rgba(59,130,246,0) 50%), radial-gradient(ellipse at 90% 50%, rgba(234,179,8,.12), rgba(234,179,8,0) 50%);filter:blur(26px);z-index:-1;pointer-events:none}
.logo{width:220px;height:220px;background-size:contain;background-repeat:no-repeat;background-position:center;margin:0 auto 8px;flex:0 0 auto}
@media (max-width: 800px){ .logo{width:140px;height:140px} .banner{height:240px} }

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
                                <button class="theme-toggle" aria-label="Toggle theme" style="margin-right:6px"><span id="themeIcon" class="theme-icon"></span><span id="themeLabel" class="theme-label"></span></button>
                                <a href="/" class="back-link">Back</a>
                                <button class="add-btn" id="openAddBtn">+ Add</button>
                        </div>
                </header>

                <div class="toolbar">
                        <div class="tool" id="hideFieldsBtn" role="button" aria-label="Hide fields"><span class="icon" aria-hidden="true"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M12 5C7 5 3.2 8.4 1.5 12c1.7 3.6 5.5 7 10.5 7s8.8-3.4 10.5-7C20.8 8.4 17 5 12 5z" fill="currentColor"/><circle cx="12" cy="12" r="3" fill="currentColor"/></svg></span><span class="tool-label">Hide fields</span></div>
                        <div class="tool" id="filterBtn" role="button" aria-label="Filter"><span class="icon" aria-hidden="true"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M3 5h18v2L13 14v5l-2 1v-6L3 7V5z" fill="currentColor"/></svg></span><span class="tool-label">Filter</span></div>
                        <div class="tool" id="groupBtn" role="button" aria-label="Group"><span class="icon" aria-hidden="true"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><rect x="3" y="5" width="8" height="6" rx="1.2" fill="currentColor"/><rect x="13" y="5" width="8" height="6" rx="1.2" fill="currentColor"/><rect x="3" y="13" width="8" height="6" rx="1.2" fill="currentColor"/></svg></span><span class="tool-label">Group</span></div>
                        <div class="tool" id="sortBtn" role="button" aria-label="Sort"><span class="icon" aria-hidden="true"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M7 10h6v2H7v-2zM7 6h10v2H7V6zM7 14h4v2H7v-2z" fill="currentColor"/></svg></span><span class="tool-label">Sort</span></div>
                </div>

                                <div class="overlay" id="overlay"></div>

                                <!-- Hide fields modal (persistent) -->
                                <div class="modal" id="fieldModal">
                                        <h3>Hide fields</h3>
                                        <div id="fieldList"></div>
                                        <div style="margin-top:12px"><button id="applyHide" class="tool" aria-label="Apply"><span class="icon" aria-hidden="true">✓</span><span class="tool-label">Apply</span></button> <button id="cancelHide" class="tool" aria-label="Cancel"><span class="icon" aria-hidden="true">✕</span><span class="tool-label">Cancel</span></button></div>
                                </div>

                                                                   <div class="modal" id="filterModal">
                                                                           <h3>Filter</h3>
                                                                           <div style="display:flex;gap:8px;align-items:center;margin-top:8px">
                                                                                   <select id="filterFieldSelect"></select>
                                                                                   <select id="filterOpSelect"><option value="contains">contains</option><option value="equals">equals</option></select>
                                                                                   <input id="filterValueInput" placeholder="value" style="flex:1;padding:6px;border:1px solid #e6e9ef;border-radius:6px">
                                                                           </div>
                                                                           <div style="margin-top:12px"><button id="applyFilterModal" class="tool" aria-label="Apply filter"><span class="icon" aria-hidden="true">✓</span><span class="tool-label">Apply</span></button> <button id="clearFilterModal" class="tool" aria-label="Clear filter"><span class="icon" aria-hidden="true">↺</span><span class="tool-label">Clear</span></button> <button id="cancelFilter" class="tool" aria-label="Cancel filter"><span class="icon" aria-hidden="true">✕</span><span class="tool-label">Cancel</span></button></div>
                                                                   </div>

                                <!-- Filter modal (single-condition builder) -->
                                <div class="modal" id="filterModal">
                                        <h3>Filter</h3>
                                        <div style="display:flex;gap:8px;align-items:center">
                                                <select id="filterFieldSelect"></select>
                                                <select id="filterOpSelect"><option value="contains">contains</option><option value="equals">equals</option><option value="starts">starts with</option></select>
                                                <input id="filterInput" placeholder="value">
                                        </div>
                                        <div style="margin-top:12px"><button id="applyFilterBtn" class="tool" aria-label="Apply filter"><span class="icon" aria-hidden="true">✓</span><span class="tool-label">Apply</span></button> <button id="cancelFilterBtn" class="tool" aria-label="Cancel filter"><span class="icon" aria-hidden="true">✕</span><span class="tool-label">Cancel</span></button></div>
                                </div>

                                <!-- Add Record modal -->
                                                                                                                                <div class="modal" id="addRecordModal">
                                        <h3>Add record</h3>
                                                                                                                                                                <form id="addRecordForm" class="form-smooth">
                                          <div id="addFormFields" style="display:flex;flex-direction:column;gap:8px;margin-top:8px"></div>
                                          <div style="margin-top:12px;display:flex;gap:8px;justify-content:flex-end">
                                            <button type="button" id="submitAdd" class="tool" aria-label="Create record"><span class="icon" aria-hidden="true">✓</span><span class="tool-label">Create</span></button>
                                            <button type="button" id="cancelAdd" class="tool" aria-label="Cancel add"><span class="icon" aria-hidden="true">✕</span><span class="tool-label">Cancel</span></button>
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
                                                                                {% for c in r.cells %}
                                                                                        <td data-col-index="{{ loop.index0 }}" class="cell-trunc">
                                                                                                <div class="cell-content" style="white-space:pre-wrap;word-break:break-word;">{{ c|e }}</div>
                                                                                        </td>
                                                                                {% endfor %}
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
                                                                <td class="row-select" style="text-align:center;font-size:18px;color:var(--accent)">＋</td>
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
        <div style="padding:10px 18px;text-align:center;color:var(--muted);font-size:12px;font-weight:700">&copy; 2025 HSE TROJAN CONSTRUCTION GROUP &nbsp;·&nbsp; Developed by Elius</div>

<script>
        // Initialize theme from localStorage and wire theme-toggle buttons
        (function(){
                const KEY='theme';
                const saved = localStorage.getItem(KEY) || 'light';
                document.body.dataset.theme = saved;
                const toggles = Array.from(document.querySelectorAll('.theme-toggle'));
                function iconSvg(t){
                    return t==='dark'
                      ? '<svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor" xmlns="http://www.w3.org/2000/svg"><path d="M21 12.79A9 9 0 1111.21 3 7 7 0 0021 12.79z"/></svg>'
                      : '<svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor" xmlns="http://www.w3.org/2000/svg"><path d="M6.76 4.84l-1.8-1.79-1.41 1.41 1.79 1.8 1.42-1.42zM1 13h3v-2H1v2zm10-9h2V1h-2v3zm7.04 2.46l1.79-1.8-1.41-1.41-1.8 1.79 1.42 1.42zM17 13h3v-2h-3v2zm-5 8h2v-3h-2v3zm-7.66-2.34l1.41 1.41 1.8-1.79-1.42-1.42-1.79 1.8zM20 20l1.41 1.41 1.41-1.41-1.41-1.41L20 20zM12 6a6 6 0 100 12A6 6 0 0012 6z"/></svg>';
                }
                function render(){
                        const t = document.body.dataset.theme;
                        toggles.forEach(btn=>{
                            const label = btn.querySelector('#themeLabel, [data-role="themeLabel"], .theme-label');
                            const icon = btn.querySelector('#themeIcon, [data-role="themeIcon"], .theme-icon');
                            if(label) label.textContent = t==='dark'?'Dark':'Light';
                            if(icon) icon.innerHTML = iconSvg(t);
                        });
                }
                function toggleTheme(){
                        const next = document.body.dataset.theme==='dark'?'light':'dark';
                        document.body.classList.add('theme-transition');
                        document.body.dataset.theme = next;
                        try{ localStorage.setItem(KEY,next); }catch(e){}
                        render();
                        setTimeout(()=> document.body.classList.remove('theme-transition'), 350);
                }
                toggles.forEach(btn=>{
                    btn.addEventListener('pointerdown', (e)=>{ e.preventDefault(); toggleTheme(); });
                    btn.addEventListener('touchstart', (e)=>{ e.preventDefault(); toggleTheme(); }, {passive:false});
                    btn.addEventListener('click', (e)=>{ e.preventDefault(); toggleTheme(); });
                });
                render();
        })();        // Density toggle persistence (comfortable/compact)
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
        // Raw Airtable records (exact data from API)
        const RECORDS_RAW = {{ records|tojson | safe }};
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

        // tooltips (show full text on hover) — do not force truncation; allow cells to wrap
        document.querySelectorAll('tbody td').forEach(td=>{
                if(td.classList.contains('row-select') || td.classList.contains('row-index')) return;
                const txt = (td.textContent||'').trim();
                td.title = txt;
        });

        // Inline editing: click a cell to edit
        (function(){
                const meta = window.FIELDS_META || [];
                function fieldMetaByIndex(i){ return meta[i] || {name: window.FIELDS[i] || '', type: 'text'}; }
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

        // Double-click a row to view the exact Airtable record JSON in a modal
        (function(){
                // create raw modal elements
                let rawOverlay = document.getElementById('rawOverlay');
                let rawModal = document.getElementById('rawModal');
                if(!rawOverlay){
                        rawOverlay = document.createElement('div'); rawOverlay.id = 'rawOverlay'; rawOverlay.style.cssText = 'position:fixed;left:0;top:0;right:0;bottom:0;background:rgba(0,0,0,.36);display:none;z-index:120;'; document.body.appendChild(rawOverlay);
                }
                if(!rawModal){
                        rawModal = document.createElement('div'); rawModal.id = 'rawModal'; rawModal.style.cssText = 'position:fixed;left:50%;top:50%;transform:translate(-50%,-50%);min-width:320px;max-width:90%;max-height:80%;overflow:auto;background:#fff;padding:12px;border-radius:8px;box-shadow:0 12px 40px rgba(2,6,23,.12);display:none;z-index:130;font-family:monospace;font-size:13px;color:#111827';
                        const closeBtn = document.createElement('button'); closeBtn.className='tool'; closeBtn.setAttribute('aria-label','Close'); closeBtn.style.marginBottom='8px'; closeBtn.innerHTML = '<span class="icon" aria-hidden="true">✕</span><span class="tool-label">Close</span>'; closeBtn.addEventListener('click', ()=>{ rawOverlay.style.display='none'; rawModal.style.display='none'; });
                        const pre = document.createElement('pre'); pre.id = '__raw_json'; pre.style.whiteSpace='pre-wrap'; pre.style.wordBreak='break-word'; pre.style.margin=0; pre.style.padding='6px'; rawModal.appendChild(closeBtn); rawModal.appendChild(pre); document.body.appendChild(rawModal);
                }

                function showRawForId(id){
                        if(!id) return;
                        const rec = (RECORDS_RAW || []).find(r=>r && (r.id===id || r.recordId===id));
                        const pre = document.getElementById('__raw_json');
                        if(!rec){
                                if(pre) pre.textContent = 'Record not found.';
                        }else{
                                if(pre) pre.textContent = JSON.stringify(rec, null, 2);
                        }
                        rawOverlay.style.display='block'; rawModal.style.display='block';
                }

                // double-click handler on rows
                document.addEventListener('dblclick', (e)=>{
                        const tr = e.target && e.target.closest && e.target.closest('#gridBody tr');
                        if(!tr) return;
                        const rid = tr.dataset && tr.dataset.id;
                        if(!rid) return;
                        showRawForId(rid);
                });

                // click on overlay closes modal
                rawOverlay.addEventListener('click', ()=>{ rawOverlay.style.display='none'; rawModal.style.display='none'; });
        })();

        // apply persisted hidden columns on load
        applyHidden();
        updateSelectedCount();

        // Add expand/collapse buttons for long cell content
        (function(){
                const rows = document.querySelectorAll('#gridBody tr');
                rows.forEach(tr=>{
                        Array.from(tr.querySelectorAll('.cell-content')).forEach(div=>{
                                // collapse by default if content is large
                                if(div.scrollHeight > div.clientHeight + 12 || div.textContent.split('\n').length > 3 || div.textContent.length > 180){
                                        div.classList.add('collapsed');
                                        const btn = document.createElement('button'); btn.className='expand-btn'; btn.textContent='Expand';
                                        btn.addEventListener('click', (e)=>{ e.stopPropagation(); const d=div; if(d.classList.contains('collapsed')){ d.classList.remove('collapsed'); d.classList.add('expanded'); btn.textContent='Collapse'; } else { d.classList.remove('expanded'); d.classList.add('collapsed'); btn.textContent='Expand'; } });
                                        // place the button inside the cell container
                                        const parentTd = div.closest('td'); if(parentTd) parentTd.appendChild(btn);
                                }
                        });
                });
        })();

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
                                const m = meta.find(x=>x.name===f) || {name:f,client_name:(typeof f==='string'?f.replace(/\\s+/g,' ').trim():f),type:'text',choices:null,required:false,editable:true};
                                // Skip non-editable fields (autoNumber, read-only, etc.)
                                if(m.editable === false) return;
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
                                // use client-safe name (normalized) for form input keys
                                input.name = m.client_name || f;
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
                                        // show success toast then return to main menu
                                        showToast('Record created', 'success');
                                        // small delay so user sees the toast before redirect
                                        setTimeout(()=>{ window.location.href = '/'; }, 800);
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

                function normalize_field_name(s) {
                                // Client-side no-op: server performs robust normalization.
                                // Keep function for compatibility if any inline scripts call it.
                                try{ if(typeof s !== 'string') return s; return s.replace(/\\s+/g,' ').trim(); }catch(e){ return s; }
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
                                # Only add table if we have permission to access it
                                tables.append({'name': name, 'id': t.id, 'count': count})
                                total_records += count
                        except Exception as e:
                                # Skip tables we don't have permission to access
                                error_msg = str(e).lower()
                                if 'permission' in error_msg or 'forbidden' in error_msg or 'not found' in error_msg:
                                        print(f'[!] Skipping table {name} (permission denied)')
                                        continue
                                # For other errors, still add the table with 0 count as fallback
                                print(f'[!] Error counting records in {name}: {e}')
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
                error_msg = str(e).lower()
                if 'permission' in error_msg or 'forbidden' in error_msg or 'not found' in error_msg:
                        return f'Access denied to table "{table_name}". Your token may not have permission to access this table. <a href="/">Back to dashboard</a>', 403
                return f'Error fetching records for {table_name}: {e} <a href="/">Back to dashboard</a>', 500

        # Determine ordered fields from schema and build metadata per field
        fields = []
        fields_meta = []
        try:
                meta = api.base(AIRTABLE_BASE_ID).schema()
                t = next((x for x in meta.tables if x.name == table_name), None)
                if t and hasattr(t, 'fields'):
                        for f in t.fields:
                                # field object may contain name, type, required, options/choices
                                # Preserve the exact Airtable field name (do not strip)
                                fname = getattr(f, 'name', None) or getattr(f, 'id', '')
                                # client-safe name used for HTML form inputs
                                client_name = normalize_field_name(fname) if isinstance(fname, str) else fname
                                ftype = getattr(f, 'type', None) or getattr(f, 'typeName', None) or 'text'
                                read_only = bool(getattr(f, 'read_only', False) or getattr(f, 'readOnly', False))
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
                                # Include editable flag to indicate if field can be edited
                                is_editable = ftype not in ('autoNumber',) and not read_only
                                fields_meta.append({'name': fname, 'client_name': client_name, 'type': ftype, 'choices': choices, 'required': required, 'editable': is_editable})
        except Exception:
                pass

        if not fields:
                seen = []
                for r in records:
                        for k in r.get('fields', {}).keys():
                                if k not in seen:
                                        seen.append(k)
                fields = seen
                # fallback metadata: text inputs, all editable
                fields_meta = [{'name': n, 'type': 'text', 'choices': None, 'required': False, 'editable': True} for n in fields]

        display_records = []
        # Render table cells. Show a single dot '.' for empty/missing values so blank cells are visible.
        # Also ensure fields like 'X.CRS' and 'Definitions' (which are often empty) display '.' when missing.
        def _render_cell(value, field_name=None):
                # Return exact Airtable data:
                # - None -> empty string (no placeholder)
                # - list -> comma-separated
                # - dict -> JSON string
                # - otherwise str(value)
                if value is None:
                        return ''
                if isinstance(value, list):
                        return ', '.join(str(x) for x in value)
                if isinstance(value, dict):
                        try:
                                return json.dumps(value)
                        except Exception:
                                return str(value)
                return str(value)

        for r in records:
                cells = []
                for f in fields:
                        v = r.get('fields', {}).get(f, None)
                        # Always show '.' for empty values; ensure X.CRS and Definitions appear as '.' when empty
                        cell_text = _render_cell(v, f)
                        cells.append(cell_text)
                display_records.append({'id': r.get('id'), 'cells': cells})

        # build lightweight table list for the top tab strip (names + ids)
        tables = []
        try:
                meta = api.base(AIRTABLE_BASE_ID).schema()
                for t in meta.tables:
                        tables.append({'name': t.name, 'id': t.id})
        except Exception:
                pass

        return render_template_string(_TABLE, table_name=table_name, fields=fields, fields_meta=fields_meta, display_records=display_records, tables=tables, records=records)


@app.route('/add_record/<path:table_name>', methods=['GET', 'POST'])
def add_record(table_name):
        if api is None:
                return 'Airtable API not initialized', 500
        table = base.table(table_name)

        if request.method == 'POST':
                # Collect form values (skip empty)
                raw = {k: v for k, v in request.form.items() if v is not None and v != ''}

                # Build a mapping of client-safe name -> actual field name from schema
                meta_fields = []
                try:
                        meta = api.base(AIRTABLE_BASE_ID).schema()
                        t = next((x for x in meta.tables if x.name == table_name), None)
                        if t and hasattr(t, 'fields'):
                                for f in t.fields:
                                        fname = getattr(f, 'name', None) or getattr(f, 'id', '')
                                        ftype = getattr(f, 'type', None) or getattr(f, 'typeName', None) or 'text'
                                        read_only = bool(getattr(f, 'read_only', False) or getattr(f, 'readOnly', False))
                                        if ftype not in ('autoNumber',) and not read_only:
                                                client_name = normalize_field_name(fname) if isinstance(fname, str) else fname
                                                meta_fields.append({'name': fname, 'client_name': client_name})
                except Exception:
                        meta_fields = []

                client_to_actual = { mf['client_name']: mf['name'] for mf in meta_fields }

                # Map incoming form keys (which may be client-safe) to actual field names
                mapped_payload = {}
                for k, v in raw.items():
                        if k in client_to_actual:
                                mapped_payload[client_to_actual[k]] = v
                        else:
                                nk = normalize_field_name(k) if isinstance(k, str) else k
                                if nk in client_to_actual:
                                        mapped_payload[client_to_actual[nk]] = v
                                else:
                                        # pass-through unknown key
                                        mapped_payload[k] = v

                # Coerce using schema
                meta_for_coerce = []
                try:
                        meta = api.base(AIRTABLE_BASE_ID).schema()
                        t = next((x for x in meta.tables if x.name == table_name), None)
                        if t and hasattr(t, 'fields'):
                                for f in t.fields:
                                        an = getattr(f, 'name', None) or getattr(f, 'id', '')
                                        ftype = getattr(f, 'type', None) or getattr(f, 'typeName', None) or 'text'
                                        choices = []
                                        if hasattr(f, 'options') and getattr(f, 'options'):
                                                choices = [getattr(c, 'name', c if isinstance(c, str) else '') for c in getattr(f.options, 'choices', []) or []]
                                        required = bool(getattr(f, 'required', False) or getattr(f, 'isRequired', False))
                                        meta_for_coerce.append({'name': an, 'type': ftype, 'choices': choices, 'required': required})
                except Exception:
                        meta_for_coerce = []

                body, errors = coerce_payload_to_body(mapped_payload, meta_for_coerce)
                if errors:
                        return f'Validation failed: {errors}', 400
                try:
                        new = table.create(body)
                        # Return a small success page that notifies the user and returns to main menu
                        new_id = new.get('id')
                        return f'''<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Success</title>
                        <script>try{{ const t = localStorage.getItem('theme') || 'light'; document.documentElement.dataset.theme = t; if(document.body) document.body.dataset.theme = t; }}catch(e){{}}</script>
                        <style>body{{font-family:Inter,Segoe UI,Arial,Helvetica,sans-serif;background:#f8fafc;color:#111827;margin:0;display:flex;align-items:center;justify-content:center;height:100vh}}.card{{background:#fff;padding:20px;border-radius:8px;box-shadow:0 12px 40px rgba(2,6,23,.08);text-align:center}}</style>
                        </head><body><div class="card"><h2>Success</h2><p>Record created: {new_id}</p><p>Returning to main menu...</p></div>
                        <script>setTimeout(function(){{window.location.href='/' }},800);</script></body></html>'''
                except Exception as e:
                        emsg = str(e)
                        if 'UNKNOWN_FIELD_NAME' in emsg or 'Unknown field name' in emsg or 'unknown_field_name' in emsg.lower():
                                return f'Error creating record: Unknown field name. Payload keys: {list(body.keys())} - Airtable error: {e}', 500
                        return f'Error creating record: {e}', 500

        # Build best-effort form fields (skip autoNumber and read-only fields)
        form_fields = []
        try:
                meta = api.base(AIRTABLE_BASE_ID).schema()
                t = next((x for x in meta.tables if x.name == table_name), None)
                if t and hasattr(t, 'fields'):
                        for f in t.fields:
                                # Skip autoNumber and read-only fields
                                fname = getattr(f, 'name', None) or getattr(f, 'id', '')
                                # Normalize field name: strip whitespace
                                fname = fname.strip() if isinstance(fname, str) else fname
                                ftype = getattr(f, 'type', None) or getattr(f, 'typeName', None) or 'text'
                                read_only = bool(getattr(f, 'read_only', False) or getattr(f, 'readOnly', False))
                                if ftype != 'autoNumber' and not read_only:
                                        form_fields.append({'name': fname, 'type': 'text'})
        except Exception:
                try:
                        sample = table.all(max_records=10)
                        names = set()
                        for r in sample:
                                names.update(r.get('fields', {}).keys())
                        form_fields = [{'name': n, 'type': 'text'} for n in sorted(names)]
                except Exception:
                        form_fields = [{'name': 'Name', 'type': 'text'}, {'name': 'Description', 'type': 'text'}]

        form_html = ['<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Add Record</title>\n<script>\n  (function(){\n    try{ const t = localStorage.getItem("theme") || "light"; document.documentElement.dataset.theme = t; if(document.body) document.body.dataset.theme = t; else document.addEventListener("DOMContentLoaded", ()=> document.body.dataset.theme = t); }catch(e){}\n  })();\n</script>\n<style>\n:root{--bg:#f8fafc;--fg:#111827;--card:#ffffff;--muted:#6b7280;--border:#e5e7eb}\nbody{font-family:Inter,Segoe UI,Arial,Helvetica,sans-serif;margin:0;background:var(--bg);color:var(--fg);padding:18px}\n.container{max-width:800px;margin:0 auto}\n.h1{font-size:22px;margin-bottom:12px}\n.form-smooth .form-row{display:flex;flex-direction:column;gap:6px;margin-bottom:10px}\n.form-smooth label{font-size:13px;color:var(--muted)}\n.form-smooth input,.form-smooth select,.form-smooth textarea{padding:10px 12px;border:1px solid var(--border);border-radius:8px;background:var(--card);color:var(--fg);transition:box-shadow .18s ease, border-color .14s ease, transform .08s ease}\n.form-smooth input:focus,.form-smooth select:focus,.form-smooth textarea:focus{outline:0;border-color:#7c3aed;box-shadow:0 8px 30px rgba(124,58,237,.18)}\n/* dark theme for standalone form */\nbody[data-theme="dark"]{ --bg:#0b1028; --card:#0f1724; --fg:#e6eef8; --muted:#94a3b8; --border: rgba(255,255,255,0.06); }\nbody[data-theme="dark"] .form-smooth input, body[data-theme="dark"] .form-smooth select, body[data-theme="dark"] .form-smooth textarea{ background:var(--card); color:var(--fg); border:1px solid var(--border); }\n.btn{background:#7c3aed;color:#fff;padding:8px 12px;border-radius:8px;border:0;cursor:pointer;transition:transform .1s ease, box-shadow .16s ease}\n.btn:hover{transform:translateY(-1px);box-shadow:0 8px 20px rgba(124,58,237,.22)}\n.btn:disabled{opacity:.6;cursor:not-allowed}\n.link{color:#7c3aed}\n</style>\n</head><body><div class="container">']
        form_html.append(f'<h1 class="h1">Add Record to {table_name}</h1>')
        # inline success message (hidden by default)
        form_html.append('<div id="successMsg" style="display:none;padding:10px;border-radius:6px;background:#10b981;color:#fff;margin-bottom:12px;text-align:center;font-weight:600">Success</div>')
        # Use AJAX submit so we can show a simple inline success message
        form_html.append(f'<form id="addForm" method="post" class="form-smooth">')
        for f in form_fields:
                # use data-name attributes safe for JSON keys; names may contain spaces
                form_html.append(f'<div class="form-row"><label>{f["name"]}</label><input name="{f["name"]}" /></div>')
        form_html.append(f'<p><button type="submit" class="btn">Create</button> <a class="link" href="/table/{table_name}">Cancel</a></p>')
        # script to intercept submit and call AJAX endpoint; on success show inline message then redirect back to table
        js_template = '''<script>
document.getElementById('addForm').addEventListener('submit', async function(e){
  e.preventDefault();
  const fd = new FormData(e.target);
  const payload = {};
  fd.forEach((v,k)=> payload[k]=v);
  try{
    const res = await fetch('/add_record_ajax/{table}', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(payload)});
    const j = await res.json();
    if(j && j.ok){
      const msg = document.getElementById('successMsg'); msg.textContent = 'Success'; msg.style.display = 'block';
      setTimeout(function(){ window.location.href = '/table/{table}'; }, 800);
    } else {
      alert((j && j.error) ? j.error : 'Error creating record');
    }
  } catch(err){ alert('Network error'); console.error(err); }
});
</script>'''
        # use simple replace to avoid conflicts with JS braces when formatting
        form_html.append(js_template.replace('{table}', table_name))

        # Return the rendered simple form page
        return ''.join(form_html)


@app.route('/add_record_ajax/<path:table_name>', methods=['POST'])
def add_record_ajax(table_name):
        """AJAX endpoint to create a record for a given table.
        Builds schema metadata (best-effort), normalizes field names, validates and coerces values,
        and creates the record. Returns JSON with field-level errors when validation fails.
        """
        if api is None:
                return jsonify({'ok': False, 'error': 'Airtable API not initialized'}), 500

        payload = request.get_json(force=True) or {}

        # Build meta_fields from schema when available
        meta_fields = []
        try:
                meta = api.base(AIRTABLE_BASE_ID).schema()
                t = next((x for x in meta.tables if x.name == table_name), None)
                if t and hasattr(t, 'fields'):
                        for f in t.fields:
                                actual_name = getattr(f, 'name', None) or getattr(f, 'id', '')
                                # Keep actual name but store normalized mapping separately
                                actual_name = actual_name if isinstance(actual_name, str) else actual_name
                                ftype = getattr(f, 'type', None) or getattr(f, 'typeName', None) or 'text'
                                read_only = bool(getattr(f, 'read_only', False) or getattr(f, 'readOnly', False))
                                required = bool(getattr(f, 'required', False) or getattr(f, 'isRequired', False))
                                choices = None
                                if hasattr(f, 'options') and getattr(f, 'options'):
                                        choices = [getattr(c, 'name', c if isinstance(c, str) else '') for c in getattr(f.options, 'choices', []) or []]
                                if ftype not in ('autoNumber',) and not read_only:
                                        meta_fields.append({'name': actual_name, 'type': ftype, 'required': required, 'choices': choices})
        except Exception:
                meta_fields = []

        errors = {}
        body = {}

        # Map client_name -> actual schema name
        client_to_actual = {}
        for mf in meta_fields:
                name = mf.get('name')
                client = mf.get('client_name') or (normalize_field_name(name) if isinstance(name, str) else name)
                client_to_actual[client] = name

        # Remap incoming payload keys (which are client-safe names) to actual schema names
        mapped_payload = {}
        if isinstance(payload, dict):
                for k, v in payload.items():
                        if k in client_to_actual:
                                mapped_payload[client_to_actual[k]] = v
                        else:
                                # also try normalized lookup
                                nk = normalize_field_name(k) if isinstance(k, str) else k
                                if nk in client_to_actual:
                                        mapped_payload[client_to_actual[nk]] = v
                                else:
                                        mapped_payload[k] = v
        else:
                mapped_payload = payload


        # Coerce and validate using helper
        body, errors = coerce_payload_to_body(mapped_payload, meta_fields)

        if errors:
                return jsonify({'ok': False, 'errors': errors}), 400

        try:
                new = base.table(table_name).create(body)
                return jsonify({'ok': True, 'id': new.get('id')})
        except Exception as e:
                error_msg = str(e).lower()
                error_str = str(e)
                if 'unknown_field_name' in error_msg or 'unknown field name' in error_msg:
                        match = re.search(r'Unknown field name[:\s]+["\']?([^"\']+)["\']?', error_str)
                        field_info = f' ({match.group(1)})' if match else ''
                        return jsonify({'ok': False, 'error': f'Field name not recognized{field_info}. This might indicate the field has whitespace or special characters that need correction.'}), 422
                elif 'invalid_value_for_column' in error_msg or 'invalid_value' in error_msg:
                        return jsonify({'ok': False, 'error': f'One or more field values are invalid. Please check your input and try again.'}), 422
                elif 'permission' in error_msg or 'forbidden' in error_msg:
                        return jsonify({'ok': False, 'error': 'You do not have permission to create records in this table.'}), 403
                else:
                        return jsonify({'ok': False, 'error': str(e)}), 500

        # end of add_record_ajax


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
        from flask import redirect
        return redirect('/favicon.svg')


@app.route('/favicon.svg')
def favicon_svg():
        """Return an inline SVG that masks the external image into a circle for browsers that support SVG favicons."""
        svg = '''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 64 64">
  <defs>
    <clipPath id="c"><circle cx="32" cy="32" r="32"/></clipPath>
  </defs>
  <image clip-path="url(#c)" width="64" height="64" href="https://tse1.mm.bing.net/th/id/OIP.n30HBYs76HyBK5_D2EyZdQHaEK?cb=12&rs=1&pid=ImgDetMain&o=7&rm=3" preserveAspectRatio="xMidYMid slice"/>
</svg>'''
        from flask import Response
        return Response(svg, mimetype='image/svg+xml')


if __name__ == '__main__':
        # Local development
        port = int(os.environ.get('PORT', 8080))
        print(f'[*] Starting Enhanced Airtable Dashboard on http://localhost:{port}')
        app.run(debug=True, host='0.0.0.0', port=port)