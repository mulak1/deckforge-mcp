"""
TDD Test Suite 1: DeckForge Core Engines (Memo Transformer, OpenXML PPTX Builder, Google Slides Batch API).
Covers User Journeys 1-4 (Happy paths, edge cases, boundary validation, XML structural verification).
"""

import base64
import io
import xml.etree.ElementTree as ET
import zipfile
import pytest
from pydantic import ValidationError

from src.models import (
    ChartSeriesItem,
    DeckSpec,
    GoogleSlidesExportRequest,
    KpiMetric,
    MemoTransformRequest,
    RoadmapPhase,
    SlideSpec,
    TableData,
    ThemePalette,
)
from src.memo_transformer import get_executive_presets, transform_memo_to_slide_spec
from src.pptx_engine import build_pptx_bytes, generate_editable_pptx
from src.google_slides_engine import generate_google_slides_batch_requests


def test_theme_palette_hex_validation():
    """Boundary check: Rejects malformed hex color strings and accepts valid 6-char hex."""
    valid = ThemePalette(
        name="McKinsey Navy",
        primary_hex="#0B1F3A",
        secondary_hex="#1D4ED8",
        accent_hex="#0EA5E9",
        background_hex="#F8FAFC",
        text_hex="#0F172A",
        muted_hex="#64748B",
    )
    assert valid.primary_hex == "#0B1F3A"

    with pytest.raises(ValidationError):
        ThemePalette(
            name="Bad Hex",
            primary_hex="not-a-hex",
            secondary_hex="#1D4ED8",
            accent_hex="#0EA5E9",
        )


def test_transform_memo_to_slide_spec_all_layouts():
    """
    User Journey 1: As a strategy lead, I want to transform a raw executive memo with metrics
    into a structured McKinsey/Stripe-grade slide specification with action titles and KPIs.
    """
    raw_memo = """
    Q3 2026 Board Memo: Acme Cloud AI
    ARR reached $18.4M (+142% YoY) while Net Dollar Retention climbed to 124%.
    Gross Margin expanded to 81% (+600 bps) and CAC Payback dropped to 9.5 months.
    Enterprise segment grew from $2.1M to $6.8M across Q1-Q3:
    - Q1 Revenue: $11.2M
    - Q2 Revenue: $14.5M
    - Q3 Revenue: $18.4M
    - Q4 Forecast: $23.0M
    Self-Serve vs Enterprise Motion:
    - Self-Serve PLG: Fast 5-minute onboarding, $24/mo Pro tier, 38% free-to-paid conversion.
    - Enterprise Direct: SAML SSO, SOC2 Type II audit, $48k average ACV, multi-year commits.
    Roadmap:
    - Phase 1 (Q4 2026): Launch Claude & ChatGPT Store Connectors
    - Phase 2 (Q1 2027): Enterprise RBAC & Google Workspace Sync
    - Phase 3 (Q2 2027): Autonomous Board Deck Refresh Agent
    """
    req = MemoTransformRequest(
        raw_memo=raw_memo,
        deck_title="Acme Cloud Q3 2026 Executive Board Deck",
        organization="Acme Cloud AI",
        theme_preset="mckinsey_navy",
        target_slide_count=6,
    )
    result = transform_memo_to_slide_spec(req)
    assert "deck_spec" in result
    deck = DeckSpec.model_validate(result["deck_spec"])
    assert deck.title == "Acme Cloud Q3 2026 Executive Board Deck"
    assert len(deck.slides) == 6

    layout_types = [s.layout_type for s in deck.slides]
    assert "title_hero" in layout_types
    assert "kpi_metrics_grid" in layout_types
    assert "bar_chart_slide" in layout_types
    assert "two_column_comparison" in layout_types
    assert "financial_table" in layout_types
    assert "executive_roadmap" in layout_types

    # Verify KPI extraction found real metrics
    kpi_slide = next(s for s in deck.slides if s.layout_type == "kpi_metrics_grid")
    assert len(kpi_slide.kpis) >= 3
    assert any("$" in k.value or "%" in k.value for k in kpi_slide.kpis)


def test_memo_validation_rejects_too_short_input():
    """Boundary check: Rejects empty or trivially short memo strings."""
    with pytest.raises(ValidationError):
        MemoTransformRequest(raw_memo="too short", deck_title="Valid Title")


