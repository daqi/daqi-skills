#!/usr/bin/env python3

from __future__ import annotations

import argparse
import math
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional, Tuple


DEFAULT_CANVAS_WIDTH = 1440
DEFAULT_CANVAS_HEIGHT = 1920
DEFAULT_PADDING = 80
DEFAULT_GAP = 28
DEFAULT_BODY_FONT_PX = 50
DEFAULT_LINE_HEIGHT = 1.9
DEFAULT_PARAGRAPH_GAP_PX = 40
DEFAULT_TITLE_SCALE = 2.5
DEFAULT_TITLE_GAP_PX = 30


def _eprint(*args: object) -> None:
    print(*args, file=sys.stderr)


def _require_deps() -> None:
    missing: List[str] = []
    try:
        from markdown_it import MarkdownIt  # noqa: F401
    except Exception:
        missing.append("markdown-it-py")
    try:
        from mdit_py_plugins.footnote import footnote_plugin  # noqa: F401
    except Exception:
        missing.append("mdit-py-plugins")
    try:
        import playwright  # noqa: F401
        from playwright.sync_api import sync_playwright  # noqa: F401
    except Exception:
        missing.append("playwright")

    if missing:
        _eprint("Missing dependencies:", ", ".join(missing))
        _eprint("Install:")
        _eprint("  python3 -m pip install -U markdown-it-py mdit-py-plugins playwright")
        _eprint("  python3 -m playwright install chromium")
        raise SystemExit(2)


@dataclass
class PageSpec:
    index: int
    title: str
    markdown: str


@dataclass
class RenderedSection:
    index: int
    title: str
    body_html: str


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _parse_extend_value(raw: str) -> Optional[object]:
    value = raw.strip()
    if not value:
        return None
    lower = value.lower()
    if lower in {"true", "false"}:
        return lower == "true"
    try:
        if "." in value:
            return float(value)
        return int(value)
    except ValueError:
        return value


def _load_extend_prefs() -> dict:
    paths = [
        Path(".daqi-skills/xhs-md-screenshot-images/EXTEND.md"),
        Path.home() / ".daqi-skills/xhs-md-screenshot-images/EXTEND.md",
    ]
    for path in paths:
        if path.exists():
            prefs: dict = {}
            for line in _read_text(path).splitlines():
                if not line.strip() or line.strip().startswith("#"):
                    continue
                if ":" not in line:
                    continue
                key, raw = line.split(":", 1)
                value = _parse_extend_value(raw)
                if value is not None:
                    prefs[key.strip()] = value
            return prefs
    return {}


def _extract_title(md: str, fallback: str = "") -> str:
    for line in md.splitlines():
        m = re.match(r"^#\s+(.+?)\s*$", line)
        if m:
            return m.group(1).strip()
    return fallback


def _ensure_out_dir(out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "pages").mkdir(parents=True, exist_ok=True)


def _slugify(name: str) -> str:
    name = name.strip().lower()
    name = re.sub(r"\s+", "-", name)
    name = re.sub(r"[^a-z0-9\u4e00-\u9fff\-]+", "", name)
    name = re.sub(r"\-+", "-", name).strip("-")
    return name or "xhs"


def _resolve_local_image_srcs(html: str, md_path: Path) -> str:
    # Convert src="relative/path" to file:// absolute path.
    def repl(m: re.Match[str]) -> str:
        src = m.group(1)
        if re.match(r"^(https?:)?//", src) or src.startswith("data:") or src.startswith("file:"):
            return m.group(0)
        abs_path = (md_path.parent / src).resolve()
        return f'src="file://{abs_path.as_posix()}"'

    return re.sub(r'src="([^"]+)"', repl, html)


def _render_body_html(page: PageSpec, md_path: Path) -> str:
    from markdown_it import MarkdownIt
    from mdit_py_plugins.footnote import footnote_plugin

    md = MarkdownIt("commonmark", {"html": False, "linkify": True, "typographer": True}).use(
        footnote_plugin
    )

    # Do not render horizontal rules. In XHS long-text screenshots, `---` is often
    # used as a semantic separator but the line is visually distracting.
    md.renderer.rules["hr"] = lambda *args, **kwargs: ""

    body_html = md.render(page.markdown)
    return _resolve_local_image_srcs(body_html, md_path)


