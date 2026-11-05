"""
TDD Test Suite 3 (Iteration 3 Final Polish):
1. CURRENCY_OR_PCT_RE full unit extraction (9.5 mos, 1.4x, 38s, 4.2 mos) & unclipped KPI labels
2. Dark-Canvas Theme Contrast Engine (_is_dark_hex & adaptive dark SVG surfaces across all 6 layouts)
3. .pptx ChartTargetBar_N benchmark bars & layout-aware Google Slides multi-card shapes
4. 4th MCP tool remix_or_update_slide (/mcp & POST /api/tools/remix-slide)
5. Studio UI Structured Body Data Editor, 1-Click AI Executive Polish, and Standalone .HTML Export
"""

import io
import zipfile
import pytest
from fastapi.testclient import TestClient

from src.app import create_app
from src.google_slides_engine import generate_google_slides_batch_requests
from src.memo_transformer import get_executive_presets, remix_or_update_slide
from src.models import DeckSpec, GoogleSlidesExportRequest, SlideRemixRequest, SlideSpec, ThemePalette
from src.pptx_engine import build_pptx_bytes
from src.studio_ui import render_studio_html
from src.svg_renderer import _is_dark_hex, render_slide_svg_card


def test_preset_kpi_extraction_preserves_full_units_and_unclipped_labels():
    """
    Verifies P0 Fix #1:
    - Multi-char units ('9.5 mos', '4.2 mos') are never truncated to '9.5 m' or '4.2 m'
    - Multipliers ('1.4x') and seconds ('38s') are extracted cleanly
    - Long labels ('Validated Enterprise Prototype Score', 'Net New ARR') are never clipped mid-word
    """
    presets = {p["id"]: DeckSpec.model_validate(p["deck_spec"]) for p in get_executive_presets()}

    # 1. Series A Board: '9.5 mos' (not '9.5 m')
    s_a_kpis = presets["series_a_board"].slides[1].kpis
    s_a_values = [k.value for k in s_a_kpis]
    assert "9.5 mos" in s_a_values
    assert "9.5 m" not in s_a_values

    # 2. Q3 SaaS Review: 'Net New ARR' and '1.4x'
    q3_kpis = presets["q3_saas_review"].slides[1].kpis
    q3_labels = [k.label for k in q3_kpis]
    q3_values = [k.value for k in q3_kpis]
    assert "Net New ARR" in q3_labels
    assert "1.4x" in q3_values

    # 3. Enterprise Launch: '38s' and '98%'
    ent_kpis = presets["enterprise_launch"].slides[1].kpis
    ent_values = [k.value for k in ent_kpis]
    assert "38s" in ent_values
    assert "98%" in ent_values

    # 5. Customer Discovery Roadmap: 'Validated Enterprise Prototype Score' (not 'ed Enterprise Prototype Score') and '4.2 mos'
    miro_kpis = presets["customer_discovery_roadmap"].slides[1].kpis
    miro_labels = [k.label for k in miro_kpis]
    miro_values = [k.value for k in miro_kpis]
    assert "Validated Enterprise Prototype Score" in miro_labels
    assert not any(lbl.startswith("ed ") for lbl in miro_labels)
    assert "4.2 mos" in miro_values
    assert "4.2 m" not in miro_values


def test_dark_canvas_theme_contrast_engine_across_all_layouts():
    """
    Verifies P1 Fix #3:
    - _is_dark_hex accurately classifies dark vs light hex strings
    - When theme.background_hex is dark (#0F172A), all body layouts render dark-mode elevated cards (#1E293B)
      and high-contrast light text (#F8FAFC / #CBD5E1) instead of dark navy on dark slate.
    """
    assert _is_dark_hex("#0F172A") is True
    assert _is_dark_hex("#090D16") is True
    assert _is_dark_hex("#F8FAFC") is False
    assert _is_dark_hex("#FEFCE8") is False
    assert _is_dark_hex("bad") is False

    dark_theme = ThemePalette(
        name="Obsidian Dark Canvas",
        primary_hex="#0B1F3A",
        secondary_hex="#3B82F6",
        accent_hex="#38BDF8",
        background_hex="#0F172A",
        text_hex="#F8FAFC",
        muted_hex="#CBD5E1",
    )
    sample_deck = DeckSpec.model_validate(get_executive_presets()[0]["deck_spec"])
    for slide in sample_deck.slides:
        svg = render_slide_svg_card(slide, dark_theme, sample_deck.title)
        if slide.layout_type != "title_hero":
            assert 'fill="#1E293B"' in svg
            assert 'fill="#F8FAFC"' in svg