def test_generate_editable_pptx_produces_valid_openxml_archive():
    """
    User Journey 2: As an executive user in Claude/ChatGPT, I want generate_editable_pptx
    to build a real, valid OpenXML .pptx archive with all 6 slide layouts and speaker notes.
    """
    presets = get_executive_presets()
    assert len(presets) >= 3
    sample_deck = DeckSpec.model_validate(presets[0]["deck_spec"])

    result = generate_editable_pptx(sample_deck)
    assert result["status"] == "success"
    assert result["slide_count"] == len(sample_deck.slides)
    assert result["file_size_bytes"] > 4000
    assert len(result["sha256"]) == 64

    pptx_bytes = base64.b64decode(result["pptx_base64"])
    assert pptx_bytes == build_pptx_bytes(sample_deck)

    with zipfile.ZipFile(io.BytesIO(pptx_bytes), "r") as zf:
        names = set(zf.namelist())
        assert "[Content_Types].xml" in names
        assert "_rels/.rels" in names
        assert "ppt/presentation.xml" in names
        assert "ppt/_rels/presentation.xml.rels" in names
        assert "ppt/theme/theme1.xml" in names
        assert "ppt/slideMasters/slideMaster1.xml" in names
        assert "ppt/slideLayouts/slideLayout1.xml" in names

        for idx in range(1, len(sample_deck.slides) + 1):
            slide_path = f"ppt/slides/slide{idx}.xml"
            notes_path = f"ppt/notesSlides/notesSlide{idx}.xml"
            assert slide_path in names
            assert notes_path in names

            # Parse every XML file to verify 100% well-formed XML
            slide_xml = zf.read(slide_path)
            root = ET.fromstring(slide_xml)
            assert root.tag.endswith("sld")

            notes_xml = zf.read(notes_path)
            notes_root = ET.fromstring(notes_xml)
            assert notes_root.tag.endswith("notes")


def test_generate_google_slides_batch_requests_and_svg_preview():
    """
    User Journey 3: As a Google Workspace user, I want generate_google_slides_batch_requests
    to produce valid presentations.batchUpdate requests and an interactive HTML/SVG preview.
    """
    presets = get_executive_presets()
    sample_deck = DeckSpec.model_validate(presets[1]["deck_spec"])

    req = GoogleSlidesExportRequest(
        deck_spec=sample_deck,
        presentation_id="1AbCdEfGhIjKlMnOpQrStUvWxYz_demo",
    )
    output = generate_google_slides_batch_requests(req)
    assert output["presentation_id"] == "1AbCdEfGhIjKlMnOpQrStUvWxYz_demo"
    assert output["slide_count"] == len(sample_deck.slides)
    assert isinstance(output["requests"], list)
    assert len(output["requests"]) >= len(sample_deck.slides) * 3

    # Verify createSlide and insertText operations exist
    op_keys = {list(r.keys())[0] for r in output["requests"]}
    assert "createSlide" in op_keys
    assert "createShape" in op_keys
    assert "insertText" in op_keys

    # Verify responsive HTML/SVG preview (with proper XSS-safe HTML escaping)
    assert "<svg" in output["html_preview"]
    assert "Q3 SaaS Revenue, Retention &amp; GTM Efficiency Review" in output["html_preview"]
    assert len(output["slide_svg_cards"]) == len(sample_deck.slides)


def test_five_curated_presets_and_nine_designer_themes():
    """Verifies 5 curated executive presets and all 9 designer themes in THEME_PRESETS."""
    from src.models import THEME_PRESETS

    expected_themes = {
        "mckinsey_navy",
        "stripe_indigo",
        "linear_obsidian",
        "sequoia_emerald",
        "pitch_violet",
        "gamma_editorial",
        "kimi_atlas",
        "kimi_jade",
        "miro_spatial",
    }
    assert expected_themes.issubset(set(THEME_PRESETS.keys()))

    presets = get_executive_presets()
    assert len(presets) == 8
    preset_ids = [p["id"] for p in presets]
    assert "annual_operations_report" in preset_ids
    assert "customer_discovery_roadmap" in preset_ids
    assert "ma_strategic_partnership" in preset_ids
    assert "cfo_budget_vs_actuals" in preset_ids
    assert "customer_case_study_roi" in preset_ids