def _render_html_from_body(
    *,
    title: str,
    doc_title: str,
    body_html: str,
    width: int,
    height: int,
    page_no: str,
    clamp_lines: Optional[int],
    show_footer: bool,
    show_header: bool,
    header_override: Optional[str],
    padding_px: int,
    gap_px: int,
    content_font_px: float,
    line_height: float,
    paragraph_gap_px: float,
    title_scale: float,
    title_gap_px: float,
) -> str:
    header_text = ""
    if show_header:
        header_text = (header_override or title).strip() or doc_title.strip()
        # Common XHS template: the first H2 is literally "正文内容"; don't show it.
        if header_text.strip() == "正文内容":
            header_text = ""

    content_display_css = "display: block;"
    clamp_css = ""
    if clamp_lines is not None:
        content_display_css = "display: -webkit-box; -webkit-box-orient: vertical;"
        clamp_css = f"-webkit-line-clamp: {clamp_lines};"

    grid_rows: List[str] = []
    if header_text:
        grid_rows.append("auto")
    grid_rows.append("1fr")
    if show_footer:
        grid_rows.append("auto")

    css = f"""
:root {{
    --canvas-w: {width}px;
    --canvas-h: {height}px;
    --pad: {padding_px}px;
    --gap: {gap_px}px;
    --content-font: {content_font_px}px;
    --title-scale: {title_scale};
    --title-gap: {title_gap_px}px;
    --font: -apple-system, BlinkMacSystemFont, \"Segoe UI\", \"PingFang SC\", \"Hiragino Sans GB\", \"Microsoft YaHei\", Arial, sans-serif;
}}
* {{ box-sizing: border-box; }}
html, body {{ margin: 0; padding: 0; background: #fff; }}
body {{ font-family: var(--font); }}

.canvas {{
    width: var(--canvas-w);
    height: var(--canvas-h);
    padding: var(--pad);
    overflow: hidden;
    display: grid;
    grid-template-rows: {" ".join(grid_rows)};
    gap: var(--gap);
}}

.header {{
    font-size: calc(var(--content-font) * var(--title-scale));
    font-weight: 800;
    line-height: 1.15;
    word-break: break-word;
    margin-bottom: var(--title-gap);
}}

.content {{
    font-size: var(--content-font);
    line-height: {line_height};
    font-weight: 400;
    word-break: break-word;
    overflow: hidden;
    {content_display_css}
    {clamp_css}
}}

.content p {{ margin: 0 0 {paragraph_gap_px}px; }}
.content strong {{ font-weight: 800; }}
.content em {{ font-style: italic; }}
.content ul, .content ol {{ margin: 0 0 {paragraph_gap_px}px 1.2em; padding: 0; }}
.content li {{ margin: 8px 0; }}
.content blockquote {{
    margin: 0 0 {paragraph_gap_px}px;
    padding: 12px 0 12px 20px;
    border-left: 6px solid #111;
}}
.content code {{
    font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, \"Liberation Mono\", \"Courier New\", monospace;
    font-size: 0.95em;
}}
.content a {{ color: inherit; text-decoration: underline; }}
.content img {{ max-width: 100%; height: auto; display: block; }}

.footer {{
    font-size: 24px;
    line-height: 1.2;
    color: #111;
    opacity: 0.55;
    display: flex;
    justify-content: space-between;
    gap: 12px;
}}
"""

    header_html = f"<div class=\"header\">{_escape_html(header_text)}</div>" if header_text else ""
    footer_html = (
        f"<div class=\"footer\"><span>{_escape_html(doc_title)}</span><span>{_escape_html(page_no)}</span></div>"
        if show_footer
        else ""
    )

    html = f"""<!doctype html>
<html lang=\"zh-CN\">
    <head>
        <meta charset=\"utf-8\" />
        <meta name=\"viewport\" content=\"width={width}, height={height}, initial-scale=1\" />
        <title>{_escape_html(doc_title or header_text or "XHS")}</title>
        <style>{css}</style>
    </head>
    <body>
        <main class=\"canvas\" id=\"canvas\">
            {header_html}
            <div class=\"content\" id=\"content\">{body_html}</div>
            {footer_html}
        </main>
    </body>
</html>"""

    return html