def test_pptx_target_benchmark_bars_and_google_slides_multicard_shapes():
    """
    Verifies P1 Fix #4:
    - .pptx slide3.xml (bar_chart_slide) emits ChartTargetBar_1 alongside ChartBar_1
    - Google Slides batchUpdate emits _kpi_1..4, _col_left/_col_right, and _phase_1..3 shapes
    """
    deck = DeckSpec.model_validate(get_executive_presets()[0]["deck_spec"])
    pptx_bytes = build_pptx_bytes(deck)
    with zipfile.ZipFile(io.BytesIO(pptx_bytes), "r") as zf:
        slide3_xml = zf.read("ppt/slides/slide3.xml").decode("utf-8")
        assert 'name="ChartBar_1"' in slide3_xml
        assert 'name="ChartTargetBar_1"' in slide3_xml
        assert "Plan: " in slide3_xml

    gslides = generate_google_slides_batch_requests(
        GoogleSlidesExportRequest(deck_spec=deck, presentation_id="1MultiCardShapeTest")
    )
    created_ids = {
        r["createShape"]["objectId"]
        for r in gslides["requests"]
        if "createShape" in r
    }
    assert "df_slide_02_kpi_1" in created_ids
    assert "df_slide_02_kpi_4" in created_ids
    assert "df_slide_04_col_left" in created_ids
    assert "df_slide_04_col_right" in created_ids
    assert "df_slide_06_phase_1" in created_ids
    assert "df_slide_06_phase_3" in created_ids


def test_remix_or_update_slide_mcp_tool_and_rest_endpoint():
    """
    Verifies P1 Fix #5:
    - remix_or_update_slide remixes a slide across all layout types, populates default layout data,
      and applies AI executive polish
    - Exposes remix_or_update_slide via POST /mcp (tools/call) and POST /api/tools/remix-slide
    """
    deck = DeckSpec.model_validate(get_executive_presets()[0]["deck_spec"])

    # Direct unit test across layouts on a bare slide
    bare_slide = SlideSpec(
        slide_number=1,
        layout_type="title_hero",
        action_title="Initial Cover Title",
        subtitle="Initial Subtitle",
    )
    minimal_deck = deck.model_copy(update={"slides": [bare_slide]})
    for target_layout in (
        "kpi_metrics_grid",
        "bar_chart_slide",
        "two_column_comparison",
        "financial_table",
        "executive_roadmap",
        "title_hero",
    ):
        res = remix_or_update_slide(
            SlideRemixRequest(
                deck_spec=minimal_deck,
                slide_number=1,
                new_layout_type=target_layout,
                polish_mode=True,
            )
        )
        assert res["status"] == "success"
        assert res["new_layout"] == target_layout
        assert "Board Delivery Cue:" in res["remixed_slide"]["speaker_notes"]
        assert f'data-layout="{target_layout}"' in res["slide_svg"]

    # Out-of-range slide_number raises ValueError
    with pytest.raises(ValueError):
        remix_or_update_slide(SlideRemixRequest(deck_spec=deck, slide_number=99))

    # REST & MCP endpoint verification
    client = TestClient(create_app())
    rest_resp = client.post(
        "/api/tools/remix-slide",
        json={
            "deck_spec": deck.model_dump(mode="json"),
            "slide_number": 2,
            "new_layout_type": "bar_chart_slide",
            "polish_mode": True,
            "action_title": "Custom Executive Override Title",
            "takeaway_banner": "Custom Override Takeaway",
        },
    )
    assert rest_resp.status_code == 200
    rest_data = rest_resp.json()
    assert rest_data["remixed_slide"]["action_title"] == "Custom Executive Override Title"
    assert rest_data["remixed_slide"]["takeaway_banner"] == "Custom Override Takeaway"

    bad_rest = client.post(
        "/api/tools/remix-slide",
        json={"deck_spec": deck.model_dump(mode="json"), "slide_number": 45},
    )
    assert bad_rest.status_code == 400

    mcp_resp = client.post(
        "/mcp",
        json={
            "jsonrpc": "2.0",
            "id": 77,
            "method": "tools/call",
            "params": {
                "name": "remix_or_update_slide",
                "arguments": {
                    "deck_spec": deck.model_dump(mode="json"),
                    "slide_number": 3,
                    "polish_mode": True,
                },
            },
        },
    )
    assert mcp_resp.status_code == 200
    assert mcp_resp.json()["result"]["isError"] is False


def test_studio_ui_structured_body_editor_magic_polish_and_html_export():
    """
    Verifies P0 UX #2 & P1 Export #5 markers in render_studio_html():
    - #structuredBodyFields, #editBodyDataJson, syncStructuredBodyEditor, parseBodyDataEdits
    - #btnMagicPolish, polishActiveSlide()
    - #btnExportHtml, downloadStandaloneHtml()
    """
    html = render_studio_html()
    for marker in [
        "structuredBodyFields",
        "editBodyDataJson",
        "syncStructuredBodyEditor",
        "parseBodyDataEdits",
        "btnMagicPolish",
        "polishActiveSlide()",
        "btnExportHtml",
        "downloadStandaloneHtml()",
    ]:
        assert marker in html, f"Missing Iteration 3 Studio UI marker: {marker}"


