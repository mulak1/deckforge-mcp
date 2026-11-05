"""
Modular CSS and JavaScript assets for the DeckForge Executive Presentation Studio.
Separated from src/studio_ui.py to enforce /anthro-skill <400-line file modularity.
"""

from __future__ import annotations

from src.studio_client_ext import STUDIO_EXT_JS

STUDIO_CSS = """
    :root { --bg:#070b14; --panel:#0f172a; --panel-alt:#1e293b; --border:#334155; --text:#f8fafc; --muted:#94a3b8; --accent:#38bdf8; --indigo:#6366f1; --emerald:#10b981; }
    * { box-sizing:border-box; margin:0; padding:0; }
    body { font-family:Inter,-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif; background:var(--bg); color:var(--text); min-height:100vh; line-height:1.45; display:flex; flex-direction:column; }
    .topbar { display:flex; flex-wrap:wrap; justify-content:space-between; align-items:center; gap:12px; padding:12px 20px; border-bottom:1px solid var(--border); background:rgba(15,23,42,0.95); backdrop-filter:blur(12px); position:sticky; top:0; z-index:50; }
    .brand { display:flex; align-items:center; gap:12px; }
    .brand-badge { background:linear-gradient(135deg,var(--accent),var(--indigo)); color:#020617; font-weight:900; padding:4px 9px; border-radius:6px; font-size:11px; letter-spacing:0.05em; }
    .welcome-banner { background:linear-gradient(90deg,rgba(30,27,75,0.88),rgba(15,23,42,0.95)); border-bottom:1px solid var(--border); padding:14px 22px; }
    .welcome-main { display:flex; justify-content:space-between; align-items:flex-start; gap:16px; flex-wrap:wrap; }
    .welcome-kicker { font-size:11px; font-weight:800; color:var(--accent); letter-spacing:0.08em; text-transform:uppercase; }
    .welcome-title { font-size:17px; font-weight:800; color:#ffffff; margin:2px 0 4px; }
    .welcome-sub { font-size:13px; color:#cbd5e1; max-width:880px; }
    .welcome-actions { display:flex; gap:8px; align-items:center; flex-shrink:0; }
    .welcome-steps { display:grid; grid-template-columns:repeat(3,1fr); gap:12px; margin-top:10px; }
    .welcome-step { background:rgba(2,6,23,0.65); border:1px solid var(--border); border-radius:8px; padding:8px 12px; font-size:12px; display:flex; flex-direction:column; gap:2px; }
    .welcome-step strong { color:var(--accent); font-size:12px; }
    .welcome-step span { color:#cbd5e1; }
    .view-switcher { display:flex; gap:4px; background:#020617; padding:4px; border-radius:10px; border:1px solid var(--border); }
    .view-btn { background:transparent; color:var(--muted); border:none; padding:6px 12px; border-radius:7px; font-size:12px; font-weight:700; cursor:pointer; }
    .view-btn.active { background:var(--indigo); color:#ffffff; }
    .more-formats-menu { position:relative; }
    .more-formats-menu summary::-webkit-details-marker { display:none; }
    .more-formats-popover { position:absolute; right:0; top:calc(100% + 6px); background:var(--panel); border:1px solid var(--border); border-radius:10px; padding:8px; display:flex; flex-direction:column; gap:6px; min-width:210px; z-index:80; box-shadow:0 10px 25px rgba(0,0,0,0.5); }
    .preset-chip { background:#020617; color:#cbd5e1; border:1px solid var(--border); padding:3px 8px; border-radius:999px; font-size:10.5px; font-weight:700; cursor:pointer; }
    .preset-chip.active { border-color:var(--accent); color:var(--accent); background:#1e293b; }
    .quick-layout-bar { display:flex; gap:6px; align-items:center; flex-wrap:wrap; max-width:960px; margin:0 auto 10px; padding:6px 10px; background:rgba(15,23,42,0.75); border:1px solid var(--border); border-radius:9px; }
    .layout-chip { background:#020617; color:var(--muted); border:1px solid var(--border); padding:4px 10px; border-radius:999px; font-size:11px; font-weight:700; cursor:pointer; }
    .layout-chip.active { background:var(--accent); color:#020617; border-color:var(--accent); font-weight:800; }
    .bottom-slide-nav { display:flex; justify-content:space-between; align-items:center; max-width:960px; margin:10px auto 0; padding:8px 14px; background:rgba(15,23,42,0.85); border:1px solid var(--border); border-radius:10px; }
    .theme-bar { display:flex; gap:6px; align-items:center; flex-wrap:wrap; padding:8px 20px; background:#090f1d; border-bottom:1px solid var(--border); }
    .theme-bar-label { font-size:11px; font-weight:800; color:var(--muted); text-transform:uppercase; margin-right:4px; }
    .theme-pill { display:inline-flex; align-items:center; gap:6px; padding:4px 10px; border-radius:999px; font-size:11.5px; font-weight:700; cursor:pointer; background:var(--panel); color:var(--text); border:1px solid var(--border); }
    .theme-pill.active { border-color:var(--accent); background:#1e293b; color:var(--accent); }
    .swatch { width:10px; height:10px; border-radius:50%; display:inline-block; }
    .studio-grid { display:grid; grid-template-columns:350px 1fr 340px; flex:1; min-height:calc(100vh - 180px); }
    .pane-left { border-right:1px solid var(--border); background:var(--panel); padding:14px; overflow-y:auto; }
    .pane-center { background:radial-gradient(circle at top,#172036 0%,#070b14 70%); padding:20px; overflow-y:auto; }
    .pane-right { border-left:1px solid var(--border); background:var(--panel); padding:14px; overflow-y:auto; }
    h2 { font-size:12px; font-weight:800; text-transform:uppercase; letter-spacing:0.05em; color:var(--muted); margin-bottom:8px; }
    label { display:block; font-size:11px; font-weight:700; color:var(--muted); margin:8px 0 4px; text-transform:uppercase; }
    input,select,textarea { width:100%; background:#020617; border:1px solid var(--border); color:var(--text); border-radius:7px; padding:7px 10px; font-size:12.5px; font-family:inherit; }
    input[type="color"] { height:34px; padding:2px 4px; cursor:pointer; }
    input[type="checkbox"] { width:auto; accent-color:var(--accent); cursor:pointer; }
    textarea { min-height:74px; resize:vertical; }
    button { cursor:pointer; border:none; border-radius:8px; padding:7px 12px; font-weight:700; font-size:12px; transition:all 0.14s ease; }
    .btn-primary { background:linear-gradient(135deg,var(--accent),var(--indigo)); color:#020617; }
    .btn-secondary { background:var(--panel-alt); color:var(--text); border:1px solid var(--border); }
    .btn-emerald { background:var(--emerald); color:#020617; font-weight:800; }
    details.composer { background:#020617; border:1px solid var(--border); border-radius:10px; padding:10px; margin:12px 0; }
    details.composer summary { cursor:pointer; font-size:12px; font-weight:800; color:var(--accent); }
    .filmstrip-hdr { display:flex; justify-content:space-between; align-items:center; gap:6px; margin-top:12px; margin-bottom:8px; }
    .filmstrip { display:flex; flex-direction:column; gap:10px; }
    .thumb-card { background:#020617; border:1.5px solid var(--border); border-radius:10px; padding:8px; cursor:pointer; }
    .thumb-card.active { border-color:var(--accent); box-shadow:0 0 0 2px rgba(56,189,248,0.2); }
    .thumb-meta { display:flex; justify-content:space-between; align-items:center; font-size:11px; margin-bottom:5px; gap:4px; }
    .thumb-badge { background:var(--panel-alt); color:var(--accent); padding:2px 6px; border-radius:4px; font-size:10px; font-weight:800; }
    .thumb-actions { display:inline-flex; gap:3px; }
    .thumb-act { background:#1e293b; color:#cbd5e1; border:1px solid var(--border); padding:1px 6px; border-radius:4px; font-size:10.5px; font-weight:800; }
    .thumb-act:hover { background:var(--accent); color:#020617; }
    .thumb-del:hover { background:#ef4444; color:#ffffff; border-color:#ef4444; }
    .thumb-title { font-size:11.5px; font-weight:700; color:#e2e8f0; margin-top:5px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
    .stage-toolbar { display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:8px; margin-bottom:14px; background:rgba(15,23,42,0.85); border:1px solid var(--border); padding:10px 14px; border-radius:10px; max-width:960px; margin-left:auto; margin-right:auto; }
    #stageCanvas { max-width:960px; margin:0 auto; }
    .notes-box { max-width:960px; margin:12px auto 0; padding:12px 16px; background:#020617; border-left:4px solid var(--accent); border-radius:8px; font-size:13px; color:#cbd5e1; }
    .editor-panel { max-width:960px; margin:14px auto 0; padding:14px 16px; background:rgba(15,23,42,0.92); border:1px solid var(--border); border-radius:12px; }
    .editor-grid { display:grid; grid-template-columns:240px 1fr; gap:10px; align-items:start; }
    .reading-flow { max-width:860px; margin:0 auto; display:flex; flex-direction:column; gap:24px; }
    .reading-card { background:rgba(15,23,42,0.92); border:1px solid var(--border); border-radius:14px; padding:18px; }
    .reading-card-hdr { display:flex; justify-content:space-between; align-items:center; margin-bottom:10px; }
    .storyboard-board { display:grid; grid-template-columns:repeat(auto-fit,minmax(360px,1fr)); gap:18px; background-image:radial-gradient(#334155 1px,transparent 1px); background-size:18px 18px; padding:16px; border-radius:12px; border:1px dashed var(--border); }
    .storyboard-frame { background:#0b1324; border:1.5px solid var(--border); border-radius:10px; padding:10px; cursor:pointer; }
    .storyboard-frame:hover { border-color:var(--accent); }
    .storyboard-frame-hdr { display:flex; justify-content:space-between; font-size:10.5px; font-weight:800; color:var(--accent); margin-bottom:6px; }
    .inspector-card { background:#020617; border:1px solid var(--border); border-radius:10px; padding:12px; margin-bottom:12px; font-size:12px; }
    .color-grid { display:grid; grid-template-columns:repeat(4,1fr); gap:6px; margin-top:6px; }
    pre { background:#020617; border:1px solid var(--border); border-radius:8px; padding:10px; font-size:11px; color:#38bdf8; max-height:280px; overflow:auto; margin-top:8px; white-space:pre-wrap; }
    .present-overlay { position:fixed; inset:0; background:rgba(2,6,23,0.97); z-index:200; display:flex; flex-direction:column; justify-content:space-between; padding:18px 28px; }
    .present-topbar { display:flex; justify-content:space-between; align-items:center; border-bottom:1px solid var(--border); padding-bottom:12px; }
    .present-stage { flex:1; display:flex; align-items:center; justify-content:center; max-width:1280px; width:100%; margin:0 auto; padding:12px 0; }
    .present-stage svg { max-height:78vh; width:auto; max-width:100%; }
    .present-notes { max-width:1100px; width:100%; margin:0 auto; padding:10px 16px; background:#0f172a; border-left:4px solid var(--accent); border-radius:8px; font-size:14px; color:#e2e8f0; }
    @media (max-width:1180px) { .studio-grid, .editor-grid, .welcome-steps { grid-template-columns:1fr; } }
"""

