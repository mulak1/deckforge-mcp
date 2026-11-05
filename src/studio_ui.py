"""
Interactive Executive Presentation Studio for DeckForge.
Served at GET / on port 8793 and via resource ui://deckforge/studio.
Includes bespoke SVG brand mark, warm welcome greeting, 4 architectural visual styles,
8 slide layouts, 8 business templates, CSV/Sheet data importer, and 4 configurable chart types.
"""

from __future__ import annotations

from src.studio_assets import STUDIO_CSS, STUDIO_JS

DECKFORGE_LOGO_SVG = """<svg id="deckforgeBrandLogo" width="38" height="38" viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg" style="flex-shrink:0;filter:drop-shadow(0 4px 12px rgba(56,189,248,0.28));">
  <defs>
    <linearGradient id="dfGradBg" x1="0" y1="0" x2="48" y2="48" gradientUnits="userSpaceOnUse">
      <stop offset="0%" stop-color="#0F172A"/>
      <stop offset="55%" stop-color="#1E1B4B"/>
      <stop offset="100%" stop-color="#0284C7"/>
    </linearGradient>
    <linearGradient id="dfGradBackSlide" x1="8" y1="10" x2="36" y2="34" gradientUnits="userSpaceOnUse">
      <stop offset="0%" stop-color="#6366F1"/>
      <stop offset="100%" stop-color="#3B82F6"/>
    </linearGradient>
    <linearGradient id="dfGradFrontSlide" x1="12" y1="14" x2="40" y2="38" gradientUnits="userSpaceOnUse">
      <stop offset="0%" stop-color="#38BDF8"/>
      <stop offset="100%" stop-color="#0284C7"/>
    </linearGradient>
    <linearGradient id="dfGradSpark" x1="28" y1="6" x2="42" y2="20" gradientUnits="userSpaceOnUse">
      <stop offset="0%" stop-color="#FDE047"/>
      <stop offset="100%" stop-color="#F59E0B"/>
    </linearGradient>
  </defs>
  <rect x="2" y="2" width="44" height="44" rx="12" fill="url(#dfGradBg)" stroke="#38BDF8" stroke-width="1.4" stroke-opacity="0.55"/>
  <rect x="8" y="13" width="24" height="16" rx="3.5" transform="rotate(-8 8 13)" fill="url(#dfGradBackSlide)" opacity="0.72"/>
  <rect x="11" y="16" width="26" height="18" rx="4" fill="url(#dfGradFrontSlide)" stroke="#E0F2FE" stroke-width="1.2"/>
  <rect x="15" y="25" width="4" height="5" rx="1" fill="#0F172A" opacity="0.85"/>
  <rect x="21" y="22" width="4" height="8" rx="1" fill="#0F172A" opacity="0.85"/>
  <rect x="27" y="19" width="4" height="11" rx="1" fill="#FFFFFF"/>
  <path d="M36 7L37.6 11.4L42 13L37.6 14.6L36 19L34.4 14.6L30 13L34.4 11.4L36 7Z" fill="url(#dfGradSpark)"/>
</svg>"""


def render_studio_html() -> str:
    """Returns the HTML5 single-page presentation studio for DeckForge."""
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>DeckForge — Executive Presentation &amp; Slide Deck Studio</title>
  <link rel="icon" type="image/svg+xml" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 48 48'%3E%3Crect width='48' height='48' rx='12' fill='%230F172A'/%3E%3Crect x='10' y='15' width='26' height='18' rx='4' fill='%2338BDF8'/%3E%3Cpath d='M36 7L38 12L43 14L38 16L36 21L34 16L29 14L34 12Z' fill='%23F59E0B'/%3E%3C/svg%3E" />
  <style>{STUDIO_CSS}</style>