def test_studio_ui_simplification_and_intuitiveness_iteration():
    """
    Verifies the 5 UI Simplification & Intuitiveness improvements:
    1. Progressive Disclosure ('customizeThemeDrawer', 'activeThemeSummaryPill')
    2. Arrow-Key & Bottom Slide Progress Bar ('bottomSlideNav', 'bottomSlideProgressPill')
    3. 1-Click Quick Layout Switcher ('quickLayoutChipBar', 'quickSwitchLayout')
    4. Live Slide Estimate Badge + Clear + Starter Pills ('liveSlideEstimateBadge', 'btnClearNotes', 'quickPresetPills')
    5. Unified Export Bar ('btnHeroDownloadPptx', 'moreFormatsMenu')
    """
    html = render_studio_html()
    for marker in [
        "customizeThemeDrawer",
        "activeThemeSummaryPill",
        "bottomSlideNav",
        "bottomSlideProgressPill",
        "quickLayoutChipBar",
        "quickSwitchLayout",
        "liveSlideEstimateBadge",
        "btnClearNotes",
        "quickPresetPills",
        "moreFormatsMenu",
        "btnHeroDownloadPptx",
    ]:
        assert marker in html, f"Missing UI simplification marker: {marker}"


def test_p0_slim_tools_list_payload_under_5kb_and_fully_typed():
    """Verifies P0 #1: tools/list JSON response is < 5 KB with explicit type & description and zero $ref/anyOf."""
    import json as _json

    client = TestClient(create_app())
    resp = client.post("/mcp", json={"jsonrpc": "2.0", "id": 10, "method": "tools/list", "params": {}})
    assert resp.status_code == 200
    raw_bytes = len(resp.content)
    assert raw_bytes < 5000, f"Expected tools/list < 5000 bytes, got {raw_bytes} bytes"
    raw_text = resp.text
    assert '"$ref"' not in raw_text
    assert '"anyOf"' not in raw_text
    for tool in resp.json()["result"]["tools"]:
        props = tool["inputSchema"].get("properties", {})
        for pname, pval in props.items():
            assert "type" in pval, f"Missing type on {tool['name']}.{pname}"
            assert "description" in pval, f"Missing description on {tool['name']}.{pname}"


def test_p0_forgiving_cold_call_llm_input_normalizer():
    """Verifies P0 #2: Cold-call LLM aliases (deck_title, title, layout, bullet_points) normalize cleanly with isError=False."""
    client = TestClient(create_app())
    cold_spec = {
        "deck_title": "Q3 Board Update",
        "slides": [
            {
                "slide_number": 1,
                "title": "Executive Summary",
                "layout": "title_hero",
                "bullet_points": ["ARR grew 142% YoY", "NRR reached 124%"],
            },
            {
                "title": "Key Operating Metrics",
                "layout": "kpi",
                "bullets": ["Gross margin expanded to 81.2%", "CAC payback improved to 9.5 mos"],
            },
        ],
    }
    for tool_name in ("generate_editable_pptx", "generate_google_slides_batch_requests", "remix_or_update_slide"):
        resp = client.post(
            "/mcp",
            json={
                "jsonrpc": "2.0",
                "id": 20,
                "method": "tools/call",
                "params": {"name": tool_name, "arguments": {"deck_spec": cold_spec}},
            },
        )
        assert resp.status_code == 200
        result = resp.json()["result"]
        assert result["isError"] is False, f"{tool_name} failed on cold LLM input: {result}"


def test_p0_clickable_ephemeral_https_pptx_download_link():
    """Verifies P0 #3: generate_editable_pptx returns a clickable /downloads/<filename>.pptx link that serves valid .pptx bytes."""
    client = TestClient(create_app())
    resp = client.post(
        "/mcp",
        json={
            "jsonrpc": "2.0",
            "id": 30,
            "method": "tools/call",
            "params": {
                "name": "generate_editable_pptx",
                "arguments": {
                    "deck_spec": {
                        "deck_title": "Q3 Executive Briefing",
                        "slides": [{"slide_number": 1, "title": "Headline Overview", "layout": "title_hero"}],
                    }
                },
            },
        },
    )
    assert resp.status_code == 200
    res = resp.json()["result"]
    assert res["isError"] is False
    text_block = res["content"][0]["text"]
    assert "https://deckforge-mcp-production.up.railway.app/downloads/" in text_block
    dl_url = res["structuredContent"]["download_url"]
    dl_path = "/downloads/" + dl_url.split("/downloads/")[-1]
    dl_resp = client.get(dl_path)
    assert dl_resp.status_code == 200
    assert dl_resp.headers["content-type"] == "application/vnd.openxmlformats-officedocument.presentationml.presentation"
    assert dl_resp.content[:4] == b"PK\x03\x04"


def test_p0_zero_bloat_studio_ux_polish_markers():
    """Verifies P0 #4: Studio UI includes 1-click Tighten Wording, Copy Talking Points, Cmd+Enter shortcut, and @media print."""
    html = render_studio_html()
    for marker in [
        "btnTightenBullets",
        "tightenActiveSlideBullets()",
        "btnCopyTalkingPoints",
        "copyActiveTalkingPoints()",
        "@media print",
        "⌘↵",
    ]:
        assert marker in html, f"Missing P0 Studio UX marker: {marker}"


