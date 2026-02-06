---
name: xhs-md-screenshot-images
description: 将小红书文章Markdown渲染成HTML，再用截图方式批量导出图片（PNG/JPG）。适用"md转图片 / 渲染成html截图 / 小红书文章转图片"。
---

# XHS Markdown → HTML → Screenshot Images

把一篇小红书 Markdown 文章渲染成固定尺寸的 HTML 卡片，再用 Playwright（Chromium）截图导出图片。

## 快速开始

（推荐）先从原始 Markdown 抽取“标题 + 纯正文”，避免把标题建议/标签/运营Tips 渲染进图片。

Step 0：设置 `SKILL_DIR`

- `SKILL_DIR` = 本文件（SKILL.md）所在目录

```bash
SKILL_DIR="/path/to/xhs-md-screenshot-images"
```

Step 1：创建输出目录

```bash
mkdir -p xhs-img
```

Step 2：复制原文到 `xhs-img/`

```bash
cp /path/to/article.md xhs-img/article.md
```

Step 3：抽取标题（写入 `xhs-img/title.txt`）

- 若原文有 `## 标题建议`：从候选里选一个最合适的
- 否则使用原文的 H1（`# ...`）

Step 4：抽取正文（写入 `xhs-img/body.md`）

- 正文范围：`## 正文内容` 下面到 `## 标签` 前面

Step 5：生成图片到 `xhs-img/`

1) 生成图片

```bash
npx -y bun ${SKILL_DIR}/scripts/md2image.ts xhs-img/body.md --title "文章标题" --out xhs-img
```

## 完整参数

```bash
npx -y bun ${SKILL_DIR}/scripts/md2image.ts <markdown-file> [options]

Options:
  --out <dir>           输出目录 (默认: xhs-img)
  --title <text>        文章标题
  --width <px>          单页宽度 (默认: 1440)
  --height <px>         单页高度 (默认: 1920, 3:4 比例)
  --device-scale <n>    设备像素比 (默认: 2)
  --format <png|jpg>    输出格式 (默认: png)
  --quality <n>         JPG 质量 (默认: 85)
  --max-pages <n>       最大页数预估 (默认: 20)
```

## Notes

- 相对路径图片会解析为本地 `file://...`。
- 标题从原始 Markdown 选取：优先 `## 标题建议`，否则用 H1；建议用 `--title` 明确指定。
- 默认自动分页，避免截断。
- 默认不显示页脚。
- 标题为“正文内容”的 section 不显示页眉标题。
- 默认不生成封面，标题仅在**第一页**显示，字号为正文的 **2.5x**。
