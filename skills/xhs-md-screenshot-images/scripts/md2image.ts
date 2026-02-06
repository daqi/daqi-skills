#!/usr/bin/env node

/**
 * Markdown to Images with CSS Multi-column Auto-pagination
 *
 * 使用 CSS columns 属性实现自动分页：
 * 1. 创建宽度为 W × N 的容器（N 是预估页数）
 * 2. 设置 column-width: W 和 column-gap: 0
 * 3. 内容自动流式布局到多列
 * 4. 通过移动视口截取每一页
 */

import fs from 'node:fs';
import path from 'node:path';
import { chromium } from 'playwright';
import MarkdownIt from 'markdown-it';

// 默认配置
const DEFAULT_CONFIG = {
  width: 1440,           // 单页宽度
  height: 1920,          // 单页高度 (3:4 比例)
  padding: 80,           // 内边距
  gap: 28,               // 元素间距
  bodyFontPx: 50,        // 正文字号
  lineHeight: 1.9,       // 行高
  paragraphGap: 40,      // 段落间距
  titleScale: 2.5,       // 标题字号倍数
  titleGap: 30,          // 标题下方间距
  deviceScale: 2,        // 设备像素比
  format: 'png',         // 输出格式
  quality: 85,           // JPG 质量
  maxPages: 20,          // 最大页数（用于预估容器宽度）
};

/**
 * 解析命令行参数
 */
function parseArgs() {
  const args = process.argv.slice(2);
  const config = { ...DEFAULT_CONFIG };
  let mdFile = null;
  let outDir = 'xhs-img';
  let title = '';

  for (let i = 0; i < args.length; i++) {
    const arg = args[i];
    if (arg === '--width') config.width = parseInt(args[++i]);
    else if (arg === '--height') config.height = parseInt(args[++i]);
    else if (arg === '--out') outDir = args[++i];
    else if (arg === '--title') title = args[++i];
    else if (arg === '--device-scale') config.deviceScale = parseFloat(args[++i]);
    else if (arg === '--format') config.format = args[++i];
    else if (arg === '--quality') config.quality = parseInt(args[++i]);
    else if (arg === '--max-pages') config.maxPages = parseInt(args[++i]);
    else if (!mdFile) mdFile = arg;
  }

  if (!mdFile) {
    console.error('Usage: node md2image.js <markdown-file> [options]');
    console.error('Options:');
    console.error('  --out <dir>           输出目录 (默认: xhs-img)');
    console.error('  --title <text>        文章标题');
    console.error('  --width <px>          单页宽度 (默认: 1440)');
    console.error('  --height <px>         单页高度 (默认: 1920)');
    console.error('  --device-scale <n>    设备像素比 (默认: 2)');
    console.error('  --format <png|jpg>    输出格式 (默认: png)');
    console.error('  --quality <n>         JPG 质量 (默认: 85)');
    console.error('  --max-pages <n>       最大页数 (默认: 20)');
    process.exit(1);
  }

  return { mdFile, outDir, title, config };
}

/**
 * 从 Markdown 提取标题
 */
function extractTitle(markdown) {
  const match = markdown.match(/^#\s+(.+?)$/m);
  return match ? match[1].trim() : '';
}

/**
 * 渲染 Markdown 为 HTML
 */
function renderMarkdown(markdown, mdFilePath) {
  const md = new MarkdownIt({
    html: false,
    linkify: true,
    typographer: true,
  });

  // 不渲染水平线（在小红书长文中常用作语义分隔，但视觉上干扰）
  md.renderer.rules.hr = () => '';

  let html = md.render(markdown);

  // 将相对路径图片转换为绝对路径
  const mdDir = path.dirname(path.resolve(mdFilePath));
  html = html.replace(/src="([^"]+)"/g, (match, src) => {
    if (src.startsWith('http') || src.startsWith('data:') || src.startsWith('file:')) {
      return match;
    }
    const absPath = path.resolve(mdDir, src);
    return `src="file://${absPath}"`;
  });

  return html;
}