def test_all_six_bespoke_svg_slide_layouts_render_distinct_vectors():
    """
    Verifies that every one of the 6 slide layouts renders a bespoke designer 960x540 SVG
    rather than falling back to a generic text block.
    """
    presets = get_executive_presets()
    sample_deck = DeckSpec.model_validate(presets[0]["deck_spec"])
    output = generate_google_slides_batch_requests(
        GoogleSlidesExportRequest(deck_spec=sample_deck, presentation_id="1SvgLayoutTest")
    )
    cards_by_layout = {c["layout_type"]: c["svg"] for c in output["slide_svg_cards"]}
    assert set(cards_by_layout.keys()) == {
        "title_hero",
        "kpi_metrics_grid",
        "bar_chart_slide",
        "two_column_comparison",
        "financial_table",
        "executive_roadmap",
    }

    # 1. title_hero: cover badge + hero geometry + takeaway banner
    assert 'data-layout="title_hero"' in cards_by_layout["title_hero"]
    assert "EXECUTIVE BRIEFING" in cards_by_layout["title_hero"]

    # 2. kpi_metrics_grid: 2x2 smart KPI cards with sentiment pill
    assert 'data-layout="kpi_metrics_grid"' in cards_by_layout["kpi_metrics_grid"]
    assert "+142% YoY" in cards_by_layout["kpi_metrics_grid"]

    # 3. bar_chart_slide: proportional column chart with gridlines & target benchmark legend
    assert 'data-layout="bar_chart_slide"' in cards_by_layout["bar_chart_slide"]
    assert "PLAN TARGET" in cards_by_layout["bar_chart_slide"].upper()

    # 4. two_column_comparison: side-by-side cards with central VS badge
    assert 'data-layout="two_column_comparison"' in cards_by_layout["two_column_comparison"]
    assert ">VS<" in cards_by_layout["two_column_comparison"]

    # 5. financial_table: formatted table with header row and zebra-striped rows
    assert 'data-layout="financial_table"' in cards_by_layout["financial_table"]
    assert "Ending ARR ($M)" in cards_by_layout["financial_table"]
    assert "Free Cash Flow Margin" in cards_by_layout["financial_table"]

    # 6. executive_roadmap: 3-column phase-gate cards with timeline pills & checkmarks
    assert 'data-layout="executive_roadmap"' in cards_by_layout["executive_roadmap"]
    assert "Phase 1" in cards_by_layout["executive_roadmap"]
    assert "Weeks 1" in cards_by_layout["executive_roadmap"]


def test_kpi_sentiment_inference_and_directional_arrows_svg_and_pptx():
    """
    Verifies P0 Fix #1:
    - _extract_kpis infers negative, neutral, and inverse-cost positive sentiments accurately
    - SVG _render_kpi_grid_body renders ▲ (positive), ▼ (negative), and ◆ (neutral)
    - PPTX KpiCard shapes use semantic hex colors (#15803D, #B91C1C, #0369A1) and arrows
    """
    memo = (
        "Q4 Operating Memo: Enterprise ARR reached $22.4M (+135% YoY), "
        "Legacy Services Revenue dropped to $1.8M (-24% YoY), "
        "CAC Payback Period dropped to 8.2 mos (-3.1 mos YoY), "
        "Seat Churn Rate climbed to 4.8% (0% flat QoQ)."
    )
    res = transform_memo_to_slide_spec(
        MemoTransformRequest(
            raw_memo=memo,
            deck_title="Sentiment & Direction Verification Deck",
            organization="DeckForge QA",
            theme_preset="mckinsey_navy",
            target_slide_count=6,
        )
    )
    deck = DeckSpec.model_validate(res["deck_spec"])
    kpi_slide = next(s for s in deck.slides if s.layout_type == "kpi_metrics_grid")
    sentiments_by_label = {k.label.lower(): k.sentiment for k in kpi_slide.kpis}

    assert any("arr" in lbl and sent == "positive" for lbl, sent in sentiments_by_label.items())
    assert any("legacy" in lbl and sent == "negative" for lbl, sent in sentiments_by_label.items())
    assert any("payback" in lbl and sent == "positive" for lbl, sent in sentiments_by_label.items())
    assert any("churn" in lbl and sent == "neutral" for lbl, sent in sentiments_by_label.items())

    # Verify SVG directional arrows
    gslides = generate_google_slides_batch_requests(
        GoogleSlidesExportRequest(deck_spec=deck, presentation_id="1KpiSentimentTest")
    )
    kpi_svg = next(c["svg"] for c in gslides["slide_svg_cards"] if c["layout_type"] == "kpi_metrics_grid")
    assert "▲" in kpi_svg
    assert "▼" in kpi_svg
    assert "◆" in kpi_svg
    assert "#15803D" in kpi_svg
    assert "#B91C1C" in kpi_svg
    assert "#0369A1" in kpi_svg

    # Verify PPTX KpiCard semantic colors and arrows
    pptx_bytes = build_pptx_bytes(deck)
    with zipfile.ZipFile(io.BytesIO(pptx_bytes), "r") as zf:
        slide2_xml = zf.read("ppt/slides/slide2.xml").decode("utf-8")
        assert "15803D" in slide2_xml
        assert "B91C1C" in slide2_xml
        assert "0369A1" in slide2_xml
        assert "▲" in slide2_xml
        assert "▼" in slide2_xml
        assert "◆" in slide2_xml