def _escape_html(s: str) -> str:
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#39;")
    )


def _write_page_html(out_dir: Path, page: PageSpec, html: str) -> Path:
    page_path = out_dir / "pages" / f"{page.index:02d}.html"
    page_path.write_text(html, encoding="utf-8")
    return page_path


def _paginate_in_browser(
    section_html_path: Path,
    *,
    width: int,
    height: int,
    device_scale: float,
) -> List[str]:
    """Return a list of HTML chunks (innerHTML) for #content, paginated by actual render height."""

    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = None
        launch_errors: List[str] = []
        try:
            browser = p.chromium.launch()
        except Exception as e:  # noqa: BLE001
            launch_errors.append(f"chromium.launch(): {e}")
        if browser is None:
            try:
                browser = p.chromium.launch(channel="chrome")
            except Exception as e:  # noqa: BLE001
                launch_errors.append(f"chromium.launch(channel=chrome): {e}")
        if browser is None and sys.platform == "darwin":
            chrome_path = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
            if os.path.exists(chrome_path):
                try:
                    browser = p.chromium.launch(executable_path=chrome_path)
                except Exception as e:  # noqa: BLE001
                    launch_errors.append(f"chromium.launch(executable_path=Chrome): {e}")
        if browser is None:
            _eprint("Failed to launch a browser via Playwright (pagination step).")
            for err in launch_errors:
                _eprint("-", err)
            raise SystemExit(2)

        context = browser.new_context(
            viewport={"width": width, "height": height},
            device_scale_factor=device_scale,
        )
        page = context.new_page()
        page.goto(section_html_path.resolve().as_uri(), wait_until="networkidle")

        chunks: List[str] = page.evaluate(
            """() => {
              const content = document.querySelector('#content');
              if (!content) return [];

              // Clone nodes to avoid layout thrash on originals.
              const nodes = Array.from(content.children).map(n => n.cloneNode(true));
              content.innerHTML = '';

              const maxH = content.clientHeight;
              const pages = [];

              let current = document.createElement('div');
              current.style.display = 'block';
              content.appendChild(current);

              const fits = () => current.scrollHeight <= maxH + 1;

              for (const node of nodes) {
                current.appendChild(node);
                if (fits()) continue;

                // If single node is too big, keep it alone (avoid infinite loop).
                current.removeChild(node);
                if (current.children.length === 0) {
                  current.appendChild(node);
                  pages.push(current.innerHTML);
                  current.innerHTML = '';
                  continue;
                }

                pages.push(current.innerHTML);
                current.innerHTML = '';
                current.appendChild(node);

                if (!fits()) {
                  pages.push(current.innerHTML);
                  current.innerHTML = '';
                }
              }

              if (current.children.length) pages.push(current.innerHTML);
              return pages;
            }"""
        )

        context.close()
        browser.close()

    return [c for c in chunks if str(c).strip()]