/**
 * 生成 HTML 模板（使用 CSS 多列布局）
 */
function generateHTML(bodyHtml, title, config) {
  const { width, height, padding, gap, bodyFontPx, lineHeight, paragraphGap, titleScale, titleGap, maxPages } = config;

  // 容器宽度 = 单页宽度 × 最大页数
  const containerWidth = width * maxPages;

  const css = `
:root {
  --canvas-w: ${width}px;
  --canvas-h: ${height}px;
  --container-w: ${containerWidth}px;
  --pad: ${padding}px;
  --gap: ${gap}px;
  --content-font: ${bodyFontPx}px;
  --title-scale: ${titleScale};
  --title-gap: ${titleGap}px;
  --font: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", Arial, sans-serif;
}

* { box-sizing: border-box; }
html, body { margin: 0; padding: 0; background: #fff; }
body { font-family: var(--font); }

.container {
  width: var(--container-w);
  height: var(--canvas-h);
  padding: var(--pad) 0;
  column-width: var(--canvas-w);
  column-gap: 0;
  column-fill: auto;
}

.title {
  font-size: calc(var(--content-font) * var(--title-scale));
  font-weight: 800;
  line-height: 1.15;
  word-break: break-word;
  margin-bottom: var(--title-gap);
  padding-left: var(--pad);
  padding-right: var(--pad);
  break-after: avoid;
}

.content {
  font-size: var(--content-font);
  line-height: ${lineHeight};
  font-weight: 400;
  word-break: break-word;
  padding-left: var(--pad);
  padding-right: var(--pad);
}

.content p { margin: 0 0 ${paragraphGap}px; }
.content strong { font-weight: 800; }
.content em { font-style: italic; }
.content ul, .content ol { margin: 0 0 ${paragraphGap}px 1.2em; padding: 0; }
.content li { margin: 8px 0; }
.content blockquote {
  margin: 0 0 ${paragraphGap}px;
  padding: 12px 0 12px 20px;
  border-left: 6px solid #111;
}
.content blockquote p {
  margin: 5px 0;
}
.content code {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
  font-size: 0.95em;
  background: #f5f5f5;
  border-radius: 20px;
  padding: 10px;
}
.content a { color: inherit; text-decoration: underline; }
.content img { max-width: 100%; height: auto; display: block; }
`;

  const titleHtml = title ? `<div class="title">${escapeHtml(title)}</div>` : '';

  return `<!doctype html>
<html lang="zh-CN">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=${width}, height=${height}, initial-scale=1" />
    <title>${escapeHtml(title || 'XHS')}</title>
    <style>${css}</style>
  </head>
  <body>
    <div class="container">
      ${titleHtml}
      <div class="content">${bodyHtml}</div>
    </div>
  </body>
</html>`;
}

/**
 * HTML 转义
 */
