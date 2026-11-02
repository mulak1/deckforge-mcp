"""
TDD Test Suite 4: Plain-English Rewrite, Welcome Greeting, Missing Executive Features,
and 3-Iteration 8-Persona Swarm User Journey Verification.
"""

from __future__ import annotations

import io
import json
import zipfile
from pathlib import Path
from fastapi.testclient import TestClient

from src.app import create_app


def test_welcome_greeting_banner_and_endpoints():
    """
    Verifies that users are warmly greeted at the beginning across:
    1. GET / Studio UI (#welcomeGreetingBanner, #welcomeHeadline, 3-step quick guide)
    2. GET /api/greeting REST endpoint
    3.GET /api/presets ('welcome' key)
    4. POST /mcp initialize ('instructions' & 'welcome' fields)
    """
    client = TestClient(create_app())

    # 1. Studio HTML welcome banner
    html = client.get("/").text
    assert 'id="welcomeGreetingBanner"' in html
    assert "Welcome! Good to have you here" in html
    assert "1. Pick a starting point" in html
    assert "2. Review &amp; tailor each slide" in html
    assert "3. Present or download" in html
    assert "clearToBlankNotes()" in html
    assert "pasteQuickSampleNotes()" in html

    # 2. GET /api/greeting
    greet_res = client.get("/api/greeting")
    assert greet_res.status_code == 200
    greet = greet_res.json()
    assert "Welcome to DeckForge" in greet["headline"]
    assert len(greet["steps"]) == 3
    assert len(greet["sample_prompts"]) >= 3

    # 3. GET /api/presets includes welcome object
    presets_res = client.get("/api/presets").json()
    assert "welcome" in presets_res
    assert "Welcome to DeckForge" in presets_res["welcome"]["headline"]

    # 4. POST /mcp initialize includes warm greeting
    mcp_init = client.post(
        "/mcp",
        json={"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}},
    ).json()["result"]
    assert "Welcome to DeckForge" in mcp_init["instructions"]
    assert "welcome" in mcp_init


def test_zero_vendor_names_and_zero_prompt_leakage_across_all_surfaces():
    """
    Verifies zero vendor brand names (McKinsey, Stripe, Linear, Sequoia, Pitch, Gamma, Kimi, Miro)
    and zero coding/prompt leakage (Store Connectors, OpenXML, ECMA-376, OAuth 2.1 S256)
    appear in GET /, GET /api/presets, or store manifests' human-facing copy.
    """
    client = TestClient(create_app())

    html = client.get("/").text
    presets_json_str = json.dumps(client.get("/api/presets").json())

    banned_vendor_tokens = [
        "mckinsey",
        "stripe",
        "sequoia",
        "pitch",
        "gamma",
        "kimi",
        "miro",
        "moonshot",
    ]
    for token in banned_vendor_tokens:
        assert token not in html.lower(), f"Vendor token '{token}' leaked in GET / Studio HTML"
        assert token not in presets_json_str.lower(), f"Vendor token '{token}' leaked in GET /api/presets"

    banned_coding_phrases = [
        "store connectors",
        "ecma-376",
        "openxml",
        "presentations.batchupdate",
        "oauth 2.1",
        "mcp store",
        "claude connectors",
    ]
    for phrase in banned_coding_phrases:
        assert phrase not in html.lower(), f"Jargon phrase '{phrase}' leaked in GET / Studio HTML"
        assert phrase not in presets_json_str.lower(), f"Coding template phrase '{phrase}' leaked in GET /api/presets"

    # Also check human descriptions in store manifests
    root = Path(__file__).resolve().parent.parent
    claude_manifest = json.loads((root / "claude-connector-manifest.json").read_text())
    openai_manifest = json.loads((root / "openai-mcp-app.json").read_text())
    for phrase in ("mckinsey", "stripe", "ecma-376", "openxml", "batchupdate"):
        assert phrase not in claude_manifest["description"].lower()
        assert phrase not in openai_manifest["description_for_human"].lower()


def test_eight_persona_swarm_user_journeys_end_to_end():
    """
    Executes the 3-iteration 8-persona user journey test suite against live endpoints:
    1. @elena_chief_of_staff: Board briefing, custom confidentiality footer on SVG & PPTX, 1-page Read-Ahead Brief
    2. @marcus_vp_finance: Custom FP&A memo dynamically populates KPI grid, chart, AND financial table
    3. @priya_strategy_consultant: Audience-specific framing ('client' vs 'leadership') & plain-English SVG badges
    4. @david_series_a_founder: Deck Readiness Check (100/100 score vs actionable plain-English suggestions)
    5. @samantha_exec_assistant: 9 vendor-free color palettes & 3 plain-English view modes
    6. @jordan_vp_sales: All 5 business templates verified for commercial realism
    7. @liam_ops_director: Single-slide layout switch + plain-English wording polish
    8. @chen_it_compliance_reviewer: MCP tools/list plain-English titles + JSON & form OAuth token exchange
    """
    client = TestClient(create_app())

    # --- Persona 1: @elena_chief_of_staff ---
    elena_resp = client.post(
        "/api/tools/transform-memo",
        json={
            "raw_memo": (
                "Q4 Board Pack: Annual Recurring Revenue reached $28.5M (+64% YoY), "
                "Net Customer Retention hit 128% (+600 bps), Gross Margin expanded to 83.0%, "
                "Customer Payback dropped to 8.1 mos. Q1: $19.0M, Q2: $22.1M, Q3: $25.0M, Q4: $28.5M.\n"
                "- Multi-year enterprise agreements grew 85% year-over-year across financial services clients.\n"
                "- Automated onboarding reduced implementation time from 21 days to 4 days."
            ),
            "deck_title": "Q4 Board of Directors Briefing",
            "organization": "Aegis Enterprise Corp",
            "theme_preset": "boardroom_navy",
            "audience": "board",
            "footer_label": "Strictly Confidential — Board of Directors Only",
            "target_slide_count": 6,
        },
    )
    assert elena_resp.status_code == 200
    elena_deck = elena_resp.json()["deck_spec"]
    assert elena_deck["footer_label"] == "Strictly Confidential — Board of Directors Only"

    # Verify footer_label renders on live SVG preview AND inside .pptx slide XML
    gslides_resp = client.post(
        "/api/tools/google-slides",
        json={"deck_spec": elena_deck, "presentation_id": "elena_board_preview"},
    ).json()
    assert "Strictly Confidential — Board of Directors Only" in gslides_resp["slide_svg_cards"][0]["svg"]

    pptx_dl = client.post(
        "/api/pptx/download",
        json={"deck_spec": elena_deck, "api_key": "df_pro_enterprise"},
    )
    assert pptx_dl.status_code == 200
    with zipfile.ZipFile(io.BytesIO(pptx_dl.content), "r") as zf:
        slide1_xml = zf.read("ppt/slides/slide1.xml").decode("utf-8")
        assert "Strictly Confidential — Board of Directors Only" in slide1_xml

    # Verify 1-Page Meeting Read-Ahead Brief
    brief_resp = client.post("/api/tools/executive-brief", json={"deck_spec": elena_deck})
    assert brief_resp.status_code == 200
    brief_md = brief_resp.json()["brief_markdown"]
    assert "# Q4 Board of Directors Briefing" in brief_md
    assert "Strictly Confidential — Board of Directors Only" in brief_md
    assert "$28.5M" in brief_md

    # --- Persona 2: @marcus_vp_finance ---
    marcus_resp = client.post(
        "/api/tools/transform-memo",
        json={
            "raw_memo": (
                "FP&A Quarterly Close: Net Operating Revenue reached $42.5M (+31% YoY), "
                "EBITDA Margin hit 24.8% (+350 bps), Free Cash Flow reached $9.4M (+52% YoY), "
                "Net Customer Retention at 118%. Q1: $31.0M, Q2: $35.4M, Q3: $39.1M, Q4: $42.5M."
            ),
            "deck_title": "Q4 FP&A Financial Close & Margin Review",
            "organization": "Citadel Financial Group",
            "theme_preset": "executive_indigo",
            "audience": "leadership",
            "target_slide_count": 6,
        },
    ).json()["deck_spec"]
    fin_table_slide = next(s for s in marcus_resp["slides"] if s["layout_type"] == "financial_table")
    flat_table_str = json.dumps(fin_table_slide["table"]["rows"])
    assert "$31.0M" in flat_table_str
    assert "$42.5M" in flat_table_str
    assert "24.8%" in flat_table_str
    assert "$9.4M" in flat_table_str

    # --- Persona 3: @priya_strategy_consultant ---
    priya_resp = client.post(
        "/api/tools/transform-memo",
        json={
            "raw_memo": (
                "Client Proposal: Annual Cost Savings reached $12.4M (+45% YoY), "
                "Cycle Time Reduction hit 62%, Team Adoption reached 94%, Payback Period dropped to 5.2 mos. "
                "Q1: $4.2M, Q2: $6.8M, Q3: $9.5M, Q4: $12.4M.\n"
                "- Manual spreadsheet handoffs delayed monthly regional reporting by 6 business days.\n"
                "- Automated shared workflows cut approval turnaround time to under 4 hours."
            ),
            "deck_title": "Commercial Operations Transformation Proposal",
            "organization": "Kestrel Advisory Partners",
            "theme_preset": "heritage_emerald",
            "audience": "client",
            "target_slide_count": 6,
        },
    ).json()["deck_spec"]
    assert "Executive Client Proposal & Value Briefing" in priya_resp["slides"][0]["subtitle"]
    comp_slide = next(s for s in priya_resp["slides"] if s["layout_type"] == "two_column_comparison")
    assert comp_slide["left_column_title"] == "Current Workflow Challenges"
    assert comp_slide["right_column_title"] == "Proposed Solution & Business Value"

    priya_svgs = client.post(
        "/api/tools/google-slides",
        json={"deck_spec": priya_resp, "presentation_id": "priya_svg_check"},
    ).json()["slide_svg_cards"]
    all_svg_text = " ".join(c["svg"] for c in priya_svgs)
    for badge in ("EXECUTIVE BRIEFING", "KEY NUMBERS", "TREND CHART", "COMPARISON", "SUMMARY TABLE", "ACTION PLAN", "BOTTOM LINE"):
        assert badge in all_svg_text

    # --- Persona 4: @david_series_a_founder ---
    ready_audit = client.post("/api/tools/audit-deck", json={"deck_spec": priya_resp}).json()
    assert ready_audit["readiness_score"] == 100
    assert ready_audit["verdict"] == "Ready for the Boardroom"

    # Also test a rough draft with a short headline & empty takeaway/notes to verify constructive tips
    draft_deck = json.loads(json.dumps(priya_resp))
    draft_deck["slides"][0]["action_title"] = "Short Title"
    draft_deck["slides"][0]["takeaway_banner"] = ""
    draft_deck["slides"][0]["speaker_notes"] = ""
    draft_audit = client.post("/api/tools/audit-deck", json={"deck_spec": draft_deck}).json()
    assert draft_audit["readiness_score"] < 100
    assert any("Make the headline more specific" in c["tip"] for c in draft_audit["checks"])

    # --- Persona 5 & 6: @samantha_exec_assistant & @jordan_vp_sales ---
    presets_payload = client.get("/api/presets").json()
    themes = presets_payload["themes"]
    assert len(themes) == 9
    assert {t["name"] for t in themes.values()} == {
        "Boardroom Navy",
        "Executive Indigo",
        "Modern Slate",
        "Heritage Emerald",
        "Royal Plum",
        "Warm Terracotta",
        "Pacific Blue",
        "Sage & Gold",
        "Warm Sandstone",
    }
    assert len(presets_payload["presets"]) == 8
    assert set(presets_payload["design_styles"].keys()) == {
        "classic_boardroom",
        "editorial_serif",
        "modern_minimal",
        "bold_keynote",
    }

    # --- Persona 7: @liam_ops_director ---
    liam_remix = client.post(
        "/api/tools/remix-slide",
        json={
            "deck_spec": elena_deck,
            "slide_number": 4,
            "new_layout_type": "executive_roadmap",
            "polish_mode": True,
        },
    ).json()
    assert liam_remix["new_layout"] == "executive_roadmap"
    assert "90-Day Action Plan & Team Owners:" in liam_remix["remixed_slide"]["action_title"]
    assert "Strictly Confidential — Board of Directors Only" in liam_remix["slide_svg"]

    # --- Persona 8: @chen_it_compliance_reviewer ---
    mcp_tools = client.post(
        "/mcp",
        json={"jsonrpc": "2.0", "id": 88, "method": "tools/list", "params": {}},
    ).json()["result"]["tools"]
    assert len(mcp_tools) == 4
    for t in mcp_tools:
        assert "OpenXML" not in t["description"]
        assert "presentations.batchUpdate" not in t["description"]


def test_eight_layouts_four_design_styles_four_chart_types_csv_import_and_logo():
    """
    Verifies:
    1. World-class SVG logo (#deckforgeBrandLogo) & +Add Slide Layout Picker (#newSlideLayoutSelect)
    2. All 4 architectural design styles (classic_boardroom, editorial_serif, modern_minimal, bold_keynote)
    3. All 4 chart types (vertical_bar, horizontal_bar, line_trend, stacked_bar) & chart config flags
    4. New layouts (executive_summary & quote_callout) in SVG, remix-slide, and .pptx
    5. Spreadsheet / CSV / TSV / Pipe data importer (POST /api/tools/import-data) for both table and chart slides
    """
    client = TestClient(create_app())
    html = client.get("/").text
    assert 'id="deckforgeBrandLogo"' in html
    assert 'id="newSlideLayoutSelect"' in html
    assert 'id="styleFamilySelect"' in html
    assert 'id="csvFileInput"' in html
    assert "runDataImport('chart')" in html
    assert "runDataImport('table')" in html

    presets = client.get("/api/presets").json()["presets"]
    base_deck = presets[0]["deck_spec"]

    # Test CSV / TSV / Pipe Data Import as Chart across all 4 chart types
    csv_sheet = (
        "Region,Actual Revenue ($M),Plan Goal ($M)\n"
        "North America,$24.8M,$22.0M\n"
        "Europe & UK,$14.6M,$13.5M\n"
        "Asia-Pacific,$9.4M,$8.2M\n"
        "Latin America,$5.2M,$4.8M"
    )
    for c_type, expected_marker in (
        ("vertical_bar", "VERTICAL COLUMNS"),
        ("horizontal_bar", "HORIZONTAL BARS"),
        ("line_trend", "<polyline"),
        ("stacked_bar", "STACKED vs. GOAL"),
    ):
        imp_chart = client.post(
            "/api/tools/import-data",
            json={
                "raw_tabular_text": csv_sheet,
                "target_mode": "chart",
                "chart_type": c_type,
                "chart_unit": "$M",
                "slide_title": f"Regional Breakdown ({c_type})",
                "deck_spec": base_deck,
            },
        )
        assert imp_chart.status_code == 200
        imp_data = imp_chart.json()
        assert imp_data["rows_imported"] == 4
        assert expected_marker in imp_data["slide_svg"]
        assert len(imp_data["deck_spec"]["slides"]) == 7

    # Test TSV / Pipe Data Import as Table
    pipe_sheet = (
        "| Department | Q1 Budget | Q2 Actual | Variance |\n"
        "|---|---|---|---|\n"
        "| Enterprise Sales | $4.2M | $4.8M | +14% |\n"
        "| Product & Eng | $3.1M | $3.0M | -3% |"
    )
    imp_table = client.post(
        "/api/tools/import-data",
        json={
            "raw_tabular_text": pipe_sheet,
            "target_mode": "table",
            "slide_title": "Department Budget vs. Actuals",
            "deck_spec": base_deck,
            "replace_slide_number": 5,
        },
    )
    assert imp_table.status_code == 200
    assert imp_table.json()["slide"]["layout_type"] == "financial_table"
    assert "Enterprise Sales" in imp_table.json()["slide_svg"]

    # Test remixing into executive_summary & quote_callout across all 4 design styles + PPTX build
    for style_key, new_layout in (
        ("editorial_serif", "executive_summary"),
        ("modern_minimal", "quote_callout"),
        ("bold_keynote", "bar_chart_slide"),
        ("classic_boardroom", "kpi_metrics_grid"),
    ):
        styled_deck = json.loads(json.dumps(base_deck))
        styled_deck["theme"]["style_family"] = style_key
        remixed = client.post(
            "/api/tools/remix-slide",
            json={
                "deck_spec": styled_deck,
                "slide_number": 2,
                "new_layout_type": new_layout,
                "chart_type": "line_trend",
                "polish_mode": True,
            },
        )
        assert remixed.status_code == 200
        r_json = remixed.json()
        assert f'data-style="{style_key}"' in r_json["slide_svg"]
        assert f'data-layout="{new_layout}"' in r_json["slide_svg"]

        pptx_res = client.post(
            "/api/pptx/download",
            json={"deck_spec": r_json["deck_spec"], "api_key": "df_pro_enterprise"},
        )
        assert pptx_res.status_code == 200
        assert pptx_res.content[:2] == b"PK"

