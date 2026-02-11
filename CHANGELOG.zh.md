# 更新日志

本项目的所有重要变更都将记录在此文件中。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)，
版本号遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

## 0.1.1 - 2026-02-11

### 修复
- 优化 `xhs-md2img` 的排版细节与流程说明

## 0.1.0 - 2026-02-11

### 新功能
- 将 `xhs-md-screenshot-images` 更名为 `xhs-md2img`

## 0.0.5 - 2026-02-06

### 修复
- 优化 `xhs-md-screenshot-images` 截图中引用与代码的样式

## 0.0.4 - 2026-02-06

### 新功能
- 新增 `xhs-md-to-plain-text`：将 Markdown 转为适合小红书发布的纯文本

## 0.0.3 - 2026-02-06

### 重构
- 将 `xhs-md-screenshot-images` 的 md2image 脚本切换为 Bun（TypeScript）实现

## 0.0.1 - 2026-01-28

### 新功能
- 添加 CLAUDE.md 项目指南和结构说明

### 修复
- 修正 article-producer 中的 skill 引用名称 (outliner → article-outliner, writer-agent → article-writer, polish → article-polish)

## 0.0.2 - 2026-02-05

### 新功能
- 新增 `xhs-writer`：小红书爆款文案助手（S.L.R.A. 模型）
- 新增 `xhs-md-screenshot-images`：将小红书 Markdown 渲染为 HTML 并用 Playwright 截图导出图片