</head>
<body>
  <header class="topbar">
    <div class="brand">
      {DECKFORGE_LOGO_SVG}
      <div>
        <div style="display:flex;align-items:center;gap:8px;">
          <span class="brand-badge">DECKFORGE</span>
          <strong style="font-size:15px;letter-spacing:-0.02em;">Executive Presentation Studio</strong>
        </div>
        <div style="font-size:11.5px;color:var(--muted);">Turn notes, spreadsheets &amp; numbers into boardroom-ready slides</div>
      </div>
    </div>
    <div class="view-switcher" role="tablist">
      <button class="view-btn active" id="viewBtnStage" onclick="setViewMode('stage')">Slide Stage (16:9)</button>
      <button class="view-btn" id="viewBtnFlow" onclick="setViewMode('flow')">Reading View (Cards)</button>
      <button class="view-btn" id="viewBtnSpatial" onclick="setViewMode('spatial')">Storyboard Grid (All Slides)</button>
    </div>
    <div style="display:flex;gap:12px;align-items:center;flex-wrap:wrap;">
      <nav style="display:flex;gap:12px;align-items:center;font-size:12px;margin-right:4px;">
        <a href="/about" style="color:var(--accent);text-decoration:none;font-weight:700;">About</a>
        <a href="/docs" style="color:var(--accent);text-decoration:none;font-weight:700;">Documentation</a>
        <a href="/analytics" style="color:var(--accent);text-decoration:none;font-weight:700;">Analytics</a>
        <a href="/privacy" style="color:var(--muted);text-decoration:none;font-weight:600;">Privacy Policy</a>
        <a href="/terms" style="color:var(--muted);text-decoration:none;font-weight:600;">Terms</a>
        <a id="headerUpgradeLink" href="/upgrade" target="_blank" rel="noopener" style="color:#34d399;text-decoration:none;font-weight:800;">Upgrade ($49.99) →</a>
      </nav>
      <details class="more-formats-menu" id="moreFormatsMenu">
        <summary class="btn-secondary" style="list-style:none;">More Formats ▾</summary>
        <div class="more-formats-popover">
          <button class="btn-secondary" id="btnExecBriefTop" onclick="openExecutiveBrief()">📄 1-Page Meeting Brief</button>
          <button class="btn-secondary" id="btnExportHtml" onclick="downloadStandaloneHtml()">⬇ Save Web Slides (.html)</button>
        </div>
      </details>
      <button class="btn-emerald" id="btnHeroDownloadPptx" style="padding:8px 16px;font-size:13px;box-shadow:0 4px 14px rgba(16,185,129,0.3);" onclick="downloadPptxFile()">⬇ Download PowerPoint (.pptx)</button>
    </div>
  </header>

  <section class="welcome-banner" id="welcomeGreetingBanner">
    <div class="welcome-main">
      <div>
        <div class="welcome-kicker">WELCOME TO DECKFORGE — ALL LAYOUTS, STYLES &amp; CHARTS INCLUDED FREE</div>
        <h1 class="welcome-title" id="welcomeHeadline">Welcome! Good to have you here — let's build a presentation you're proud to share.</h1>
        <p class="welcome-sub" id="welcomeMessage">
          Choose from 8 business templates, 8 slide layouts, 4 architectural design styles, and 4 interactive chart types — or import your own CSV/spreadsheet table in one click:
        </p>
      </div>
      <div class="welcome-actions">
        <button class="btn-primary" id="btnStartBlank" onclick="clearToBlankNotes()">✎ Start with My Own Notes</button>
        <button class="btn-secondary" onclick="dismissWelcomeBanner()">Got It, Hide Welcome</button>
      </div>
    </div>
    <div class="welcome-steps">
      <div class="welcome-step"><strong>1. Pick a starting point</strong><span>Choose 1 of 8 business templates, paste your notes, or import a spreadsheet/CSV table on the left.</span></div>
      <div class="welcome-step"><strong>2. Review &amp; tailor each slide</strong><span>Switch between 4 Visual Design Styles, 8 Slide Layouts, and 4 Chart Types (Column, Line, Horizontal, Stacked).</span></div>
      <div class="welcome-step"><strong>3. Present or download</strong><span>Present full-screen, download an editable PowerPoint (.pptx) file, or save a 1-page Meeting Brief.</span></div>
    </div>
  </section>

  <nav class="theme-bar" id="liveThemeBar">
    <span class="theme-bar-label">1-Click Color Palette:</span>
  </nav>

  <main class="studio-grid">
    <aside class="pane-left">
      <h2>1. Pick a Starter Template (8)</h2>
      <div id="quickPresetPills" class="quick-preset-pills" style="display:flex;gap:5px;flex-wrap:wrap;margin-bottom:6px;"></div>
      <select id="presetSelect" onchange="loadPreset(Number(this.value))">
        <option value="0">1. Series A Board Update [Board &amp; Investors]</option>
      </select>

      <details class="composer" id="memoComposerDetails" open>
        <summary>2. Quick Build from Your Notes</summary>
        <div style="display:flex;justify-content:space-between;align-items:center;margin-top:8px;">
          <label for="deckTitle" style="margin:0;">Presentation Title</label>
          <div style="display:flex;gap:4px;">
            <button class="btn-secondary" style="padding:2px 8px;font-size:10.5px;" onclick="pasteQuickSampleNotes()">Paste Sample Notes</button>
            <button class="btn-secondary" id="btnClearNotes" style="padding:2px 8px;font-size:10.5px;" onclick="clearToBlankNotes()">Clear</button>
          </div>
        </div>
        <input id="deckTitle" value="Series A Board of Directors Update — Q3 2026" placeholder="e.g., Q3 Business Review &amp; Q4 Priorities" />

        <div style="display:grid;grid-template-columns:1.4fr 0.8fr;gap:8px;">
          <div>
            <label for="orgName">Company or Team</label>
            <input id="orgName" value="Northstar Enterprise Corp" placeholder="e.g., Acme Corp" />
          </div>
          <div>
            <label for="targetSlideCountSelect">Slide Count</label>
            <select id="targetSlideCountSelect" onchange="updateLiveSlideEstimate()">
              <option value="5">5 Slides</option>
              <option value="6" selected>6 Slides</option>
              <option value="8">8 Slides</option>
            </select>
          </div>
        </div>

        <div style="display:flex;justify-content:space-between;align-items:center;margin-top:8px;margin-bottom:4px;">
          <label for="rawMemo" style="margin:0;">Paste Your Meeting Notes or Numbers</label>
          <span class="thumb-badge" id="liveSlideEstimateBadge">~6 slides · 4 metrics detected</span>
        </div>
        <textarea id="rawMemo" oninput="updateLiveSlideEstimate()" onkeydown="if((event.metaKey||event.ctrlKey)&&event.key==='Enter'){{event.preventDefault();runTransformMemo();}}" placeholder="Paste your bullet points, key metrics (like Revenue: $14.2M +35% YoY), quarterly numbers (Q1: $10M, Q2: $12M...), and next steps..."></textarea>
        <button class="btn-primary" style="width:100%;margin-top:8px;padding:9px 12px;font-size:13px;" onclick="runTransformMemo()">Build / Update My Slide Deck (⌘↵)</button>

        <details id="customizeThemeDrawer" style="margin-top:10px;border-top:1px solid var(--border);padding-top:8px;">
          <summary style="display:flex;justify-content:space-between;align-items:center;font-size:11.5px;color:var(--muted);">
            <span>Customize Theme, Colors &amp; Audience ▾</span>
            <span class="thumb-badge" id="activeThemeSummaryPill">Boardroom Navy · Classic</span>
          </summary>
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-top:6px;">
            <div>
              <label for="audienceSelect">Target Audience</label>
              <select id="audienceSelect">
                <option value="board">Board &amp; Investors</option>
                <option value="leadership">Executive Leadership</option>
                <option value="client">Client &amp; Sales Proposal</option>
                <option value="team">Team &amp; Operations</option>
              </select>
            </div>
            <div>
              <label for="themePreset">Color Palette (9)</label>
              <select id="themePreset" onchange="switchThemeLive(this.value)">
                <option value="boardroom_navy">Boardroom Navy</option>
                <option value="executive_indigo">Executive Indigo</option>
                <option value="modern_slate">Modern Slate</option>
                <option value="heritage_emerald">Heritage Emerald</option>
                <option value="royal_plum">Royal Plum</option>
                <option value="warm_terracotta">Warm Terracotta</option>
                <option value="pacific_atlas">Pacific Blue</option>
                <option value="sage_report">Sage &amp; Gold</option>
                <option value="warm_sandstone">Warm Sandstone</option>
              </select>
            </div>
          </div>
          <label for="styleFamilySelect">Architectural Design Style (4 Free Styles)</label>
          <select id="styleFamilySelect" onchange="switchDesignStyleLive(this.value)">
            <option value="classic_boardroom">Classic Boardroom (Solid Header &amp; Rounded Cards)</option>
            <option value="editorial_serif">Editorial Magazine (Serif Type &amp; Paper Rule Header)</option>
            <option value="modern_minimal">Modern Swiss Grid (Top Accent Bar &amp; Crisp Square Grid)</option>
            <option value="bold_keynote">Executive Keynote Dark (Dark Stage &amp; Elevated Cards)</option>
          </select>
          <label for="footerLabelInput">Slide Footer / Confidentiality Note</label>
          <input id="footerLabelInput" value="Confidential — Leadership Briefing" placeholder="e.g., Confidential — For Internal Discussion Only" />
        </details>
      </details>

      <details class="composer" id="dataImportDetails">
        <summary>3. Import Spreadsheet / CSV Data (Table or Chart)</summary>
        <p style="font-size:11.5px;color:var(--muted);margin-top:6px;">Upload a <code>.csv</code> / <code>.tsv</code> file or paste cells copied directly from Excel or Google Sheets.</p>
        <div style="display:flex;gap:6px;align-items:center;margin-top:8px;">
          <input type="file" id="csvFileInput" accept=".csv,.tsv,.txt" onchange="handleCsvFileUpload(this)" style="font-size:11px;padding:4px;" />
          <button class="btn-secondary" style="white-space:nowrap;padding:5px 8px;font-size:11px;" onclick="pasteSampleSheetData()">Sample Sheet</button>
        </div>
        <label for="importSlideTitle">Slide Headline for Imported Data</label>
        <input id="importSlideTitle" value="Quarterly Regional Revenue &amp; Plan Comparison" />
        <div style="display:grid;grid-template-columns:1.3fr 0.7fr;gap:6px;">
          <div>
            <label for="importChartType">If Importing as Chart</label>
            <select id="importChartType">
              <option value="vertical_bar">Vertical Column Chart</option>
              <option value="line_trend">Line &amp; Area Trend Chart</option>
              <option value="horizontal_bar">Horizontal Ranking Bars</option>
              <option value="stacked_bar">Stacked vs. Goal Columns</option>
            </select>
          </div>
          <div>
            <label for="importChartUnit">Unit</label>
            <input id="importChartUnit" value="$M" placeholder="$M, %, k" />
          </div>
        </div>
        <label for="rawTabularData">CSV / Spreadsheet Rows (Header + Data Rows)</label>
        <textarea id="rawTabularData" style="font-family:monospace;font-size:11.5px;min-height:82px;" placeholder="Quarter,Actual,Plan Target&#10;Q1 2026,14.2,13.0&#10;Q2 2026,17.8,16.5&#10;Q3 2026,22.4,20.0&#10;Q4 2026,27.5,25.0"></textarea>
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:6px;margin-top:8px;">
          <button class="btn-primary" id="btnImportAsChart" onclick="runDataImport('chart')">📊 Add as Chart Slide</button>
          <button class="btn-emerald" id="btnImportAsTable" onclick="runDataImport('table')">📋 Add as Table Slide</button>
        </div>
      </details>

      <div class="filmstrip-hdr">
        <h2 style="margin-bottom:0;">4. Slide Outline (<span id="filmstripCount">6</span>)</h2>
        <button class="btn-secondary" id="btnDuplicateSlide" style="padding:4px 8px;font-size:11px;" onclick="duplicateActiveSlide()">⧉ Copy Slide</button>
      </div>
      <div style="display:grid;grid-template-columns:1fr auto;gap:6px;margin-bottom:10px;">
        <select id="newSlideLayoutSelect" aria-label="Choose slide layout to add" style="font-size:11.5px;padding:5px 8px;">
          <option value="kpi_metrics_grid">Layout: 4-Card Key Numbers Grid</option>
          <option value="executive_summary">Layout: 3-Pillar Executive Summary</option>
          <option value="bar_chart_slide">Layout: Data Chart (Bar / Line / Stacked)</option>
          <option value="financial_table">Layout: Financial &amp; Data Table</option>
          <option value="two_column_comparison">Layout: Side-by-Side Comparison</option>
          <option value="executive_roadmap">Layout: 3-Phase Action Roadmap</option>
          <option value="quote_callout">Layout: Customer Quote &amp; ROI Spotlight</option>
          <option value="title_hero">Layout: Section Cover Slide</option>
        </select>
        <button class="btn-primary" id="btnAddSlide" style="padding:5px 10px;font-size:11.5px;white-space:nowrap;" onclick="addSlide()">+ Add Slide</button>
      </div>
      <div class="filmstrip" id="filmstripList"></div>
    </aside>

    <section class="pane-center">
      <div id="stageView">
        <div class="stage-toolbar">
          <div style="display:flex;gap:8px;align-items:center;">
            <button class="btn-secondary" onclick="stepSlide(-1)">← Previous</button>
            <strong id="slideCounterLabel" style="font-size:13px;">Slide 1 of 6</strong>
            <button class="btn-secondary" onclick="stepSlide(1)">Next →</button>
          </div>
          <div style="display:flex;gap:8px;align-items:center;">
            <span class="thumb-badge" id="activeLayoutBadge" style="font-size:11px;padding:4px 10px;">Cover Slide</span>
            <button class="btn-primary" id="btnPresentMode" onclick="togglePresentMode(true)">⛶ Present Fullscreen (F)</button>
          </div>
        </div>
        <div class="quick-layout-bar" id="quickLayoutChipBar" aria-label="1-Click Slide Layout Switcher"></div>
        <div id="stageCanvas">Loading slide preview...</div>
        <div class="bottom-slide-nav" id="bottomSlideNav">
          <button class="btn-secondary" onclick="stepSlide(-1)">← Prev Slide</button>
          <span id="bottomSlideProgressPill" class="thumb-badge" style="font-size:12px;padding:5px 12px;">Slide 1 of 6 · Use ← / → arrow keys</span>
          <button class="btn-secondary" onclick="stepSlide(1)">Next Slide →</button>
        </div>
        <div class="notes-box" style="display:flex;justify-content:space-between;align-items:center;gap:10px;">
          <div id="speakerNotesBox">Talking points for this slide will appear here.</div>
          <button class="btn-secondary" id="btnCopyTalkingPoints" style="padding:4px 10px;font-size:11px;white-space:nowrap;" onclick="copyActiveTalkingPoints()">📋 Copy Talking Points</button>
        </div>

        <div class="editor-panel" id="slideEditorPanel">
          <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px;margin-bottom:8px;">
            <h2 style="margin-bottom:0;color:var(--accent);">Edit This Slide (8 Layouts &amp; 4 Chart Types)</h2>
            <div style="display:flex;gap:8px;align-items:center;">
              <button class="btn-secondary" id="btnTightenBullets" onclick="tightenActiveSlideBullets()">✂ Tighten Bullets</button>
              <button class="btn-emerald" id="btnMagicPolish" onclick="polishActiveSlide()">✨ Tighten &amp; Polish Wording</button>
              <button class="btn-primary" id="btnApplySlideEdits" onclick="applySlideEdits()">Save Slide Changes</button>
            </div>
          </div>
          <div class="editor-grid">
            <div>
              <label for="editSlideLayout">Slide Layout Style (8 Layouts)</label>
              <select id="editSlideLayout" onchange="onLayoutDropdownChange()">
                <option value="title_hero">Title &amp; Headline Cover</option>
                <option value="executive_summary">3-Pillar Executive Summary</option>
                <option value="kpi_metrics_grid">4-Card Key Numbers Grid</option>
                <option value="bar_chart_slide">Data Chart (Columns, Line, Horizontal, Stacked)</option>
                <option value="two_column_comparison">Side-by-Side Comparison</option>
                <option value="financial_table">Financial &amp; Performance Table</option>
                <option value="executive_roadmap">3-Phase Action Roadmap</option>
                <option value="quote_callout">Customer Quote &amp; Impact Spotlight</option>
              </select>
              <label for="editTakeaway">Bottom Takeaway Line</label>
              <input id="editTakeaway" onchange="applySlideEdits()" placeholder="One clear sentence summarizing the bottom line..." />
            </div>
            <div>
              <label for="editActionTitle">Slide Headline (Main Conclusion)</label>
              <input id="editActionTitle" onchange="applySlideEdits()" placeholder="State the main takeaway and key number..." />
              <label for="editSubtitle">Supporting Subtitle</label>
              <input id="editSubtitle" onchange="applySlideEdits()" />
              <label for="editSpeakerNotes">Speaker Talking Points (What to Say in the Room)</label>
              <textarea id="editSpeakerNotes" onchange="applySlideEdits()"></textarea>
            </div>
          </div>
          <div style="margin-top:10px;padding-top:10px;border-top:1px solid var(--border);">
            <label style="margin-top:0;color:var(--accent);">Slide Numbers, Chart Settings, Bullets &amp; Table Values</label>
            <div id="structuredBodyFields" style="margin-bottom:6px;"></div>
            <details style="margin-top:4px;">
              <summary style="cursor:pointer;font-size:11px;font-weight:700;color:var(--muted);">Advanced: Edit Raw Slide Data</summary>
              <textarea id="editBodyDataJson" style="font-family:monospace;font-size:11.5px;min-height:84px;margin-top:6px;"></textarea>
            </details>
          </div>
        </div>
      </div>

      <div id="flowView" style="display:none;"><div class="reading-flow" id="readingFlowContainer"></div></div>
      <div id="spatialView" style="display:none;"><div class="storyboard-board" id="storyboardContainer"></div></div>
    </section>

    <aside class="pane-right">
      <h2>Presentation Readiness &amp; Handouts</h2>
      <div class="inspector-card">
        <p style="color:var(--muted);margin-bottom:8px;">Check whether your slides are concise and ready for the room, or generate a 1-page summary to email before the meeting.</p>
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:6px;">
          <button class="btn-primary" id="btnAuditDeck" onclick="runDeckQualityCheck()">✓ Check Deck Readiness</button>
          <button class="btn-secondary" id="btnExecBrief" onclick="openExecutiveBrief()">📄 1-Page Brief</button>
        </div>
        <div id="readinessReportBox" style="margin-top:10px;display:none;"></div>
      </div>

      <h2>Company Brand Colors &amp; Style</h2>
      <div class="inspector-card">
        <div class="color-grid">
          <div><label for="customPrimaryHex" style="margin-top:0;">Header</label><input type="color" id="customPrimaryHex" value="#0B1F3A" onchange="applyCustomBrandColors()" /></div>
          <div><label for="customSecondaryHex" style="margin-top:0;">Primary</label><input type="color" id="customSecondaryHex" value="#1D4ED8" onchange="applyCustomBrandColors()" /></div>
          <div><label for="customAccentHex" style="margin-top:0;">Highlight</label><input type="color" id="customAccentHex" value="#0284C7" onchange="applyCustomBrandColors()" /></div>
          <div><label for="customBgHex" style="margin-top:0;">Background</label><input type="color" id="customBgHex" value="#F8FAFC" onchange="applyCustomBrandColors()" /></div>
        </div>
        <button class="btn-secondary" style="width:100%;margin-top:8px;" onclick="applyCustomBrandColors()">Apply My Company Colors</button>
      </div>

      <h2>Your Account &amp; Monthly Plan</h2>
      <div class="inspector-card">
        <label for="apiKeySelect" style="margin-top:0;">Active Membership Plan</label>
        <select id="apiKeySelect" onchange="refreshQuota()">
          <option value="df_free_demo">Starter Plan — 3 Free Decks / Month (All Layouts &amp; Styles Unlocked)</option>
          <option value="df_pro_enterprise">Unlimited Pro Plan ($49.99) — Unlimited Decks</option>
        </select>
        <div id="quotaBox" style="margin-top:8px;color:#cbd5e1;">Loading plan details...</div>
        <a id="cardUpgradeLink" class="btn-primary" href="/upgrade" target="_blank" rel="noopener" style="display:block;text-align:center;text-decoration:none;margin-top:8px;">Upgrade to Unlimited Pro ($49.99) →</a>
      </div>

      <h2>Resources &amp; Support</h2>
      <div class="inspector-card" data-local-mcp="http://localhost:8793/mcp">
        <p style="color:var(--muted);margin-bottom:8px;">Read the user guide, privacy policy, or reach out for support.</p>
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:6px;">
          <a href="/docs" class="btn-secondary" style="text-align:center;text-decoration:none;display:block;">Documentation</a>
          <a href="/about" class="btn-secondary" style="text-align:center;text-decoration:none;display:block;">About DeckForge</a>
          <a href="/privacy" class="btn-secondary" style="text-align:center;text-decoration:none;display:block;">Privacy Policy</a>
          <a href="/terms" class="btn-secondary" style="text-align:center;text-decoration:none;display:block;">Terms of Service</a>
        </div>
        <span id="opsCounter" style="display:none;">0</span>
        <button id="btnRunPkce" style="display:none;" onclick="runLivePkceHandshake()">Verify Connection</button>
        <pre id="jsonInspector" style="display:none;"></pre>
      </div>
    </aside>
  </main>

  <div id="presentOverlay" class="present-overlay" style="display:none;">
    <div class="present-topbar">
      <div style="display:flex;gap:12px;align-items:center;">
        <span class="brand-badge">PRESENTATION MODE</span>
        <strong id="presentCounterLabel">Slide 1 of 6</strong>
      </div>
      <div style="display:flex;gap:8px;align-items:center;">
        <button class="btn-secondary" onclick="stepSlide(-1)">← Previous</button>
        <button class="btn-secondary" onclick="stepSlide(1)">Next →</button>
        <button class="btn-secondary" id="btnToggleTeleprompter" onclick="toggleTeleprompter()">Show / Hide Speaker Notes</button>
        <button class="btn-emerald" onclick="togglePresentMode(false)">Exit Fullscreen (Esc)</button>
      </div>
    </div>
    <div id="presentSvgStage" class="present-stage"></div>
    <div id="presentNotesBox" class="present-notes"></div>
  </div>

  <script>{STUDIO_JS}</script>
</body>
</html>"""
