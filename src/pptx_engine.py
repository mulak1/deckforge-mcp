"""
Pure-Python ECMA-376 OpenXML PowerPoint (.pptx) Generator for DeckForge MCP.
Builds valid, editable 16:9 widescreen .pptx archives with native DrawingML vector shapes,
KPI grids, proportional bar chart geometry, financial tables, roadmaps, and speaker notes.
"""

from __future__ import annotations

import base64
import hashlib
import io
import zipfile
from typing import Any, Dict, List

from src.models import DeckSpec, SlideSpec, ThemePalette
from src.openxml_parts import (
    A_NS,
    P_NS,
    R_NS,
    REL_NS,
    build_content_types_xml,
    build_notes_xml,
    build_presentation_xml,
    build_theme_xml,
    hex_clean,
    xml_esc,
)


def _shape_box(
    shape_id: int,
    name: str,
    x: int,
    y: int,
    cx: int,
    cy: int,
    fill_hex: str,
    lines: List[tuple[str, int, str, bool]],
    geom: str = "rect",
    border_hex: str | None = None,
) -> str:
    """Renders a DrawingML <p:sp> vector shape with multi-paragraph styled text."""
    stroke_xml = (
        f'<a:ln w="12700"><a:solidFill><a:srgbClr val="{hex_clean(border_hex)}"/></a:solidFill></a:ln>'
        if border_hex
        else "<a:ln><a:noFill/></a:ln>"
    )
    paras: List[str] = []
    for text, pt_size, text_hex, is_bold in lines:
        b_attr = ' b="1"' if is_bold else ""
        sz_val = int(pt_size * 100)
        paras.append(
            f'<a:p><a:r><a:rPr lang="en-US" sz="{sz_val}"{b_attr} dirty="0">'
            f'<a:solidFill><a:srgbClr val="{hex_clean(text_hex)}"/></a:solidFill>'
            f'<a:latin typeface="Calibri"/></a:rPr>'
            f"<a:t>{xml_esc(text)}</a:t></a:r></a:p>"
        )
    if not paras:
        paras.append('<a:p><a:endParaRPr lang="en-US"/></a:p>')

    return (
        f"<p:sp>"
        f'<p:nvSpPr><p:cNvPr id="{shape_id}" name="{xml_esc(name)}"/><p:cNvSpPr/><p:nvPr/></p:nvSpPr>'
        f"<p:spPr>"
        f'<a:xfrm><a:off x="{x}" y="{y}"/><a:ext cx="{cx}" cy="{cy}"/></a:xfrm>'
        f'<a:prstGeom prst="{geom}"><a:avLst/></a:prstGeom>'
        f'<a:solidFill><a:srgbClr val="{hex_clean(fill_hex)}"/></a:solidFill>'
        f"{stroke_xml}"
        f"</p:spPr>"
        f'<p:txBody><a:bodyPr wrap="square" lIns="114300" tIns="91440" rIns="114300" bIns="91440"/>'
        f"<a:lstStyle/>{''.join(paras)}</p:txBody>"
        f"</p:sp>"
    )


def _build_bar_chart_shapes(slide: SlideSpec, theme: ThemePalette, sid: int) -> List[str]:
    series = slide.chart_series or []
    max_val = max((max(item.value, item.target or 0.0) for item in series), default=1.0) or 1.0
    slot_w = int(10200000 / max(len(series), 1))
    bar_w = int(slot_w * 0.42)
    target_w = int(bar_w * 0.78)
    shapes: List[str] = []
    for idx, item in enumerate(series):
        bar_h = max(int((item.value / max_val) * 3100000), 240000)
        x = 960000 + idx * slot_w
        y = 5100000 - bar_h
        shapes.append(
            _shape_box(
                sid + idx * 3,
                f"ChartBar_{idx + 1}",
                x,
                y,
                bar_w,
                bar_h,
                theme.secondary_hex,
                [(f"{item.value}{slide.chart_unit}", 12, "#FFFFFF", True)],
            )
        )
        if item.target is not None and item.target > 0:
            t_h = max(int((item.target / max_val) * 3100000), 200000)
            t_x = x + bar_w + 50000
            t_y = 5100000 - t_h
            shapes.append(
                _shape_box(
                    sid + idx * 3 + 1,
                    f"ChartTargetBar_{idx + 1}",
                    t_x,
                    t_y,
                    target_w,
                    t_h,
                    theme.accent_hex,
                    [(f"Plan: {item.target}{slide.chart_unit}", 10, "#FFFFFF", True)],
                    border_hex=theme.primary_hex,
                )
            )
        shapes.append(
            _shape_box(
                sid + idx * 3 + 2,
                f"ChartLabel_{idx + 1}",
                x,
                5160000,
                bar_w + target_w,
                420000,
                theme.background_hex,
                [(item.category, 11, theme.text_hex, True)],
            )
        )
    return shapes


