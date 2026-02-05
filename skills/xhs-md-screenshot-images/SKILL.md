---
name: xhs-md-screenshot-images
description: 将小红书文章Markdown渲染成HTML，再用截图方式批量导出图片（PNG/JPG）。适用“md转图片 / 渲染成html截图 / 小红书文章转图片”。
---

# XHS Markdown → HTML → Screenshot Images

把一篇小红书 Markdown 文章渲染成固定尺寸的 HTML 卡片，再用 Playwright（Chromium）截图导出图片。

## Quick Start

1) 安装依赖（一次性）

```bash
python3 -m pip install -U markdown-it-py mdit-py-plugins playwright
python3 -m playwright install chromium
```

如果无法下载 Chromium：
- 安装本机 Google Chrome（脚本会用 `channel=chrome`）
- 或重试 `python3 -m playwright install chromium`

2) 生成图片

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

```bash
python3 "${SKILL_DIR}/scripts/xhs_md_to_images.py" \
  xhs-img/body.md \
  --out xhs-img \
  --title "$(cat xhs-img/title.txt)"
```

## Splitting (拆页)

默认不做章节拆分：整篇作为一份正文，分页只由“自动分页”控制。

## Canvas (画布)

默认 3:4 比例（推荐）：
- `--width 1440 --height 1920`

也可自定义尺寸。

## Common Options

```bash
--title "自定义标题"        # 覆盖从 Markdown 里提取的标题
--device-scale 2           # 提高清晰度（相当于更高 DPR）
--format png|jpg           # 默认 png
--quality 85               # 仅 jpg 生效
--full-page                # 截图整个页面高度（不固定 3:4）
--no-paginate              # 关闭自动分页（会截断溢出内容）
--show-footer              # 显示页脚（默认不显示）
```

## Output

- `01.png`, `02.png`, ...
- `pages/01.html`, `pages/02.html`, ...

## Notes

- 相对路径图片会解析为本地 `file://...`。
- 标题从原始 Markdown 选取：优先 `## 标题建议`，否则用 H1；建议用 `--title` 明确指定。
- 默认自动分页，避免截断。
- 默认不显示页脚。
- 标题为“正文内容”的 section 不显示页眉标题。
- 默认不生成封面，标题仅在**第一页**显示，字号为正文的 **2.5x**。