def test_long_action_title_multiline_wrapping_and_financial_table_semantics():
    """
    Verifies P0 Fix #2:
    - Long McKinsey action titles (>76 chars, up to 130 chars) wrap cleanly across 2 lines in SVG
      without mid-word chopping at [:76]
    - Financial table renders full metric labels (up to 38 chars) and colors + / - cells semantically
    """
    from src.svg_renderer import render_slide_svg_card

    long_title = (
        "Accelerating Enterprise Multi-Seat Expansion While Compressing Customer Acquisition Payback Below Nine Months"
    )
    assert len(long_title) > 100
    slide = SlideSpec(
        slide_number=5,
        layout_type="financial_table",
        action_title=long_title,
        subtitle="Quarterly unit economics progression across cohorts",
        takeaway_banner="Positive FCF achieved ahead of plan.",
        table=TableData(
            headers=["Operating Metric Name", "Q1 Actual", "Q2 Actual", "Q3 Actual"],
            rows=[
                ["Enterprise Net New Annual Recurring Rev", "$4.1M", "$5.8M", "$8.4M"],
                ["Free Cash Flow Operating Margin (%)", "-8.0%", "-2.5%", "+4.2%"],
            ],
        ),
    )
    svg = render_slide_svg_card(slide, ThemePalette(), "Board Deck")
    # Must contain the end of the 109-char title ("Below Nine Months") rather than chopping at [:76]
    assert "Below Nine Months" in svg
    assert 'font-size="15.5"' in svg
    # Financial table must preserve long metric label up to 38 chars and semantic +/- colors
    assert "Enterprise Net New Annual Recurring" in svg
    assert "#15803D" in svg
    assert "#B91C1C" in svg


def test_studio_iteration2_interactive_editor_crud_present_and_pkce_ui():
    """
    Verifies P0/P1/P2 Studio UI enhancements:
    - Live Slide Editor & Layout Switcher (#slideEditorPanel, #editSlideLayout, applySlideEdits)
    - Filmstrip CRUD (+ Add Slide, Duplicate Active, moveSlide, deleteSlide)
    - Fullscreen Present Mode (#presentOverlay, #btnPresentMode, ArrowLeft/ArrowRight/Escape)
    - Custom Brand Hex Pickers & 1-Click Live OAuth 2.1 S256 PKCE Handshake Runner (#btnRunPkce)
    """
    from src.studio_ui import render_studio_html

    html = render_studio_html()
    for expected_marker in [
        "slideEditorPanel",
        "editSlideLayout",
        "editActionTitle",
        "applySlideEdits",
        "addSlide()",
        "duplicateActiveSlide()",
        "moveSlide(",
        "deleteSlide(",
        "btnPresentMode",
        "presentOverlay",
        "ArrowRight",
        "ArrowLeft",
        "btnRunPkce",
        "runLivePkceHandshake",
        "applyCustomBrandColors",
    ]:
        assert expected_marker in html, f"Missing Studio UI marker: {expected_marker}"



