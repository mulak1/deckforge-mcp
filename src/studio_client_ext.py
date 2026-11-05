"""
Extended Client-Side Interactive Studio Controllers for DeckForge.
Provides layout-aware Slide Content Editor (all 8 layouts + 4 chart types & configs),
CSV/Spreadsheet Data Importer, 1-Click Wording Polish, 1-Page Meeting Brief, and Readiness Check.
"""

from __future__ import annotations

STUDIO_EXT_JS = """
    const QUICK_LAYOUT_CHIPS = [
      ['title_hero', 'Cover'], ['kpi_metrics_grid', 'Key Numbers'], ['bar_chart_slide', 'Data Chart'],
      ['financial_table', 'Table'], ['two_column_comparison', 'Side-by-Side'], ['executive_roadmap', '3-Step Plan'],
      ['executive_summary', 'Summary'], ['quote_callout', 'Customer Quote']
    ];
    function renderQuickPresetPills() {
      const box = document.getElementById('quickPresetPills'); if (!box || !PRESETS.length) return;
      box.innerHTML = PRESETS.slice(0, 4).map((p, i) =>
        `<button class="preset-chip ${i === ACTIVE_PRESET_IDX ? 'active' : ''}" onclick="loadPreset(${i})">${p.label.split(' ')[0]} ${p.label.split(' ')[1] || ''}</button>`
      ).join('');
    }
    function updateLiveSlideEstimate() {
      const badge = document.getElementById('liveSlideEstimateBadge'); if (!badge) return;
      const raw = (document.getElementById('rawMemo') && document.getElementById('rawMemo').value.trim()) || '';
      const cnt = Number((document.getElementById('targetSlideCountSelect') && document.getElementById('targetSlideCountSelect').value) || 6);
      if (!raw) { badge.textContent = 'Paste notes to estimate slides'; return; }
      const metrics = (raw.match(/(\\$\\d+|\\d+(?:\\.\\d+)?%|\\d+\\s*bps|\\d+(?:\\.\\d+)?x)/gi) || []).length;
      badge.textContent = `~${cnt} slides · ${Math.max(metrics, 1)} metrics detected`;
    }
    function updateThemeSummaryPill() {
      const pill = document.getElementById('activeThemeSummaryPill'); if (!pill) return;
      const tName = (THEMES[ACTIVE_THEME_KEY] && THEMES[ACTIVE_THEME_KEY].name) || 'Boardroom Navy';
      const sKey = (CURRENT_DECK && CURRENT_DECK.theme && CURRENT_DECK.theme.style_family) || 'classic_boardroom';
      const sName = (DESIGN_STYLES[sKey] && DESIGN_STYLES[sKey].label) || 'Classic';
      pill.textContent = `${tName} · ${sName}`;
    }
    function renderQuickLayoutChips(activeLayout) {
      const bar = document.getElementById('quickLayoutChipBar'); if (!bar) return;
      bar.innerHTML = '<span style="font-size:11px;font-weight:800;color:var(--muted);margin-right:4px;">1-Click Layout:</span>' +
        QUICK_LAYOUT_CHIPS.map(([k, lbl]) =>
          `<button class="layout-chip ${k === activeLayout ? 'active' : ''}" onclick="quickSwitchLayout('${k}')">${lbl}</button>`
        ).join('');
    }
    async function quickSwitchLayout(layoutKey) {
      const sel = document.getElementById('editSlideLayout');
      if (sel) sel.value = layoutKey;
      await onLayoutDropdownChange();
    }
    async function moveSlide(idx, dir, ev) {
      if (ev) ev.stopPropagation();
      const target = idx + dir;
      if (!CURRENT_DECK || target < 0 || target >= CURRENT_DECK.slides.length) return;
      const copy = [...CURRENT_DECK.slides]; [copy[idx], copy[target]] = [copy[target], copy[idx]];
      CURRENT_DECK = { ...CURRENT_DECK, slides: reindexSlides(copy) };
      ACTIVE_SLIDE_IDX = target; await renderDeckPreview(CURRENT_DECK, false);
    }
    async function deleteSlide(idx, ev) {
      if (ev) ev.stopPropagation();
      if (!CURRENT_DECK || CURRENT_DECK.slides.length <= 1) return;
      const copy = CURRENT_DECK.slides.filter((_, i) => i !== idx);
      CURRENT_DECK = { ...CURRENT_DECK, slides: reindexSlides(copy) };
      if (ACTIVE_SLIDE_IDX >= copy.length) ACTIVE_SLIDE_IDX = copy.length - 1;
      await renderDeckPreview(CURRENT_DECK, false);
    }
    function togglePresentMode(forceState) {
      PRESENT_ACTIVE = typeof forceState === 'boolean' ? forceState : !PRESENT_ACTIVE;
      document.getElementById('presentOverlay').style.display = PRESENT_ACTIVE ? 'flex' : 'none';
      if (PRESENT_ACTIVE) renderStageSlide();
    }
    function toggleTeleprompter() {
      TELEPROMPTER_VISIBLE = !TELEPROMPTER_VISIBLE;
      document.getElementById('presentNotesBox').style.display = TELEPROMPTER_VISIBLE ? 'block' : 'none';
    }
    function renderAllViews() {
      renderStageSlide();
      document.getElementById('readingFlowContainer').innerHTML = CURRENT_SVGS.map((c, idx) => {
        const s = (CURRENT_DECK && CURRENT_DECK.slides && CURRENT_DECK.slides[idx]) || {};
        return `<article class="reading-card"><div class="reading-card-hdr"><strong>Slide ${c.slide_number} — ${c.action_title}</strong>` +
          `<span class="thumb-badge">${LAYOUT_LABELS[c.layout_type] || c.layout_type}</span></div><div>${c.svg}</div>` +
          `<div style="margin-top:10px;font-size:12.5px;color:#cbd5e1;"><strong>Talking Points:</strong> ${s.speaker_notes || ''}</div></article>`;
      }).join('');
      document.getElementById('storyboardContainer').innerHTML = CURRENT_SVGS.map((c, idx) =>
        `<div class="storyboard-frame" onclick="setViewMode('stage');selectSlide(${idx});">` +
        `<div class="storyboard-frame-hdr"><span>Slide ${c.slide_number} · ${LAYOUT_LABELS[c.layout_type] || c.layout_type}</span><span>Click to Edit</span></div><div>${c.svg}</div></div>`
      ).join('');
    }
    function extractBodyDataSlice(slide) {
      const lt = slide.layout_type || 'title_hero';
      if (lt === 'kpi_metrics_grid') return { kpis: slide.kpis || [] };
      if (lt === 'bar_chart_slide') return {
        chart_title: slide.chart_title || 'Quarterly Performance',
        chart_unit: slide.chart_unit || '$M',
        chart_type: slide.chart_type || 'vertical_bar',
        chart_show_target: slide.chart_show_target !== false,
        chart_show_values: slide.chart_show_values !== false,
        chart_show_grid: slide.chart_show_grid !== false,
        chart_series: slide.chart_series || []
      };
      if (lt === 'two_column_comparison') return { left_column_title: slide.left_column_title || 'Left Column', left_bullets: slide.left_bullets || [], right_column_title: slide.right_column_title || 'Right Column', right_bullets: slide.right_bullets || [] };
      if (lt === 'financial_table') return { table: slide.table || { headers: ['Metric', 'Q1', 'Q2', 'Q3', 'Q4'], rows: [] } };
      if (lt === 'executive_roadmap' || lt === 'executive_summary') return { roadmap_phases: slide.roadmap_phases || [] };
      if (lt === 'quote_callout') return { quote_text: slide.quote_text || '', quote_attribution: slide.quote_attribution || '', kpis: (slide.kpis || []).slice(0, 2) };
      return { subtitle: slide.subtitle || '', takeaway_banner: slide.takeaway_banner || '' };
    }
    function escAttr(v) { return String(v || '').replace(/&/g, '&amp;').replace(/"/g, '&quot;').replace(/</g, '&lt;'); }
    function syncStructuredBodyEditor(slide) {
      const ensured = ensureLayoutDefaults(slide);
      const slice = extractBodyDataSlice(ensured);
      const jsonBox = document.getElementById('editBodyDataJson');
      if (jsonBox) jsonBox.value = JSON.stringify(slice, null, 2);
      const box = document.getElementById('structuredBodyFields');
      if (!box) return;
      const lt = ensured.layout_type;
      if (lt === 'kpi_metrics_grid') {
        box.innerHTML = (ensured.kpis || []).slice(0, 4).map((k, i) =>
          `<div style="display:grid;grid-template-columns:1.4fr 0.9fr 1fr 0.8fr;gap:6px;margin-bottom:6px;">` +
          `<input data-kpi-idx="${i}" data-field="label" value="${escAttr(k.label)}" placeholder="Metric Name" oninput="syncVisualFieldsToJson()" />` +
          `<input data-kpi-idx="${i}" data-field="value" value="${escAttr(k.value)}" placeholder="Number" oninput="syncVisualFieldsToJson()" />` +
          `<input data-kpi-idx="${i}" data-field="delta" value="${escAttr(k.delta)}" placeholder="Change (e.g. +18%)" oninput="syncVisualFieldsToJson()" />` +
          `<select data-kpi-idx="${i}" data-field="sentiment" onchange="syncVisualFieldsToJson()">` +
          `<option value="positive" ${k.sentiment === 'positive' ? 'selected' : ''}>▲ Improving</option>` +
          `<option value="negative" ${k.sentiment === 'negative' ? 'selected' : ''}>▼ Declining</option>` +
          `<option value="neutral" ${k.sentiment === 'neutral' ? 'selected' : ''}>◆ Unchanged</option></select></div>`
        ).join('');
      } else if (lt === 'bar_chart_slide') {
        const ct = ensured.chart_type || 'vertical_bar';
        box.innerHTML =
          `<div style="display:grid;grid-template-columns:1.2fr 1.1fr 80px;gap:6px;margin-bottom:8px;">` +
          `<div><label style="margin-top:0;">Chart Heading</label><input id="visChartTitle" value="${escAttr(ensured.chart_title)}" oninput="syncVisualFieldsToJson()" /></div>` +
          `<div><label style="margin-top:0;">Chart Type (4 Styles)</label><select id="visChartType" onchange="syncVisualFieldsToJson();applySlideEdits();">` +
          `<option value="vertical_bar" ${ct === 'vertical_bar' ? 'selected' : ''}>Vertical Column Chart</option>` +
          `<option value="line_trend" ${ct === 'line_trend' ? 'selected' : ''}>Line &amp; Area Trend Chart</option>` +
          `<option value="horizontal_bar" ${ct === 'horizontal_bar' ? 'selected' : ''}>Horizontal Ranking Bars</option>` +
          `<option value="stacked_bar" ${ct === 'stacked_bar' ? 'selected' : ''}>Stacked vs. Goal Columns</option></select></div>` +
          `<div><label style="margin-top:0;">Unit</label><input id="visChartUnit" value="${escAttr(ensured.chart_unit)}" oninput="syncVisualFieldsToJson()" /></div></div>` +
          `<div style="display:flex;gap:16px;align-items:center;margin-bottom:8px;font-size:11.5px;color:#cbd5e1;">` +
          `<label style="display:inline-flex;align-items:center;gap:5px;margin:0;text-transform:none;"><input type="checkbox" id="visChartShowTarget" ${ensured.chart_show_target !== false ? 'checked' : ''} onchange="syncVisualFieldsToJson();applySlideEdits();" /> Show Plan/Target Benchmark</label>` +
          `<label style="display:inline-flex;align-items:center;gap:5px;margin:0;text-transform:none;"><input type="checkbox" id="visChartShowValues" ${ensured.chart_show_values !== false ? 'checked' : ''} onchange="syncVisualFieldsToJson();applySlideEdits();" /> Show Value Labels</label>` +
          `<label style="display:inline-flex;align-items:center;gap:5px;margin:0;text-transform:none;"><input type="checkbox" id="visChartShowGrid" ${ensured.chart_show_grid !== false ? 'checked' : ''} onchange="syncVisualFieldsToJson();applySlideEdits();" /> Show Gridlines</label></div>` +
          (ensured.chart_series || []).map((c, i) =>
            `<div style="display:grid;grid-template-columns:1.3fr 1fr 1fr;gap:6px;margin-bottom:6px;">` +
            `<input data-bar-idx="${i}" data-field="category" value="${escAttr(c.category)}" placeholder="Quarter / Category" oninput="syncVisualFieldsToJson()" />` +
            `<input data-bar-idx="${i}" data-field="value" type="number" step="0.1" value="${c.value}" placeholder="Actual" oninput="syncVisualFieldsToJson()" />` +
            `<input data-bar-idx="${i}" data-field="target" type="number" step="0.1" value="${c.target ?? ''}" placeholder="Plan Goal" oninput="syncVisualFieldsToJson()" /></div>`
          ).join('');
      } else if (lt === 'two_column_comparison') {
        box.innerHTML = `<div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;">` +
          `<div><input id="visLeftColTitle" value="${escAttr(ensured.left_column_title)}" oninput="syncVisualFieldsToJson()" style="margin-bottom:4px;" />` +
          `<textarea id="visLeftBullets" oninput="syncVisualFieldsToJson()" style="min-height:64px;">${escAttr((ensured.left_bullets || []).join('\\n'))}</textarea></div>` +
          `<div><input id="visRightColTitle" value="${escAttr(ensured.right_column_title)}" oninput="syncVisualFieldsToJson()" style="margin-bottom:4px;" />` +
          `<textarea id="visRightBullets" oninput="syncVisualFieldsToJson()" style="min-height:64px;">${escAttr((ensured.right_bullets || []).join('\\n'))}</textarea></div></div>`;
      } else if (lt === 'financial_table') {
        const tbl = ensured.table || { headers: ['Metric', 'Q1', 'Q2', 'Q3', 'Q4'], rows: [] };
        box.innerHTML = `<input id="visTblHeaders" value="${escAttr((tbl.headers || []).join(' | '))}" oninput="syncVisualFieldsToJson()" style="margin-bottom:6px;" />` +
          `<textarea id="visTblRows" oninput="syncVisualFieldsToJson()" style="min-height:76px;">${escAttr((tbl.rows || []).map(r => r.join(' | ')).join('\\n'))}</textarea>`;
      } else if (lt === 'executive_roadmap' || lt === 'executive_summary') {
        box.innerHTML = (ensured.roadmap_phases || []).slice(0, 3).map((p, i) =>
          `<div style="display:grid;grid-template-columns:1fr 0.7fr 0.7fr 1.6fr;gap:6px;margin-bottom:6px;">` +
          `<input data-rm-idx="${i}" data-field="phase" value="${escAttr(p.phase)}" oninput="syncVisualFieldsToJson()" />` +
          `<input data-rm-idx="${i}" data-field="timeline" value="${escAttr(p.timeline)}" oninput="syncVisualFieldsToJson()" />` +
          `<input data-rm-idx="${i}" data-field="owner" value="${escAttr(p.owner)}" oninput="syncVisualFieldsToJson()" />` +
          `<input data-rm-idx="${i}" data-field="deliverables" value="${escAttr((p.deliverables || []).join(' ; '))}" oninput="syncVisualFieldsToJson()" /></div>`
        ).join('');
      } else if (lt === 'quote_callout') {
        const k0 = (ensured.kpis && ensured.kpis[0]) || { label: 'Time Saved', value: '84%', delta: '-4.5 days' };
        const k1 = (ensured.kpis && ensured.kpis[1]) || { label: 'ROI Multiple', value: '6.4x', delta: '6 wks payback' };
        box.innerHTML =
          `<label style="margin-top:0;">Customer or Executive Quote</label>` +
          `<textarea id="visQuoteText" oninput="syncVisualFieldsToJson()" style="min-height:54px;margin-bottom:6px;">${escAttr(ensured.quote_text)}</textarea>` +
          `<input id="visQuoteAttrib" value="${escAttr(ensured.quote_attribution)}" placeholder="Speaker Name &amp; Title" oninput="syncVisualFieldsToJson()" style="margin-bottom:6px;" />` +
          `<div style="display:grid;grid-template-columns:1fr 1fr;gap:6px;">` +
          `<input id="visQuoteKpi0" value="${escAttr(k0.label + ' | ' + k0.value + ' | ' + k0.delta)}" oninput="syncVisualFieldsToJson()" />` +
          `<input id="visQuoteKpi1" value="${escAttr(k1.label + ' | ' + k1.value + ' | ' + k1.delta)}" oninput="syncVisualFieldsToJson()" /></div>`;
      } else {
        box.innerHTML = `<div style="font-size:11.5px;color:var(--muted);">Cover slide uses the Headline, Supporting Subtitle, and Bottom Takeaway Line above.</div>`;
      }
    }
    function syncVisualFieldsToJson() {
      const lt = document.getElementById('editSlideLayout').value, jsonBox = document.getElementById('editBodyDataJson');
      if (!jsonBox) return;
      let obj = {};
      if (lt === 'kpi_metrics_grid') {
        obj = { kpis: [0, 1, 2, 3].map(i => {
          const lbl = document.querySelector(`[data-kpi-idx="${i}"][data-field="label"]`);
          return lbl ? {
            label: lbl.value, value: document.querySelector(`[data-kpi-idx="${i}"][data-field="value"]`).value,
            delta: document.querySelector(`[data-kpi-idx="${i}"][data-field="delta"]`).value,
            sentiment: document.querySelector(`[data-kpi-idx="${i}"][data-field="sentiment"]`).value
          } : null;
        }).filter(Boolean) };
      } else if (lt === 'bar_chart_slide') {
        const items = [];
        document.querySelectorAll('[data-bar-idx][data-field="category"]').forEach((el, i) => {
          const val = parseFloat(document.querySelector(`[data-bar-idx="${i}"][data-field="value"]`).value || '0');
          const tRaw = document.querySelector(`[data-bar-idx="${i}"][data-field="target"]`).value;
          items.push({ category: el.value, value: val, target: tRaw !== '' ? parseFloat(tRaw) : null });
        });
        obj = {
          chart_title: document.getElementById('visChartTitle').value, chart_unit: document.getElementById('visChartUnit').value,
          chart_type: document.getElementById('visChartType') ? document.getElementById('visChartType').value : 'vertical_bar',
          chart_show_target: document.getElementById('visChartShowTarget') ? document.getElementById('visChartShowTarget').checked : true,
          chart_show_values: document.getElementById('visChartShowValues') ? document.getElementById('visChartShowValues').checked : true,
          chart_show_grid: document.getElementById('visChartShowGrid') ? document.getElementById('visChartShowGrid').checked : true,
          chart_series: items
        };
      } else if (lt === 'two_column_comparison') {
        obj = {
          left_column_title: document.getElementById('visLeftColTitle').value,
          left_bullets: document.getElementById('visLeftBullets').value.split('\\n').map(s => s.trim()).filter(Boolean),
          right_column_title: document.getElementById('visRightColTitle').value,
          right_bullets: document.getElementById('visRightBullets').value.split('\\n').map(s => s.trim()).filter(Boolean)
        };
      } else if (lt === 'financial_table') {
        obj = { table: {
          headers: document.getElementById('visTblHeaders').value.split('|').map(s => s.trim()).filter(Boolean),
          rows: document.getElementById('visTblRows').value.split('\\n').map(r => r.split('|').map(c => c.trim())).filter(r => r.length && r[0])
        }};
      } else if (lt === 'executive_roadmap' || lt === 'executive_summary') {
        const phases = [];
        document.querySelectorAll('[data-rm-idx][data-field="phase"]').forEach((el, i) => {
          phases.push({
            phase: el.value, timeline: document.querySelector(`[data-rm-idx="${i}"][data-field="timeline"]`).value,
            owner: document.querySelector(`[data-rm-idx="${i}"][data-field="owner"]`).value,
            deliverables: document.querySelector(`[data-rm-idx="${i}"][data-field="deliverables"]`).value.split(';').map(s => s.trim()).filter(Boolean)
          });
        });
        obj = { roadmap_phases: phases };
      } else if (lt === 'quote_callout') {
        const parseKpi = (id) => {
          const p = (document.getElementById(id) ? document.getElementById(id).value : '').split('|').map(s => s.trim());
          return { label: p[0] || 'Impact Metric', value: p[1] || '84%', delta: p[2] || '+25% YoY', sentiment: 'positive' };
        };
        obj = { quote_text: document.getElementById('visQuoteText').value, quote_attribution: document.getElementById('visQuoteAttrib').value, kpis: [parseKpi('visQuoteKpi0'), parseKpi('visQuoteKpi1')] };
      }
      jsonBox.value = JSON.stringify(obj, null, 2);
    }
    function parseBodyDataEdits(slide) {
      const jsonBox = document.getElementById('editBodyDataJson');
      if (!jsonBox || !jsonBox.value.trim()) return slide;
      try { return { ...slide, ...JSON.parse(jsonBox.value) }; } catch (_) { return slide; }
    }
    function pasteSampleSheetData() {
      document.getElementById('importSlideTitle').value = 'Regional Enterprise Revenue vs. Plan Target ($M)';
      document.getElementById('importChartUnit').value = '$M';
      document.getElementById('rawTabularData').value = 'Region,Actual Revenue ($M),Plan Goal ($M),YoY Growth\\nNorth America,24.8,22.0,+38%\\nEurope & UK,14.6,13.5,+44%\\nAsia-Pacific,9.4,8.2,+52%\\nLatin America,5.2,4.8,+31%';
    }
    function handleCsvFileUpload(inputEl) {
      const file = inputEl && inputEl.files && inputEl.files[0];
      if (!file) return;
      const reader = new FileReader();
      reader.onload = (ev) => {
        document.getElementById('rawTabularData').value = String(ev.target.result || '');
        const cleanName = file.name.replace(/\\.(csv|tsv|txt)$/i, '').replace(/[_-]+/g, ' ');
        if (cleanName) document.getElementById('importSlideTitle').value = 'Imported Data: ' + cleanName;
      };
      reader.readAsText(file);
    }
    async function runDataImport(targetMode) {
      if (!CURRENT_DECK) return;
      let rawText = document.getElementById('rawTabularData').value.trim();
      if (!rawText) { pasteSampleSheetData(); rawText = document.getElementById('rawTabularData').value.trim(); }
      const res = await fetch('/api/tools/import-data', {
        method: 'POST', headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
          raw_tabular_text: rawText,
          target_mode: targetMode,
          chart_type: document.getElementById('importChartType').value,
          chart_unit: document.getElementById('importChartUnit').value || '$M',
          slide_title: document.getElementById('importSlideTitle').value || 'Imported Performance Data',
          deck_spec: CURRENT_DECK
        })
      });
      const data = await res.json();
      if (data.deck_spec) {
        CURRENT_DECK = data.deck_spec;
        ACTIVE_SLIDE_IDX = CURRENT_DECK.slides.length - 1;
        await renderDeckPreview(CURRENT_DECK, false);
        document.getElementById('jsonInspector').textContent = JSON.stringify({
          imported_mode: data.target_mode, rows_imported: data.rows_imported, slide_number: ACTIVE_SLIDE_IDX + 1
        }, null, 2);
      }
    }
    async function polishActiveSlide() {
      if (!CURRENT_DECK || !CURRENT_DECK.slides[ACTIVE_SLIDE_IDX]) return;
      const targetLayout = document.getElementById('editSlideLayout').value;
      const res = await fetch('/api/tools/remix-slide', {
        method: 'POST', headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ deck_spec: CURRENT_DECK, slide_number: ACTIVE_SLIDE_IDX + 1, new_layout_type: targetLayout, polish_mode: true })
      });
      const data = await res.json();
      if (data.deck_spec) {
        CURRENT_DECK = data.deck_spec;
        await renderDeckPreview(CURRENT_DECK, false);
        document.getElementById('jsonInspector').textContent = JSON.stringify({ slide_wording_polished: true, slide_number: data.slide_number, layout: data.new_layout }, null, 2);
      }
    }
    async function openExecutiveBrief() {
      if (!CURRENT_DECK) return;
      const res = await fetch('/api/tools/executive-brief', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({ deck_spec: CURRENT_DECK, api_key: 'df_free_demo' }) });
      const data = await res.json();
      const box = document.getElementById('readinessReportBox');
      if (box && data.brief_markdown) {
        box.style.display = 'block';
        box.innerHTML = `<div style="background:#0f172a;border:1px solid var(--accent);border-radius:8px;padding:10px;">` +
          `<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;gap:4px;"><strong style="color:var(--accent);">1-Page Meeting Read-Ahead Brief</strong>` +
          `<div style="display:flex;gap:4px;"><button class="btn-secondary" style="padding:3px 8px;font-size:11px;" onclick="navigator.clipboard.writeText(window.LAST_BRIEF_MD||'')">Copy</button>` +
          `<button class="btn-secondary" style="padding:3px 8px;font-size:11px;" onclick="downloadExecutiveBrief()">⬇ Save (.md)</button></div></div>` +
          `<pre style="max-height:220px;color:#e2e8f0;margin-top:4px;">${escAttr(data.brief_markdown)}</pre></div>`;
        window.LAST_BRIEF_MD = data.brief_markdown;
      }
      document.getElementById('jsonInspector').textContent = data.brief_markdown || JSON.stringify(data, null, 2);
    }
    function downloadExecutiveBrief() {
      if (!window.LAST_BRIEF_MD) return;
      const slug = ((CURRENT_DECK && CURRENT_DECK.title) || 'meeting_brief').toLowerCase().replace(/[^a-z0-9]+/g, '_') + '_1page_brief.md';
      const url = URL.createObjectURL(new Blob([window.LAST_BRIEF_MD], { type: 'text/markdown' }));
      const a = document.createElement('a'); a.href = url; a.download = slug;
      document.body.appendChild(a); a.click(); a.remove(); URL.revokeObjectURL(url);
    }
    async function runDeckQualityCheck() {
      if (!CURRENT_DECK) return;
      const res = await fetch('/api/tools/audit-deck', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({ deck_spec: CURRENT_DECK, api_key: 'df_free_demo' }) });
      const data = await res.json();
      const box = document.getElementById('readinessReportBox');
      if (box && data.checks) {
        box.style.display = 'block';
        const itemsHtml = data.checks.map(c => `<li style="margin-bottom:4px;"><strong>${escAttr(c.slide)} (${escAttr(c.status)}):</strong> ${escAttr(c.tip)}</li>`).join('');
        box.innerHTML = `<div style="background:#0f172a;border:1px solid #10b981;border-radius:8px;padding:10px;">` +
          `<div style="font-weight:800;color:#34d399;margin-bottom:6px;">Readiness Score: ${data.readiness_score}/100 — ${escAttr(data.verdict)}</div>` +
          `<ul style="padding-left:16px;color:#cbd5e1;font-size:11.5px;">${itemsHtml}</ul></div>`;
      }
      document.getElementById('jsonInspector').textContent = JSON.stringify(data, null, 2);
    }
    function downloadStandaloneHtml() {
      if (!CURRENT_DECK || !CURRENT_SVGS.length) return;
      const slidesHtml = CURRENT_SVGS.map((c, i) => {
        const s = (CURRENT_DECK.slides && CURRENT_DECK.slides[i]) || {};
        return `<section class="slide-frame" data-idx="${i}" style="display:${i === 0 ? 'block' : 'none'};max-width:960px;margin:0 auto;">` +
          `<div>${c.svg}</div><div style="margin-top:12px;padding:12px 16px;background:#0f172a;border-left:4px solid #38bdf8;border-radius:8px;color:#e2e8f0;font-size:14px;">` +
          `<strong>Slide ${c.slide_number} Talking Points:</strong> ${escAttr(s.speaker_notes || '')}</div></section>`;
      }).join('');
      const doc = `<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><title>${escAttr(CURRENT_DECK.title)} — Interactive Presentation</title>` +
        `<style>body{font-family:Inter,system-ui,sans-serif;background:#070b14;color:#f8fafc;margin:0;padding:24px;}header{max-width:960px;margin:0 auto 16px;display:flex;justify-content:space-between;align-items:center;}button{background:#1e293b;color:#f8fafc;border:1px solid #334155;padding:8px 14px;border-radius:8px;cursor:pointer;font-weight:700;}</style></head>` +
        `<body><header><div><strong>${escAttr(CURRENT_DECK.title)}</strong> <span id="cnt" style="color:#38bdf8;margin-left:8px;">Slide 1 of ${CURRENT_SVGS.length}</span></div>` +
        `<div style="display:flex;gap:8px;"><button onclick="go(-1)">← Previous</button><button onclick="go(1)">Next →</button></div></header>${slidesHtml}` +
        `<script>let cur=0,tot=${CURRENT_SVGS.length};function go(d){cur=Math.max(0,Math.min(tot-1,cur+d));document.querySelectorAll('.slide-frame').forEach((el,i)=>el.style.display=i===cur?'block':'none');document.getElementById('cnt').textContent='Slide '+(cur+1)+' of '+tot;}window.addEventListener('keydown',e=>{if(e.key==='ArrowRight')go(1);if(e.key==='ArrowLeft')go(-1);});<` + `/script></body></html>`;
      const slug = (CURRENT_DECK.title.toLowerCase().replace(/[^a-z0-9]+/g, '_') || 'deckforge') + '_interactive_deck.html';
      const url = URL.createObjectURL(new Blob([doc], { type: 'text/html' }));
      const a = document.createElement('a'); a.href = url; a.download = slug;
      document.body.appendChild(a); a.click(); a.remove(); URL.revokeObjectURL(url);
      document.getElementById('jsonInspector').textContent = JSON.stringify({ exported_standalone_html: slug, slide_count: CURRENT_SVGS.length }, null, 2);
    }
    async function refreshQuota() {
      const sel = document.getElementById('apiKeySelect');
      if (window.location.search.includes('pro_activated=1') || localStorage.getItem('df_pro_active') === '1') {
        localStorage.setItem('df_pro_active', '1');
        if (sel) sel.value = 'df_pro_enterprise';
        const hLink = document.getElementById('headerUpgradeLink');
        if (hLink) hLink.textContent = '✓ Pro Plan Active ($49.99)';
        const cLink = document.getElementById('cardUpgradeLink');
        if (cLink) cLink.textContent = '✓ Pro Plan Active ($49.99)';
      }
      const key = sel ? sel.value : 'df_free_demo';
      const q = await (await fetch('/api/quota?api_key=' + encodeURIComponent(key))).json();
      document.getElementById('quotaBox').innerHTML = `<div><strong>Plan:</strong> ${q.price_label}</div><div><strong>Presentations Built:</strong> ${q.decks_used} of ${q.tier === 'pro' ? 'Unlimited' : q.decks_limit} this month</div>`;
    }
    async function downloadPptxFile() {
      if (!CURRENT_DECK) return;
      const apiKey = document.getElementById('apiKeySelect').value;
      const res = await fetch('/api/pptx/download', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({deck_spec: CURRENT_DECK, api_key: apiKey}) });
      if (!res.ok) { document.getElementById('jsonInspector').textContent = JSON.stringify(await res.json(), null, 2); await refreshQuota(); return; }
      const url = URL.createObjectURL(await res.blob());
      const a = document.createElement('a'); a.href = url; a.download = (CURRENT_DECK.title.toLowerCase().replace(/[^a-z0-9]+/g, '_') || 'deckforge') + '.pptx';
      document.body.appendChild(a); a.click(); a.remove(); URL.revokeObjectURL(url);
      await refreshQuota();
    }
    async function inspectGoogleSlides() {
      if (!CURRENT_DECK) return;
      const d = await (await fetch('/api/tools/google-slides', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({deck_spec: CURRENT_DECK, presentation_id: '1DeckForgeLiveSync_99'}) })).json();
      document.getElementById('jsonInspector').textContent = JSON.stringify({ presentation_id: d.presentation_id, operations_count: d.operations_count, sample_requests: d.requests.slice(0, 5) }, null, 2);
    }
    async function inspectMcpTools() {
      const res = await fetch('/mcp', { method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({jsonrpc:'2.0',id:99,method:'tools/list',params:{}}) });
      document.getElementById('jsonInspector').textContent = JSON.stringify(await res.json(), null, 2);
    }
    async function inspectMcpResources() {
      const res = await fetch('/mcp', { method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({jsonrpc:'2.0',id:100,method:'resources/list',params:{}}) });
      document.getElementById('jsonInspector').textContent = JSON.stringify(await res.json(), null, 2);
    }
    async function runLivePkceHandshake() {
      const verifier = 'dBjftJeZ4CVP-mB92K27uhbUJU1p1r_wW1gFWFOEjXk', challenge = 'E9Melhoa2OwvFrEMTJguCHaoeK1t8URWbuGJSstw-cM', redirectUri = 'http://localhost:8793/callback';
      const regRes = await (await fetch('/oauth/register', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({ client_name: 'Presentation Studio Client', redirect_uris: [redirectUri] }) })).json();
      const authUrl = `/oauth/authorize?response_type=code&client_id=${encodeURIComponent(regRes.client_id)}&redirect_uri=${encodeURIComponent(redirectUri)}&code_challenge=${encodeURIComponent(challenge)}&code_challenge_method=S256&state=studio_s256_verified`;
      const authRes = await (await fetch(authUrl)).json();
      const tokenRes = await (await fetch('/oauth/token', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({ grant_type: 'authorization_code', code: authRes.code, client_id: regRes.client_id, redirect_uri: redirectUri, code_verifier: verifier }) })).json();
      document.getElementById('jsonInspector').textContent = JSON.stringify({ connection_status: 'VERIFIED', step1_register: regRes, step2_authorize: { code: authRes.code, state: authRes.state }, step3_token: tokenRes }, null, 2);
    }
    function copyMcpUrl() { navigator.clipboard.writeText('http://localhost:8793/mcp'); document.getElementById('jsonInspector').textContent = 'Copied http://localhost:8793/mcp to clipboard!'; }
    initStudio();
"""