def _render_layout_shapes(
    slide: SlideSpec,
    theme: ThemePalette,
    deck_title: str,
    footer_label: str = "Confidential — Leadership Briefing",
) -> List[str]:
    shapes: List[str] = [
        _shape_box(2, "SlideBackground", 0, 0, 12192000, 6858000, theme.background_hex, []),
        _shape_box(
            3,
            "HeaderBanner",
            0,
            0,
            12192000,
            960000,
            theme.primary_hex,
            [
                (slide.action_title, 20, "#FFFFFF", True),
                (slide.subtitle or deck_title, 11, "#CBD5E1", False),
            ],
        ),
    ]
    sid = 10

    if slide.layout_type == "title_hero":
        shapes.append(
            _shape_box(
                sid, "HeroCard", 720000, 1450000, 10752000, 3600000, theme.primary_hex,
                [(deck_title, 34, "#FFFFFF", True), (slide.subtitle, 16, "#93C5FD", False), (slide.takeaway_banner, 14, "#F8FAFC", True)],
                geom="roundRect", border_hex=theme.accent_hex,
            )
        )
    elif slide.layout_type == "kpi_metrics_grid":
        for idx, kpi in enumerate(slide.kpis[:4]):
            x = 720000 + (idx % 2) * 5520000
            y = 1320000 + (idx // 2) * 2050000
            arrow = "▼" if kpi.sentiment == "negative" else ("◆" if kpi.sentiment == "neutral" else "▲")
            delta_color = "#B91C1C" if kpi.sentiment == "negative" else ("#0369A1" if kpi.sentiment == "neutral" else "#15803D")
            shapes.append(
                _shape_box(
                    sid + idx, f"KpiCard_{idx + 1}", x, y, 5200000, 1820000, "#FFFFFF",
                    [(kpi.label.upper(), 11, theme.muted_hex, True), (kpi.value, 32, theme.primary_hex, True), (f"{arrow} Delta: {kpi.delta}", 13, delta_color, True)],
                    geom="roundRect", border_hex=theme.secondary_hex,
                )
            )
    elif slide.layout_type == "bar_chart_slide":
        shapes.extend(_build_bar_chart_shapes(slide, theme, sid))
    elif slide.layout_type == "two_column_comparison":
        left_lines = [(slide.left_column_title, 16, theme.primary_hex, True)] + [(f"• {b}", 12, theme.text_hex, False) for b in slide.left_bullets]
        right_lines = [(slide.right_column_title, 16, theme.secondary_hex, True)] + [(f"• {b}", 12, theme.text_hex, False) for b in slide.right_bullets]
        shapes.append(_shape_box(sid, "LeftColumnCard", 720000, 1320000, 5200000, 4100000, "#FFFFFF", left_lines, "roundRect", theme.primary_hex))
        shapes.append(_shape_box(sid + 1, "RightColumnCard", 6240000, 1320000, 5200000, 4100000, "#FFFFFF", right_lines, "roundRect", theme.secondary_hex))
    elif slide.layout_type == "financial_table" and slide.table:
        shapes.append(_shape_box(sid, "TableHeaderRow", 720000, 1320000, 10752000, 560000, theme.primary_hex, [("   |   ".join(slide.table.headers), 13, "#FFFFFF", True)]))
        for r_idx, row in enumerate(slide.table.rows[:6]):
            fill = "#FFFFFF" if r_idx % 2 == 0 else "#E2E8F0"
            shapes.append(
                _shape_box(
                    sid + r_idx + 1, f"TableRow_{r_idx + 1}", 720000, 1920000 + r_idx * 560000, 10752000, 520000,
                    fill, [("   |   ".join(row), 12, theme.text_hex, False)], border_hex="#CBD5E1",
                )
            )
    elif slide.layout_type == "quote_callout":
        q_txt = slide.quote_text or "Standardizing our quarterly leadership briefings cut preparation time from five days to four hours."
        q_attr = slide.quote_attribution or "Chief Operating Officer — Customer Case Study"
        shapes.append(
            _shape_box(
                sid, "QuoteSpotlightCard", 720000, 1360000, 10752000, 3950000, "#FFFFFF",
                [(f'"{q_txt}"', 20, theme.primary_hex, True), (f"— {q_attr}", 14, theme.secondary_hex, True)],
                geom="roundRect", border_hex=theme.accent_hex,
            )
        )
    else:
        phases = slide.roadmap_phases or []
        col_w = int(10600000 / max(len(phases), 1)) - 120000
        for p_idx, phase in enumerate(phases[:4]):
            x = 720000 + p_idx * (col_w + 150000)
            lines = [(phase.timeline.upper(), 11, theme.accent_hex, True), (phase.phase, 15, theme.primary_hex, True), (f"Owner: {phase.owner}", 11, theme.muted_hex, False)] + [
                (f"✓ {d}", 11, theme.text_hex, False) for d in phase.deliverables
            ]
            shapes.append(_shape_box(sid + p_idx, f"RoadmapPhase_{p_idx + 1}", x, 1360000, col_w, 3950000, "#FFFFFF", lines, "roundRect", theme.secondary_hex))

    if slide.takeaway_banner:
        shapes.append(
            _shape_box(
                90, "BottomTakeawayBanner", 720000, 5720000, 10752000, 640000, theme.primary_hex,
                [(f"BOTTOM LINE: {slide.takeaway_banner}", 12, "#FFFFFF", True)], geom="roundRect",
            )
        )
    if footer_label:
        shapes.append(
            _shape_box(
                91, "SlideFooterNote", 720000, 6420000, 10752000, 340000, theme.background_hex,
                [(f"{footer_label}   |   Slide {slide.slide_number}", 9, theme.muted_hex, False)],
            )
        )
    return shapes


def _build_slide_xml(
    slide: SlideSpec,
    theme: ThemePalette,
    deck_title: str,
    footer_label: str = "Confidential — Leadership Briefing",
) -> str:
    shapes_xml = "".join(_render_layout_shapes(slide, theme, deck_title, footer_label))
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        f'<p:sld xmlns:a="{A_NS}" xmlns:r="{R_NS}" xmlns:p="{P_NS}">'
        "<p:cSld><p:spTree>"
        '<p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr>'
        '<p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/>'
        '<a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr>'
        f"{shapes_xml}"
        "</p:spTree></p:cSld>"
        '<p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr>'
        "</p:sld>"
    )