def _screenshot_pages(
    out_dir: Path,
    page_html_paths: List[Path],
    *,
    width: int,
    height: int,
    device_scale: float,
    img_format: str,
    quality: int,
    full_page: bool,
) -> None:
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = None
        launch_errors: List[str] = []
        # 1) Prefer Playwright-managed Chromium (best compatibility)
        try:
            browser = p.chromium.launch()
        except Exception as e:  # noqa: BLE001
            launch_errors.append(f"chromium.launch(): {e}")

        # 2) Fallback to system Chrome channel (avoids downloading browsers)
        if browser is None:
            try:
                browser = p.chromium.launch(channel="chrome")
            except Exception as e:  # noqa: BLE001
                launch_errors.append(f"chromium.launch(channel=chrome): {e}")

        # 3) Fallback to well-known Chrome path on macOS
        if browser is None and sys.platform == "darwin":
            chrome_path = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
            if os.path.exists(chrome_path):
                try:
                    browser = p.chromium.launch(executable_path=chrome_path)
                except Exception as e:  # noqa: BLE001
                    launch_errors.append(f"chromium.launch(executable_path=Chrome): {e}")

        if browser is None:
            _eprint("Failed to launch a browser via Playwright.")
            for err in launch_errors:
                _eprint("-", err)
            _eprint("\nFix options:")
            _eprint("1) Install Playwright browsers:")
            _eprint("   python3 -m playwright install chromium")
            _eprint("2) Or install Google Chrome and retry (script will use channel=chrome).")
            raise SystemExit(2)
        context = browser.new_context(
            viewport={"width": width, "height": height},
            device_scale_factor=device_scale,
        )
        page = context.new_page()

        for i, html_path in enumerate(page_html_paths, start=1):
            url = html_path.resolve().as_uri()
            page.goto(url, wait_until="networkidle")

            # Prefer clipping to the fixed canvas if not full-page.
            clip = None
            if not full_page:
                canvas = page.locator("#canvas")
                box = canvas.bounding_box()
                if box:
                    clip = {
                        "x": math.floor(box["x"]),
                        "y": math.floor(box["y"]),
                        "width": math.floor(box["width"]),
                        "height": math.floor(box["height"]),
                    }

            out_path = out_dir / f"{i:02d}.{img_format}"
            if img_format == "png":
                page.screenshot(path=str(out_path), full_page=full_page, clip=clip)
            else:
                page.screenshot(
                    path=str(out_path),
                    full_page=full_page,
                    clip=clip,
                    type="jpeg",
                    quality=quality,
                )

        context.close()
        browser.close()


