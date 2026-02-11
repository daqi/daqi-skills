---
name: xhs-md2img
description: 将Markdown批量导出固定尺寸的小红书长文图片。适用"md转图片/转小红书长文图"。
---

# Markdown to XHS Images (Playwright)

Convert a Markdown article into fixed-size Xiaohongshu (小红书) long-form images.

Implementation highlights:
- CSS multi-column auto-pagination (no manual page breaks)
- Playwright screenshot per column (exact `clip`)
- Auto-detect actual page count by rendered content width

## Script Directory

**Agent Execution**:
1. `SKILL_DIR` = this SKILL.md file's directory
2. Script path = `${SKILL_DIR}/scripts/md2image.ts`

## Usage

```bash
# Basic (render directly from the original Markdown)
npx -y bun ${SKILL_DIR}/scripts/md2image.ts article.md --out xhs-img

# Custom canvas size
npx -y bun ${SKILL_DIR}/scripts/md2image.ts article.md --out xhs-img --width 1440 --height 1920

# Higher device scale (sharper text, larger files)
npx -y bun ${SKILL_DIR}/scripts/md2image.ts article.md --out xhs-img --device-scale 2
```

## File Structure

Each session creates an independent directory named by content slug:

```
xhs-img/{topic-slug}/
├── pages
│   └── temp.html
├── source.{ext}             # Source files (text, images, etc.)
├── 01-page.png
├── 02-page.png
└── NN-page.png
```

## Options

| Option | Description |
|--------|-------------|
| `<markdown-file>` | Input Markdown file path (required) |
| `--out <dir>` | Output directory (default: `xhs-img`). Supports nested paths like `xhs-img/<slug>` |
| `--width <px>` | Single-page width (default: `1440`) |
| `--height <px>` | Single-page height (default: `1920`, 3:4) |
| `--device-scale <n>` | Device scale factor / DPR (default: `2`) |

## Environment Variables

| Variable | Description |
|----------|-------------|
| (none) | No environment variables are required by this skill |

**Load Priority**: CLI args > defaults

## Browser Selection

1. If a system browser is found (Chrome/Edge/Chromium by OS-specific known paths) → launch it via Playwright `executablePath`
2. Otherwise → use Playwright bundled Chromium

## Pagination & Output

- Auto pagination: content flows into CSS columns (`column-width = page width`, `column-gap = 0`)
- Page count: computed from rendered content’s maximum right edge
- Screenshot: one image per page via `clip: { x: pageIndex * width, y: 0, width, height }`

## Rendering Notes

- Relative images in Markdown are rewritten to absolute `file://...` URLs
- Horizontal rules (`---`) are not rendered (treated as semantic separators but visually noisy)


## Error Handling

- Missing Markdown file → exit with error
- Browser not found → fallback to Playwright Chromium