def build_pptx_bytes(deck: DeckSpec) -> bytes:
    """Builds an in-memory OpenXML .pptx binary ZIP archive from a validated DeckSpec."""
    buf = io.BytesIO()
    slide_count = len(deck.slides)
    pres_xml, pres_rels = build_presentation_xml(slide_count)

    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml", build_content_types_xml(slide_count))
        zf.writestr(
            "_rels/.rels",
            f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="{REL_NS}">'
            f'<Relationship Id="rId1" Type="{R_NS}/officeDocument" Target="ppt/presentation.xml"/>'
            '<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/>'
            f'<Relationship Id="rId3" Type="{R_NS}/extended-properties" Target="docProps/app.xml"/></Relationships>',
        )
        zf.writestr(
            "docProps/core.xml",
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" '
            f'xmlns:dc="http://purl.org/dc/elements/1.1/"><dc:title>{xml_esc(deck.title)}</dc:title>'
            f"<dc:creator>{xml_esc(deck.author)}</dc:creator></cp:coreProperties>",
        )
        zf.writestr(
            "docProps/app.xml",
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties">'
            f"<Application>DeckForge MCP OpenXML Engine</Application><Slides>{slide_count}</Slides></Properties>",
        )
        zf.writestr("ppt/presentation.xml", pres_xml)
        zf.writestr("ppt/_rels/presentation.xml.rels", pres_rels)
        zf.writestr(
            "ppt/slideMasters/slideMaster1.xml",
            f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><p:sldMaster xmlns:a="{A_NS}" xmlns:r="{R_NS}" xmlns:p="{P_NS}">'
            '<p:cSld><p:spTree><p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr><p:grpSpPr/></p:spTree></p:cSld>'
            '<p:clrMap bg1="lt1" tx1="dk1" bg2="lt2" tx2="dk2" accent1="accent1" accent2="accent2" accent3="accent3" accent4="accent4" accent5="accent5" accent6="accent6" hlink="hlink" folHlink="folHlink"/>'
            '<p:sldLayoutIdLst><p:sldLayoutId id="2147483649" r:id="rId1"/></p:sldLayoutIdLst></p:sldMaster>',
        )
        zf.writestr(
            "ppt/slideMasters/_rels/slideMaster1.xml.rels",
            f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="{REL_NS}">'
            f'<Relationship Id="rId1" Type="{R_NS}/slideLayout" Target="../slideLayouts/slideLayout1.xml"/>'
            f'<Relationship Id="rId2" Type="{R_NS}/theme" Target="../theme/theme1.xml"/></Relationships>',
        )
        zf.writestr(
            "ppt/slideLayouts/slideLayout1.xml",
            f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><p:sldLayout xmlns:a="{A_NS}" xmlns:r="{R_NS}" xmlns:p="{P_NS}" type="blank">'
            '<p:cSld name="Blank"><p:spTree><p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr><p:grpSpPr/></p:spTree></p:cSld></p:sldLayout>',
        )
        zf.writestr(
            "ppt/slideLayouts/_rels/slideLayout1.xml.rels",
            f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="{REL_NS}">'
            f'<Relationship Id="rId1" Type="{R_NS}/slideMaster" Target="../slideMasters/slideMaster1.xml"/></Relationships>',
        )
        zf.writestr("ppt/theme/theme1.xml", build_theme_xml(deck.theme))

        for idx, slide in enumerate(deck.slides, 1):
            zf.writestr(f"ppt/slides/slide{idx}.xml", _build_slide_xml(slide, deck.theme, deck.title, deck.footer_label))
            zf.writestr(
                f"ppt/slides/_rels/slide{idx}.xml.rels",
                f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="{REL_NS}">'
                f'<Relationship Id="rId1" Type="{R_NS}/slideLayout" Target="../slideLayouts/slideLayout1.xml"/>'
                f'<Relationship Id="rId2" Type="{R_NS}/notesSlide" Target="../notesSlides/notesSlide{idx}.xml"/></Relationships>',
            )
            zf.writestr(f"ppt/notesSlides/notesSlide{idx}.xml", build_notes_xml(slide))
            zf.writestr(
                f"ppt/notesSlides/_rels/slide{idx}.xml.rels" if False else f"ppt/notesSlides/_rels/notesSlide{idx}.xml.rels",
                f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="{REL_NS}">'
                f'<Relationship Id="rId1" Type="{R_NS}/slide" Target="../slides/slide{idx}.xml"/></Relationships>',
            )

    return buf.getvalue()


