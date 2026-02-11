---
name: xhs-md2img
description: 将Markdown批量导出固定尺寸的小红书长文图片。适用"md转图片/转小红书长文图"。
---

# Markdown to XHS Images

Convert a Markdown article into fixed-size Xiaohongshu (小红书) long-form images.

## Usage

```bash
/xhs-md2img posts/turing-story/source.md
```

## Script Directory

**Important**: All scripts are located in the `scripts/` subdirectory of this skill.

**Agent Execution Instructions**:
1. Determine this SKILL.md file's directory path as `SKILL_DIR`
2. Script path = `${SKILL_DIR}/scripts/<script-name>.ts`
3. Replace all `${SKILL_DIR}` in this document with the actual path

**Script Reference**:
| Script | Purpose |
|--------|---------|
| `scripts/md2image.ts` | Main script to convert Markdown to images |

## File Structure

Output directory: `xhs-img/{topic-slug}/`
- Slug: 2-4 words kebab-case from topic (e.g., `alan-turing-bio`)
- Conflict: append timestamp (e.g., `turing-story-20260118-143052`)

**Contents**:
| File | Description |
|------|-------------|
| `source.{ext}` | Source files |
| `pages/temp.html` | Temporary HTML file for rendering |
| `NN-page.png` | Generated images |


## Workflow

### Progress Checklist

```
Comic Progress:
- [ ] Step 1: Check existing
- [ ] Step 2: Generate images
- [ ] Step 3: Completion report
```
### Step Summary

| Step | Action | Key Output |
|------|--------|------------|
| 1 | Check existing directory | Handle conflicts |
| **2** | Generate images | `NN-page.png` |
| 3 | Completion report | Summary |

### Step 2: Image Generation ⚠️ CRITICAL

```bash
# Basic (render directly from the original Markdown)
npx -y bun ${SKILL_DIR}/scripts/md2image.ts article.md \
  --out xhs-img/${TOPIC_SLUG} \
  --width 1440 --height 1920 \
  --device-scale 2 \
```

## Options

| Option | Description |
|--------|-------------|
| `<markdown-file>` | Input Markdown file path (required) |
| `--out <dir>` | Output directory (default: `xhs-img`). Supports nested paths like `xhs-img/<topic-slug>` |
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