function escapeHtml(text) {
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

/**
 * 查找系统 Chrome 可执行文件
 */
function findChromeExecutable() {
  const candidates = [];

  switch (process.platform) {
    case 'darwin':
      candidates.push(
        '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
        '/Applications/Google Chrome Canary.app/Contents/MacOS/Google Chrome Canary',
        '/Applications/Google Chrome Beta.app/Contents/MacOS/Google Chrome Beta',
        '/Applications/Chromium.app/Contents/MacOS/Chromium',
        '/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge',
      );
      break;
    case 'win32':
      candidates.push(
        'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
        'C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe',
        'C:\\Program Files\\Microsoft\\Edge\\Application\\msedge.exe',
        'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe',
      );
      break;
    default:
      candidates.push(
        '/usr/bin/google-chrome',
        '/usr/bin/google-chrome-stable',
        '/usr/bin/chromium',
        '/usr/bin/chromium-browser',
        '/snap/bin/chromium',
        '/usr/bin/microsoft-edge',
      );
      break;
  }

  // 检查文件是否存在
  for (const p of candidates) {
    if (fs.existsSync(p)) {
      console.log(`✓ 找到系统浏览器: ${p}`);
      return p;
    }
  }

  console.log('⚠️  未找到系统浏览器，将使用 Playwright 自带的 Chromium');
  return null;
}

/**
 * 计算实际页数并截图
 */
async function screenshotPages(htmlPath, outDir, config) {
  const { width, height, deviceScale, format, quality } = config;

  // 优先使用系统 Chrome
  const chromeExecutable = findChromeExecutable();
  const launchOptions = chromeExecutable ? { executablePath: chromeExecutable } : {};

  const browser = await chromium.launch(launchOptions);
  const context = await browser.newContext({
    viewport: { width: width * config.maxPages, height },
    deviceScaleFactor: deviceScale,
  });
  const page = await context.newPage();

  // 加载 HTML（确保使用绝对路径）
  const absoluteHtmlPath = path.resolve(htmlPath);
  await page.goto(`file://${absoluteHtmlPath}`, { waitUntil: 'networkidle' });

  // 计算实际页数（基于内容实际宽度，而不是容器宽度）
  const actualPages = await page.evaluate((w) => {
    const container = document.querySelector('.container');
    if (!container) return 1;

    // 获取容器内最后一个有内容的元素的位置
    const children = container.querySelectorAll('.title, .content > *');
    if (children.length === 0) return 1;

    let maxRight = 0;
    children.forEach(child => {
      const rect = child.getBoundingClientRect();
      const right = rect.right;
      if (right > maxRight) {
        maxRight = right;
      }
    });

    // 计算页数：最右边元素的位置 / 单页宽度
    const containerRect = container.getBoundingClientRect();
    const contentWidth = maxRight - containerRect.left;
    return Math.max(1, Math.ceil(contentWidth / w));
  }, width);

  console.log(`检测到 ${actualPages} 页`);

  // 创建输出目录
  if (!fs.existsSync(outDir)) {
    fs.mkdirSync(outDir, { recursive: true });
  }

  // 截取每一页（通过 clip 精确截取每一列）
  for (let i = 0; i < actualPages; i++) {
    const outputPath = path.join(outDir, `${String(i + 1).padStart(2, '0')}.${format}`);
    const screenshotOptions = {
      path: outputPath,
      clip: {
        x: i * width,  // 每一列的 x 偏移
        y: 0,
        width,
        height,
      },
    };

    if (format === 'jpg' || format === 'jpeg') {
      screenshotOptions.type = 'jpeg';
      screenshotOptions.quality = quality;
    }

    await page.screenshot(screenshotOptions);
    console.log(`已生成: ${outputPath}`);
  }

  await browser.close();
  return actualPages;
}

/**
 * 主函数
 */
async function main() {
  const { mdFile, outDir, title, config } = parseArgs();

  // 读取 Markdown 文件
  if (!fs.existsSync(mdFile)) {
    console.error(`文件不存在: ${mdFile}`);
    process.exit(1);
  }

  const markdown = fs.readFileSync(mdFile, 'utf-8');
  const docTitle = title || extractTitle(markdown) || path.basename(mdFile, '.md');

  console.log(`处理文件: ${mdFile}`);
  console.log(`标题: ${docTitle}`);

  // 渲染 Markdown
  const bodyHtml = renderMarkdown(markdown, mdFile);

  // 生成 HTML
  const html = generateHTML(bodyHtml, docTitle, config);

  // 保存临时 HTML 文件
  const tempDir = path.join(outDir, 'pages');
  if (!fs.existsSync(tempDir)) {
    fs.mkdirSync(tempDir, { recursive: true });
  }
  const htmlPath = path.join(tempDir, 'temp.html');
  fs.writeFileSync(htmlPath, html, 'utf-8');

  console.log(`已生成 HTML: ${htmlPath}`);

  // 截图
  const pageCount = await screenshotPages(htmlPath, outDir, config);

  console.log(`\n✅ 完成！共生成 ${pageCount} 张图片`);
  console.log(`输出目录: ${path.resolve(outDir)}`);
}

// 运行主函数
main().catch((error) => {
  console.error('错误:', error);
  process.exit(1);
});