STUDIO_JS = """
    let PRESETS = [], THEMES = {}, DESIGN_STYLES = {}, CURRENT_DECK = null, CURRENT_SVGS = [];
    let ACTIVE_SLIDE_IDX = 0, ACTIVE_VIEW_MODE = 'stage', ACTIVE_THEME_KEY = 'boardroom_navy', ACTIVE_PRESET_IDX = 0;
    let PRESENT_ACTIVE = false, TELEPROMPTER_VISIBLE = true;
    const LAYOUT_LABELS = {
      title_hero: 'Cover Slide', executive_summary: '3-Pillar Summary', kpi_metrics_grid: 'Key Numbers Grid',
      bar_chart_slide: 'Data Chart', two_column_comparison: 'Side-by-Side Comparison',
      financial_table: 'Financial & Data Table', executive_roadmap: '90-Day Roadmap', quote_callout: 'Customer Quote & ROI'
    };
    const LAYOUT_DEFAULT_HEADLINES = {
      title_hero: ['Executive Briefing & Strategic Overview', 'Key priorities, operating metrics, and 90-day execution plan'],
      executive_summary: ['Executive Summary: Three Takeaways Driving Quarterly Momentum', 'Structured synthesis across growth, efficiency, and execution'],
      kpi_metrics_grid: ['Key Operating Highlights & Performance Scorecard', 'Measurable progress across revenue growth, retention, and payback'],
      bar_chart_slide: ['Quarterly Performance Trajectory vs. Plan Goal', 'Period-over-period trend comparing actual results against target'],
      two_column_comparison: ['Side-by-Side Comparison: Core Drivers vs. Next-Quarter Focus', 'Comparing high-velocity growth channels and enterprise expansion'],
      financial_table: ['Financial & Operating Summary Table', 'Period-over-period metrics, margin expansion, and cash generation'],
      executive_roadmap: ['90-Day Action Plan & Key Team Milestones', 'Sequenced deliverables with clear team ownership and target dates'],
      quote_callout: ['Verified Customer & Leadership Impact Spotlight', 'Direct stakeholder feedback paired with quantified ROI outcomes']
    };
    async function initStudio() {
      const data = await (await fetch('/api/presets')).json();
      PRESETS = data.presets || []; THEMES = data.themes || {}; DESIGN_STYLES = data.design_styles || {};
      document.getElementById('presetSelect').innerHTML = PRESETS.map((p, i) => `<option value="${i}">${i + 1}. ${p.label} [${p.badge}]</option>`).join('');
      renderThemePills();
      if (PRESETS.length > 0) await loadPreset(0);
      await refreshQuota();
      window.addEventListener('keydown', handleGlobalKeydown);
    }
    function dismissWelcomeBanner() { const el = document.getElementById('welcomeGreetingBanner'); if (el) el.style.display = 'none'; }
    function clearToBlankNotes() {
      ['deckTitle', 'orgName', 'rawMemo'].forEach(id => { document.getElementById(id).value = ''; });
      ACTIVE_PRESET_IDX = -1; if (typeof renderQuickPresetPills === 'function') renderQuickPresetPills();
      if (typeof updateLiveSlideEstimate === 'function') updateLiveSlideEstimate();
      const details = document.getElementById('memoComposerDetails'); if (details) details.open = true;
      document.getElementById('deckTitle').focus();
    }
    function pasteQuickSampleNotes() {
      document.getElementById('deckTitle').value = 'Quarterly Leadership Operating Update';
      document.getElementById('orgName').value = 'Apex Commercial Partners';
      document.getElementById('rawMemo').value = 'Annual Revenue reached $24.6M (+38% YoY), Net Customer Retention hit 122% (+400 bps), Gross Margin expanded to 79.5% (+250 bps), Customer Payback dropped to 8.4 mos. Q1: $16.2M, Q2: $18.9M, Q3: $21.5M, Q4: $24.6M.\\n- Self-serve customer referrals drove 62% of new team sign-ups this quarter.\\n- Standardized customer onboarding cut setup time from 14 days to 3 days.';
      ACTIVE_PRESET_IDX = -1; if (typeof renderQuickPresetPills === 'function') renderQuickPresetPills();
      if (typeof updateLiveSlideEstimate === 'function') updateLiveSlideEstimate();
    }
    function handleGlobalKeydown(e) {
      const tag = (e.target && e.target.tagName) || '';
      if (['INPUT', 'TEXTAREA', 'SELECT'].includes(tag) || (e.target && e.target.isContentEditable)) return;
      if (e.key === 'ArrowRight') { e.preventDefault(); stepSlide(1); }
      else if (e.key === 'ArrowLeft') { e.preventDefault(); stepSlide(-1); }
      else if (e.key === 'Escape' && PRESENT_ACTIVE) { e.preventDefault(); togglePresentMode(false); }
      else if ((e.key === 'f' || e.key === 'F') && !e.metaKey && !e.ctrlKey && !e.altKey) { e.preventDefault(); togglePresentMode(!PRESENT_ACTIVE); }
    }
    function syncColorPickers(theme) {
      if (!theme) return;
      document.getElementById('customPrimaryHex').value = theme.primary_hex || '#0B1F3A';
      document.getElementById('customSecondaryHex').value = theme.secondary_hex || '#1D4ED8';
      document.getElementById('customAccentHex').value = theme.accent_hex || '#0284C7';
      document.getElementById('customBgHex').value = theme.background_hex || '#F8FAFC';
      const styleEl = document.getElementById('styleFamilySelect');
      if (styleEl && theme.style_family) styleEl.value = theme.style_family;
      if (typeof updateThemeSummaryPill === 'function') updateThemeSummaryPill();
    }
    function renderThemePills() {
      const curStyle = (CURRENT_DECK && CURRENT_DECK.theme && CURRENT_DECK.theme.style_family) || 'classic_boardroom';
      const stylePills = Object.entries(DESIGN_STYLES).map(([sk, sv]) =>
        `<button class="theme-pill ${sk === curStyle ? 'active' : ''}" onclick="switchDesignStyleLive('${sk}')">✦ ${sv.label}</button>`
      ).join('');
      document.getElementById('liveThemeBar').innerHTML =
        '<span class="theme-bar-label">Palette:</span>' +
        Object.entries(THEMES).map(([k, t]) =>
          `<button class="theme-pill ${k === ACTIVE_THEME_KEY ? 'active' : ''}" onclick="switchThemeLive('${k}')">` +
          `<span class="swatch" style="background:${t.secondary_hex};border:1px solid ${t.accent_hex};"></span>${t.name}</button>`
        ).join('') +
        '<span class="theme-bar-label" style="margin-left:10px;">Visual Style:</span>' + stylePills;
      if (typeof updateThemeSummaryPill === 'function') updateThemeSummaryPill();
    }
    async function switchThemeLive(themeKey) {
      if (!THEMES[themeKey] || !CURRENT_DECK) return;
      ACTIVE_THEME_KEY = themeKey; document.getElementById('themePreset').value = themeKey;
      CURRENT_DECK = { ...CURRENT_DECK, theme: THEMES[themeKey] };
      syncColorPickers(CURRENT_DECK.theme); renderThemePills();
      await renderDeckPreview(CURRENT_DECK, false);
    }
    async function switchDesignStyleLive(styleKey) {
      if (!CURRENT_DECK) return;
      const preset = DESIGN_STYLES[styleKey] || { font_family: 'Inter, sans-serif', card_radius: 10 };
      const isDarkKeynote = styleKey === 'bold_keynote';
      const updatedTheme = {
        ...CURRENT_DECK.theme, style_family: styleKey, font_family: preset.font_family, card_radius: preset.card_radius,
        background_hex: isDarkKeynote ? '#0F172A' : (CURRENT_DECK.theme.background_hex === '#0F172A' ? '#F8FAFC' : CURRENT_DECK.theme.background_hex),
      };
      CURRENT_DECK = { ...CURRENT_DECK, theme: updatedTheme };
      syncColorPickers(CURRENT_DECK.theme); renderThemePills();
      await renderDeckPreview(CURRENT_DECK, false);
    }
    async function applyCustomBrandColors() {
      if (!CURRENT_DECK) return;
      const bgHex = document.getElementById('customBgHex').value.toUpperCase();
      const r = parseInt(bgHex.slice(1, 3), 16) / 255, g = parseInt(bgHex.slice(3, 5), 16) / 255, b = parseInt(bgHex.slice(5, 7), 16) / 255;
      const isDarkBg = (0.2126 * r + 0.7152 * g + 0.0722 * b) < 0.45;
      const customTheme = {
        ...CURRENT_DECK.theme, name: 'Custom Company Palette',
        primary_hex: document.getElementById('customPrimaryHex').value.toUpperCase(),
        secondary_hex: document.getElementById('customSecondaryHex').value.toUpperCase(),
        accent_hex: document.getElementById('customAccentHex').value.toUpperCase(),
        background_hex: bgHex, text_hex: isDarkBg ? '#F8FAFC' : '#0F172A', muted_hex: isDarkBg ? '#CBD5E1' : '#475569',
      };
      CURRENT_DECK = { ...CURRENT_DECK, theme: customTheme };
      await renderDeckPreview(CURRENT_DECK, false);
      document.getElementById('jsonInspector').textContent = JSON.stringify({ custom_theme_applied: customTheme }, null, 2);
    }
    async function loadPreset(idx) {
      const p = PRESETS[idx]; if (!p) return;
      ACTIVE_PRESET_IDX = idx; ACTIVE_THEME_KEY = p.theme_preset;
      document.getElementById('presetSelect').value = String(idx);
      document.getElementById('deckTitle').value = p.deck_spec.title;
      document.getElementById('orgName').value = p.deck_spec.organization;
      document.getElementById('themePreset').value = p.theme_preset;
      if (document.getElementById('audienceSelect') && p.audience) document.getElementById('audienceSelect').value = p.audience;
      if (document.getElementById('footerLabelInput') && p.deck_spec.footer_label) document.getElementById('footerLabelInput').value = p.deck_spec.footer_label;
      document.getElementById('rawMemo').value = p.raw_memo;
      CURRENT_DECK = JSON.parse(JSON.stringify(p.deck_spec));
      syncColorPickers(CURRENT_DECK.theme); renderThemePills();
      if (typeof renderQuickPresetPills === 'function') renderQuickPresetPills();
      if (typeof updateLiveSlideEstimate === 'function') updateLiveSlideEstimate();
      await renderDeckPreview(CURRENT_DECK, true);
    }
    async function runTransformMemo() {
      const rawMemoVal = document.getElementById('rawMemo').value.trim();
      if (rawMemoVal.length < 20) {
        alert('Please enter at least a sentence or two of notes or numbers so we can build your slides.');
        return;
      }
      const countEl = document.getElementById('targetSlideCountSelect');
      const payload = {
        raw_memo: rawMemoVal,
        deck_title: document.getElementById('deckTitle').value.trim() || 'Executive Presentation Update',
        organization: document.getElementById('orgName').value.trim() || 'Leadership Team',
        theme_preset: document.getElementById('themePreset').value,
        audience: document.getElementById('audienceSelect') ? document.getElementById('audienceSelect').value : 'board',
        footer_label: document.getElementById('footerLabelInput') ? document.getElementById('footerLabelInput').value : 'Confidential — Leadership Briefing',
        target_slide_count: countEl ? Number(countEl.value) : 6
      };
      ACTIVE_THEME_KEY = payload.theme_preset; renderThemePills();
      const data = await (await fetch('/api/tools/transform-memo', {
        method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(payload)
      })).json();
      if (data.deck_spec) {
        CURRENT_DECK = data.deck_spec; syncColorPickers(CURRENT_DECK.theme);
        await renderDeckPreview(CURRENT_DECK, true);
        document.getElementById('jsonInspector').textContent = JSON.stringify(data, null, 2);
      }
    }
    async function renderDeckPreview(deckSpec, resetSlideIdx) {
      const data = await (await fetch('/api/tools/google-slides', {
        method: 'POST', headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({deck_spec: deckSpec, presentation_id: '1DeckForgeStudioPreview'})
      })).json();
      CURRENT_SVGS = data.slide_svg_cards || [];
      document.getElementById('opsCounter').textContent = data.operations_count || 0;
      document.getElementById('filmstripCount').textContent = CURRENT_SVGS.length;
      if (resetSlideIdx) ACTIVE_SLIDE_IDX = 0;
      ACTIVE_SLIDE_IDX = Math.max(0, Math.min(ACTIVE_SLIDE_IDX, Math.max(CURRENT_SVGS.length - 1, 0)));
      renderFilmstrip(); renderAllViews();
    }
    function renderFilmstrip() {
      document.getElementById('filmstripList').innerHTML = CURRENT_SVGS.map((c, idx) =>
        `<div class="thumb-card ${idx === ACTIVE_SLIDE_IDX ? 'active' : ''}" onclick="selectSlide(${idx})">` +
        `<div class="thumb-meta"><strong>Slide ${c.slide_number}</strong><span class="thumb-badge">${LAYOUT_LABELS[c.layout_type] || c.layout_type}</span>` +
        `<span class="thumb-actions"><button class="thumb-act" title="Move Slide Up" onclick="moveSlide(${idx},-1,event)">↑</button>` +
        `<button class="thumb-act" title="Move Slide Down" onclick="moveSlide(${idx},1,event)">↓</button>` +
        `<button class="thumb-act thumb-del" title="Remove Slide" onclick="deleteSlide(${idx},event)">×</button></span></div>` +
        `<div style="pointer-events:none;">${c.svg}</div><div class="thumb-title">${c.action_title}</div></div>`
      ).join('');
    }
    function selectSlide(idx) {
      if (!CURRENT_SVGS.length) return;
      ACTIVE_SLIDE_IDX = Math.max(0, Math.min(idx, CURRENT_SVGS.length - 1));
      renderFilmstrip(); renderStageSlide();
    }
    function stepSlide(delta) { selectSlide(ACTIVE_SLIDE_IDX + delta); }
    function setViewMode(mode) {
      ACTIVE_VIEW_MODE = mode;
      ['stage', 'flow', 'spatial'].forEach(m => {
        const cap = m.charAt(0).toUpperCase() + m.slice(1);
        document.getElementById('viewBtn' + cap).classList.toggle('active', mode === m);
        document.getElementById(m + 'View').style.display = mode === m ? 'block' : 'none';
      });
    }
    function renderStageSlide() {
      const card = CURRENT_SVGS[ACTIVE_SLIDE_IDX]; if (!card) return;
      const friendlyLayout = LAYOUT_LABELS[card.layout_type] || card.layout_type;
      document.getElementById('slideCounterLabel').textContent = `Slide ${card.slide_number} of ${CURRENT_SVGS.length}`;
      const btmPill = document.getElementById('bottomSlideProgressPill');
      if (btmPill) btmPill.textContent = `Slide ${card.slide_number} of ${CURRENT_SVGS.length} · ${friendlyLayout} (Use ← / → keys)`;
      document.getElementById('activeLayoutBadge').textContent = friendlyLayout;
      document.getElementById('stageCanvas').innerHTML = card.svg;
      const slideObj = (CURRENT_DECK && CURRENT_DECK.slides && CURRENT_DECK.slides[ACTIVE_SLIDE_IDX]) || {};
      const activeLayout = slideObj.layout_type || card.layout_type;
      if (typeof renderQuickLayoutChips === 'function') renderQuickLayoutChips(activeLayout);
      const notesText = slideObj.speaker_notes || 'No talking points added for this slide yet.';
      document.getElementById('speakerNotesBox').innerHTML = `<strong>Talking Points (Slide ${card.slide_number} · ${friendlyLayout}):</strong> ` + notesText;
      document.getElementById('editSlideLayout').value = activeLayout;
      document.getElementById('editActionTitle').value = slideObj.action_title || card.action_title || '';
      document.getElementById('editSubtitle').value = slideObj.subtitle || '';
      document.getElementById('editTakeaway').value = slideObj.takeaway_banner || '';
      document.getElementById('editSpeakerNotes').value = slideObj.speaker_notes || '';
      if (typeof syncStructuredBodyEditor === 'function') syncStructuredBodyEditor(slideObj);
      if (PRESENT_ACTIVE) {
        document.getElementById('presentCounterLabel').textContent = `Slide ${card.slide_number} of ${CURRENT_SVGS.length} — ${friendlyLayout}`;
        document.getElementById('presentSvgStage').innerHTML = card.svg;
        document.getElementById('presentNotesBox').innerHTML = `<strong>Speaker Notes:</strong> ${notesText}`;
      }
    }
    function ensureLayoutDefaults(slide) {
      const donor = (type) => (CURRENT_DECK.slides || []).find(s => s.layout_type === type) || {};
      const next = { ...slide };
      if (next.layout_type === 'kpi_metrics_grid' && (!next.kpis || !next.kpis.length)) {
        next.kpis = donor('kpi_metrics_grid').kpis || [
          { label: 'Annual Recurring Revenue', value: '$18.4M', delta: '+142% YoY', sentiment: 'positive' },
          { label: 'Net Customer Retention', value: '124%', delta: '+900 bps YoY', sentiment: 'positive' },
          { label: 'Gross Margin', value: '81.2%', delta: '+420 bps QoQ', sentiment: 'positive' },
          { label: 'Customer Payback Period', value: '9.5 mos', delta: '-3.2 mos YoY', sentiment: 'positive' }
        ];
      }
      if (next.layout_type === 'bar_chart_slide' && (!next.chart_series || !next.chart_series.length)) {
        next.chart_series = donor('bar_chart_slide').chart_series || [
          { category: 'Q1 Actual', value: 11.2, target: 10.5 }, { category: 'Q2 Actual', value: 14.5, target: 13.2 },
          { category: 'Q3 Actual', value: 18.4, target: 16.8 }, { category: 'Q4 Plan', value: 23.0, target: 21.0 }
        ];
        if (!next.chart_type) next.chart_type = 'vertical_bar';
      }
      if (next.layout_type === 'two_column_comparison' && (!next.left_bullets || !next.left_bullets.length)) {
        const d = donor('two_column_comparison');
        next.left_bullets = d.left_bullets || ['Fast self-serve customer onboarding in under 10 minutes', '38% trial-to-paid conversion rate'];
        next.right_bullets = d.right_bullets || ['Dedicated enterprise account management & support', 'Multi-year department expansion agreements'];
      }
      if (next.layout_type === 'financial_table' && !next.table) {
        next.table = donor('financial_table').table || {
          headers: ['Metric', 'Q1 Actual', 'Q2 Actual', 'Q3 Actual', 'Q4 Plan'],
          rows: [['Ending ARR ($M)', '$11.2M', '$14.5M', '$18.4M', '$23.0M'], ['Free Cash Flow Margin', '-8.0%', '-2.5%', '+4.2%', '+9.5%']]
        };
      }
      if ((next.layout_type === 'executive_roadmap' || next.layout_type === 'executive_summary') && (!next.roadmap_phases || !next.roadmap_phases.length)) {
        next.roadmap_phases = donor('executive_roadmap').roadmap_phases || [
          { phase: 'Phase 1: Core Rollout', timeline: 'Weeks 1–4', owner: 'Product & Ops', deliverables: ['Customer onboarding live', 'Field team training'] },
          { phase: 'Phase 2: Expansion', timeline: 'Weeks 5–8', owner: 'Commercial Team', deliverables: ['Account review templates', 'Regional rollout'] },
          { phase: 'Phase 3: Scale', timeline: 'Weeks 9–12', owner: 'Leadership', deliverables: ['Automated monthly reporting', 'Annual budget sign-off'] }
        ];
      }
      if (next.layout_type === 'quote_callout') {
        if (!next.quote_text) next.quote_text = 'Standardizing our quarterly leadership briefings cut preparation time from five days to four hours while giving our board clearer visibility into customer retention and cash flow.';
        if (!next.quote_attribution) next.quote_attribution = 'Chief Operating Officer — Enterprise Customer Case Study';
        if (!next.kpis || !next.kpis.length) next.kpis = [
          { label: 'Time Saved per Review Cycle', value: '84%', delta: '-4.5 days prep', sentiment: 'positive' },
          { label: 'Return on Investment', value: '6.4x', delta: 'Payback in 6 wks', sentiment: 'positive' }
        ];
      }
      return next;
    }
    async function onLayoutDropdownChange() {
      if (!CURRENT_DECK || !CURRENT_DECK.slides[ACTIVE_SLIDE_IDX]) return;
      const cur = CURRENT_DECK.slides[ACTIVE_SLIDE_IDX];
      const next = ensureLayoutDefaults({ ...cur, layout_type: document.getElementById('editSlideLayout').value });
      if (typeof syncStructuredBodyEditor === 'function') syncStructuredBodyEditor(next);
      await applySlideEdits();
    }
    async function applySlideEdits() {
      if (!CURRENT_DECK || !CURRENT_DECK.slides[ACTIVE_SLIDE_IDX]) return;
      const cur = CURRENT_DECK.slides[ACTIVE_SLIDE_IDX];
      const rawTitle = document.getElementById('editActionTitle').value.trim();
      const baseSlide = ensureLayoutDefaults({
        ...cur, layout_type: document.getElementById('editSlideLayout').value,
        action_title: (rawTitle.length >= 3 ? rawTitle : cur.action_title).slice(0, 160),
        subtitle: document.getElementById('editSubtitle').value.slice(0, 240),
        takeaway_banner: document.getElementById('editTakeaway').value.slice(0, 220),
        speaker_notes: document.getElementById('editSpeakerNotes').value.slice(0, 2000),
      });
      const updatedSlide = typeof parseBodyDataEdits === 'function' ? parseBodyDataEdits(baseSlide) : baseSlide;
      CURRENT_DECK = { ...CURRENT_DECK, slides: CURRENT_DECK.slides.map((s, i) => i === ACTIVE_SLIDE_IDX ? updatedSlide : s) };
      await renderDeckPreview(CURRENT_DECK, false);
    }
    const reindexSlides = (slides) => slides.map((s, idx) => ({ ...s, slide_number: idx + 1 }));
    async function addSlide(forcedLayout) {
      if (!CURRENT_DECK || CURRENT_DECK.slides.length >= 25) return;
      const selEl = document.getElementById('newSlideLayoutSelect');
      const chosenLayout = forcedLayout || (selEl ? selEl.value : 'kpi_metrics_grid');
      const [defTitle, defSub] = LAYOUT_DEFAULT_HEADLINES[chosenLayout] || LAYOUT_DEFAULT_HEADLINES.kpi_metrics_grid;
      const base = ensureLayoutDefaults({
        slide_number: CURRENT_DECK.slides.length + 1, layout_type: chosenLayout,
        action_title: defTitle, subtitle: defSub,
        takeaway_banner: 'All core targets remain on track for the quarter.',
        speaker_notes: 'Walk the room through the key takeaways and numbers on this slide.',
      });
      const copy = [...CURRENT_DECK.slides]; copy.splice(ACTIVE_SLIDE_IDX + 1, 0, base);
      CURRENT_DECK = { ...CURRENT_DECK, slides: reindexSlides(copy) };
      ACTIVE_SLIDE_IDX += 1; await renderDeckPreview(CURRENT_DECK, false);
    }
    async function duplicateActiveSlide() {
      if (!CURRENT_DECK || CURRENT_DECK.slides.length >= 25) return;
      const src = JSON.parse(JSON.stringify(CURRENT_DECK.slides[ACTIVE_SLIDE_IDX]));
      src.action_title = (src.action_title + ' (Copy)').slice(0, 160);
      const copy = [...CURRENT_DECK.slides]; copy.splice(ACTIVE_SLIDE_IDX + 1, 0, src);
      CURRENT_DECK = { ...CURRENT_DECK, slides: reindexSlides(copy) };
      ACTIVE_SLIDE_IDX += 1; await renderDeckPreview(CURRENT_DECK, false);
    }
""" + STUDIO_EXT_JS