def main(argv: Optional[List[str]] = None) -> int:
    raw_argv = argv if argv is not None else sys.argv[1:]
    parser = argparse.ArgumentParser(description="Render XHS Markdown to HTML pages and screenshot them.")
    parser.add_argument("md", type=str, help="Path to markdown file")
    parser.add_argument("--out", type=str, default="xhs-md-images", help="Output directory")
    parser.add_argument("--title", type=str, default="", help="Override document title")
    # Default to XHS-friendly 3:5 canvas.
    parser.add_argument("--width", type=int, default=DEFAULT_CANVAS_WIDTH)
    parser.add_argument("--height", type=int, default=DEFAULT_CANVAS_HEIGHT)
    parser.add_argument("--device-scale", type=float, default=2.0)
    parser.add_argument("--format", choices=["png", "jpg"], default="png")
    parser.add_argument("--quality", type=int, default=85, help="JPG quality")
    parser.add_argument("--full-page", action="store_true", help="Screenshot full page height")
    parser.add_argument("--show-footer", action="store_true", help="Render footer (default: off)")
    paginate_group = parser.add_mutually_exclusive_group()
    paginate_group.add_argument("--paginate", dest="paginate", action="store_true", help="Auto paginate to avoid truncation (default)")
    paginate_group.add_argument("--no-paginate", dest="paginate", action="store_false", help="Disable pagination and clamp content")
    parser.set_defaults(paginate=True)

    args = parser.parse_args(raw_argv)

    _require_deps()

    md_path = Path(args.md).expanduser().resolve()
    if not md_path.exists():
        _eprint("Markdown file not found:", md_path)
        return 2

    out_dir = Path(args.out).expanduser().resolve()
    _ensure_out_dir(out_dir)

    md_text = _read_text(md_path)
    doc_title = args.title.strip() or _extract_title(md_text, fallback=md_path.stem)

    prefs = _load_extend_prefs()
    if "canvas_width" in prefs and "--width" not in raw_argv:
        args.width = int(prefs["canvas_width"])
    if "canvas_height" in prefs and "--height" not in raw_argv:
        args.height = int(prefs["canvas_height"])
    if "show_footer" in prefs and "--show-footer" not in raw_argv:
        args.show_footer = bool(prefs["show_footer"])

    padding_px = int(prefs.get("padding", DEFAULT_PADDING))
    gap_px = int(prefs.get("gap", DEFAULT_GAP))
    content_font_px = float(prefs.get("body_font_px", DEFAULT_BODY_FONT_PX))
    line_height = float(prefs.get("line_height", DEFAULT_LINE_HEIGHT))
    paragraph_gap_px = float(prefs.get("paragraph_gap_px", DEFAULT_PARAGRAPH_GAP_PX))
    title_scale = float(prefs.get("title_scale", DEFAULT_TITLE_SCALE))
    title_gap_px = float(prefs.get("title_gap_px", DEFAULT_TITLE_GAP_PX))

    pages = [PageSpec(index=1, title=doc_title, markdown=md_text.strip())]

    # Render sections to HTML, then optionally paginate by real DOM height.
    rendered_sections: List[RenderedSection] = []
    for page_spec in pages:
        rendered_sections.append(
            RenderedSection(
                index=page_spec.index,
                title=page_spec.title.strip() or doc_title,
                body_html=_render_body_html(page_spec, md_path),
            )
        )

    page_html_paths: List[Path] = []
    image_no = 0

    for section in rendered_sections:
        # If full-page screenshots are requested, pagination isn't needed.
        do_paginate = args.paginate and not args.full_page
        clamp_lines = None if do_paginate else 18

        # First write a temporary section HTML to allow DOM-based pagination.
        image_no += 1
        show_header = image_no == 1
        section_html = _render_html_from_body(
            title=section.title,
            doc_title=doc_title,
            body_html=section.body_html,
            width=args.width,
            height=args.height,
            page_no=f"{image_no}",
            clamp_lines=clamp_lines,
            show_footer=bool(args.show_footer),
            show_header=show_header,
            header_override=doc_title,
            padding_px=padding_px,
            gap_px=gap_px,
            content_font_px=content_font_px,
            line_height=line_height,
            paragraph_gap_px=paragraph_gap_px,
            title_scale=title_scale,
            title_gap_px=title_gap_px,
        )
        section_page = PageSpec(index=image_no, title=section.title, markdown="")
        section_html_path = _write_page_html(out_dir, section_page, section_html)

        if not do_paginate:
            page_html_paths.append(section_html_path)
            continue

        chunks = _paginate_in_browser(
            section_html_path,
            width=args.width,
            height=args.height,
            device_scale=args.device_scale,
        )

        # Replace the temporary section page with paginated pages.
        # Keep numbering globally increasing.
        # First chunk reuses current image_no; subsequent chunks allocate new numbers.
        if not chunks:
            page_html_paths.append(section_html_path)
            continue

        # Overwrite the first page with the first chunk.
        first_html = _render_html_from_body(
            title=section.title,
            doc_title=doc_title,
            body_html=chunks[0],
            width=args.width,
            height=args.height,
            page_no=f"{image_no}",
            clamp_lines=None,
            show_footer=bool(args.show_footer),
            show_header=show_header,
            header_override=doc_title,
            padding_px=padding_px,
            gap_px=gap_px,
            content_font_px=content_font_px,
            line_height=line_height,
            paragraph_gap_px=paragraph_gap_px,
            title_scale=title_scale,
            title_gap_px=title_gap_px,
        )
        section_html_path.write_text(first_html, encoding="utf-8")
        page_html_paths.append(section_html_path)

        for chunk in chunks[1:]:
            image_no += 1
            html = _render_html_from_body(
                title=section.title,
                doc_title=doc_title,
                body_html=chunk,
                width=args.width,
                height=args.height,
                page_no=f"{image_no}",
                clamp_lines=None,
                show_footer=bool(args.show_footer),
                show_header=False,
                header_override=None,
                padding_px=padding_px,
                gap_px=gap_px,
                content_font_px=content_font_px,
                line_height=line_height,
                paragraph_gap_px=paragraph_gap_px,
                title_scale=title_scale,
                title_gap_px=title_gap_px,
            )
            page_spec = PageSpec(index=image_no, title=section.title, markdown="")
            page_html_paths.append(_write_page_html(out_dir, page_spec, html))

    _screenshot_pages(
        out_dir,
        page_html_paths,
        width=args.width,
        height=args.height,
        device_scale=args.device_scale,
        img_format=args.format,
        quality=args.quality,
        full_page=args.full_page,
    )

    print(str(out_dir))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
