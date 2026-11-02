"""
ECMA-376 OpenXML Package Parts & Boilerplate Templates for DeckForge MCP (.pptx).
Provides [Content_Types].xml, presentation.xml, slideMaster, slideLayout, theme, and notesSlide XML builders.
"""

from __future__ import annotations

from typing import List
from xml.sax.saxutils import escape

from src.models import SlideSpec, ThemePalette

P_NS = "http://schemas.openxmlformats.org/presentationml/2006/main"
A_NS = "http://schemas.openxmlformats.org/drawingml/2006/main"
R_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"


def hex_clean(color: str) -> str:
    return color.lstrip("#").upper()


def xml_esc(text: str) -> str:
    return escape(str(text or ""), {'"': "&quot;", "'": "&apos;"})


def build_notes_xml(slide: SlideSpec) -> str:
    notes_text = slide.speaker_notes or f"Speaker notes for Slide {slide.slide_number}: {slide.action_title}"
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        f'<p:notes xmlns:a="{A_NS}" xmlns:r="{R_NS}" xmlns:p="{P_NS}">'
        "<p:cSld><p:spTree>"
        '<p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr>'
        "<p:grpSpPr/>"
        "<p:sp>"
        '<p:nvSpPr><p:cNvPr id="2" name="NotesBody"/><p:cNvSpPr/><p:nvPr><p:ph type="body" idx="1"/></p:nvPr></p:nvSpPr>'
        "<p:spPr/>"
        f'<p:txBody><a:bodyPr/><a:lstStyle/><a:p><a:r><a:rPr lang="en-US" sz="1200"/><a:t>{xml_esc(notes_text)}</a:t></a:r></a:p></p:txBody>'
        "</p:sp>"
        "</p:spTree></p:cSld></p:notes>"
    )


def build_content_types_xml(slide_count: int) -> str:
    overrides = [
        '<Override PartName="/ppt/presentation.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.presentation.main+xml"/>',
        '<Override PartName="/ppt/slideMasters/slideMaster1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slideMaster+xml"/>',
        '<Override PartName="/ppt/slideLayouts/slideLayout1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slideLayout+xml"/>',
        '<Override PartName="/ppt/theme/theme1.xml" ContentType="application/vnd.openxmlformats-officedocument.theme+xml"/>',
        '<Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>',
        '<Override PartName="/docProps/app.xml" ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/>',
    ]
    for i in range(1, slide_count + 1):
        overrides.append(
            f'<Override PartName="/ppt/slides/slide{i}.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slide+xml"/>'
        )
        overrides.append(
            f'<Override PartName="/ppt/notesSlides/notesSlide{i}.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.notesSlide+xml"/>'
        )
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        f"{''.join(overrides)}</Types>"
    )


def build_presentation_xml(slide_count: int) -> tuple[str, str]:
    sld_ids: List[str] = []
    rels: List[str] = [
        f'<Relationship Id="rId1" Type="{R_NS}/slideMaster" Target="slideMasters/slideMaster1.xml"/>',
        f'<Relationship Id="rId2" Type="{R_NS}/theme" Target="theme/theme1.xml"/>',
    ]
    for i in range(1, slide_count + 1):
        rid = f"rId{i + 2}"
        sld_id = 255 + i
        sld_ids.append(f'<p:sldId id="{sld_id}" r:id="{rid}"/>')
        rels.append(f'<Relationship Id="{rid}" Type="{R_NS}/slide" Target="slides/slide{i}.xml"/>')

    pres_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        f'<p:presentation xmlns:a="{A_NS}" xmlns:r="{R_NS}" xmlns:p="{P_NS}">'
        '<p:sldMasterIdLst><p:sldMasterId id="2147483648" r:id="rId1"/></p:sldMasterIdLst>'
        f"<p:sldIdLst>{''.join(sld_ids)}</p:sldIdLst>"
        '<p:sldSz cx="12192000" cy="6858000" type="screen16x9"/>'
        '<p:notesSz cx="6858000" cy="9144000"/>'
        "</p:presentation>"
    )
    pres_rels = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        f'<Relationships xmlns="{REL_NS}">{"".join(rels)}</Relationships>'
    )
    return pres_xml, pres_rels


def build_theme_xml(theme: ThemePalette) -> str:
    return (
        f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><a:theme xmlns:a="{A_NS}" name="{xml_esc(theme.name)}">'
        '<a:themeElements><a:clrScheme name="DeckForge"><a:dk1><a:srgbClr val="0F172A"/></a:dk1>'
        '<a:lt1><a:srgbClr val="FFFFFF"/></a:lt1>'
        f'<a:accent1><a:srgbClr val="{hex_clean(theme.primary_hex)}"/></a:accent1>'
        f'<a:accent2><a:srgbClr val="{hex_clean(theme.secondary_hex)}"/></a:accent2>'
        "</a:clrScheme></a:themeElements></a:theme>"
    )
