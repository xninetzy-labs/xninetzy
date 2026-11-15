from __future__ import annotations

from pathlib import Path
from typing import Any

from langchain_core.tools import tool

from xninetzy.core.paths import ArtifactPathError
from xninetzy.integrations.document_studio.errors import DocumentStudioError

ERRORS = (DocumentStudioError, ArtifactPathError, ValueError, OSError)
DECK_FORMATS = {"pptx", "slides_pdf"}
DECK_QUESTIONS = (
    "Purpose and audience of the deck",
    "Number of slides or talk length, and the language",
    "Reference: one of the owner's Canva designs, a new Canva design generated from the brief, "
    "a brand .pptx/.potx file, or a built-in theme",
)
CANVA_REFERENCE_FLOW = (
    "search-designs with the topic, then show titles and get-design-thumbnail images; the owner picks one",
    "or generate-design for a presentation, the owner picks a candidate, then create-design-from-candidate",
    "get-export-formats, then export-design as pptx and download it to UNTRACKED_OUTPUT_DIR/canva/<design_id>.pptx",
    "artifact_theme_from_file(path, name) then artifact_render(theme=name, deck_brief_confirmed=true), "
    "or template_path=<the .pptx> to keep the Canva layouts",
)


def _error(exc: Exception) -> dict[str, Any]:
    return {"status": "error", "error": type(exc).__name__, "message": str(exc)}


def _deck_brief(wanted: set[str]) -> dict[str, Any]:
    from xninetzy.integrations.document_studio import themes

    try:
        names = [item["name"] for item in themes.list_themes()]
    except ERRORS:
        names = []
    return {
        "status": "awaiting_input",
        "rendered": False,
        "formats": sorted(wanted),
        "reason": "A deck starts with the owner's brief and a chosen reference; ask before rendering.",
        "ask_owner": list(DECK_QUESTIONS),
        "canva_reference_flow": list(CANVA_REFERENCE_FLOW),
        "canva_unavailable": "Say the Canva MCP is not connected or needs login, then offer a brand file or a built-in theme.",
        "themes": names,
        "next_call": "artifact_render with the same arguments plus deck_brief_confirmed=true once the owner has answered",
    }


@tool(description=(
    "Render Markdown into themed DOCX, PDF, PPTX and slide-PDF files in one call, with cover, table of contents, "
    "page numbers, styled tables, figures, auto-fit slides, previews and QA. Write content once: YAML front matter "
    "(title, subtitle, author, student_id, course, lecturer, program, faculty, institution, date, theme) then Markdown. "
    "Decks split on '---' lines or else at H1/H2; '|||' splits two columns; 'Notes:' lines become speaker notes; "
    "'Tabel:'/'Table:' before a table is its caption; '\\pagebreak' forces a page break. "
    "formats: docx, pdf, pptx, slides_pdf. template_path may be a .docx/.dotx or .pptx/.potx brand template. "
    "Decks (pptx, slides_pdf) first return awaiting_input with the questions to ask the owner (purpose, audience, "
    "length, reference from Canva, a brand file or a theme); call again with deck_brief_confirmed=true after the "
    "owner answers. Writes under GENERATED_DOCUMENTS_DIR; inspect the returned contact sheets before delivering."
))
def artifact_render(
    markdown: str = "",
    source_path: str = "",
    formats: list[str] | None = None,
    theme: str = "",
    output_name: str = "",
    template_path: str = "",
    preview_pages: int = 8,
    deck_brief_confirmed: bool = False,
) -> dict[str, Any]:
    from xninetzy.integrations.document_studio import studio

    deck = {str(item).lower() for item in (formats or [])} & DECK_FORMATS
    if deck and not deck_brief_confirmed:
        return _deck_brief(deck)
    try:
        return studio.render(
            markdown=markdown,
            source_path=source_path,
            formats=formats,
            theme=theme,
            output_name=output_name,
            template_path=template_path,
            preview_pages=max(1, min(int(preview_pages), 30)),
        )
    except ERRORS as exc:
        return _error(exc)


@tool(description="Render PNG page previews and a contact sheet for a .pdf, .docx or .pptx file so its layout can be inspected.")
def artifact_preview(path: str, max_pages: int = 12) -> dict[str, Any]:
    from xninetzy.integrations.document_studio import studio

    try:
        return {"status": "ok", **studio.preview(path, max(1, min(int(max_pages), 40)))}
    except ERRORS as exc:
        return _error(exc)


@tool(description="Validate a .docx, .pptx or .pdf: heading hierarchy, unrendered Markdown, shapes past slide edges, empty slides, substituted fonts.")
def artifact_validate(path: str, expected_fonts: list[str] | None = None) -> dict[str, Any]:
    from xninetzy.integrations.document_studio import qa

    try:
        return qa.check(Path(path).expanduser().resolve(), expected_fonts or [])
    except ERRORS as exc:
        return _error(exc)


@tool(description="List document and deck themes (built-in and owner-saved) available to artifact_render.")
def artifact_theme_list() -> dict[str, Any]:
    from xninetzy.integrations.document_studio import themes

    try:
        return {"status": "ok", "themes": themes.list_themes()}
    except ERRORS as exc:
        return _error(exc)


@tool(description="Show the full settings of one theme: fonts, sizes, colors, page, document and deck options.")
def artifact_theme_get(name: str) -> dict[str, Any]:
    from xninetzy.integrations.document_studio import themes

    try:
        return {"status": "ok", "theme": themes.load_theme(name).model_dump()}
    except ERRORS as exc:
        return _error(exc)


@tool(description=(
    "Save a reusable owner theme by overriding fields of a base theme, e.g. {'colors': {'accent': '#C0392B'}, "
    "'fonts': {'heading': 'Georgia'}, 'document': {'toc': true}}. Idempotent for the same name and content."
))
def artifact_theme_save(name: str, overrides: dict[str, Any], base: str = "professional") -> dict[str, Any]:
    from xninetzy.integrations.document_studio import themes

    try:
        theme, path = themes.save_theme(name, overrides, base)
        return {"status": "ok", "theme": theme.name, "path": str(path)}
    except ERRORS as exc:
        return _error(exc)


@tool(description=(
    "Create a theme from an existing .pptx/.potx/.docx/.dotx, such as a Canva PowerPoint export or a brand template: "
    "samples the colors and fonts actually used, fixes unreadable contrast, falls back to Arial for fonts not installed "
    "(keep_fonts keeps them), and saves it under `name` when save is true."
))
def artifact_theme_from_file(
    path: str,
    name: str,
    base: str = "professional",
    keep_fonts: bool = False,
    save: bool = True,
) -> dict[str, Any]:
    from xninetzy.integrations.document_studio import themes
    from xninetzy.integrations.document_studio.theme_extract import extract_theme

    try:
        overrides, evidence = extract_theme(Path(path).expanduser().resolve(), keep_fonts=keep_fonts)
        result: dict[str, Any] = {"status": "ok", "overrides": overrides, "evidence": evidence}
        if save:
            theme, saved = themes.save_theme(name, {**overrides, "description": f"Extracted from {Path(path).name}"}, base)
            result.update({"theme": theme.name, "path": str(saved)})
        return result
    except ERRORS as exc:
        return _error(exc)


DOCUMENT_STUDIO_TOOLS = [
    artifact_render,
    artifact_preview,
    artifact_validate,
    artifact_theme_list,
    artifact_theme_get,
    artifact_theme_save,
    artifact_theme_from_file,
]