_PPTX_DOWNLOAD_CACHE: Dict[str, bytes] = {}
PUBLIC_BASE_URL = "https://deckforge-mcp-production.up.railway.app"


def get_cached_pptx(filename: str) -> bytes | None:
    """Retrieves recently generated .pptx bytes by filename from bounded memory cache."""
    return _PPTX_DOWNLOAD_CACHE.get(filename)


def generate_editable_pptx(deck_spec: DeckSpec | Dict[str, Any]) -> Dict[str, Any]:
    """Validates DeckSpec and returns base64 .pptx archive, checksum, download URL, and OpenXML manifest."""
    parsed = deck_spec if isinstance(deck_spec, DeckSpec) else DeckSpec.model_validate(deck_spec)
    raw_bytes = build_pptx_bytes(parsed)
    sha256_hash = hashlib.sha256(raw_bytes).hexdigest()
    b64_payload = base64.b64encode(raw_bytes).decode("ascii")

    with zipfile.ZipFile(io.BytesIO(raw_bytes), "r") as zf:
        archive_entries = sorted(zf.namelist())

    safe_slug = "".join(c if c.isalnum() else "_" for c in parsed.title.lower()).strip("_")[:48]
    filename = f"{safe_slug or 'deckforge_executive_deck'}.pptx"
    if len(_PPTX_DOWNLOAD_CACHE) >= 30:
        _PPTX_DOWNLOAD_CACHE.pop(next(iter(_PPTX_DOWNLOAD_CACHE)), None)
    _PPTX_DOWNLOAD_CACHE[filename] = raw_bytes
    return {
        "status": "success",
        "filename": filename,
        "download_url": f"{PUBLIC_BASE_URL}/downloads/{filename}",
        "mime_type": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        "slide_count": len(parsed.slides),
        "file_size_bytes": len(raw_bytes),
        "sha256": sha256_hash,
        "openxml_entries_count": len(archive_entries),
        "openxml_entries": archive_entries,
        "compatibility": ["Microsoft PowerPoint", "Apple Keynote", "Google Slides"],
        "pptx_base64": b64_payload,
    }
