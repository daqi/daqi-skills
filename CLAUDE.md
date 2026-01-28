# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

这是一个 Claude Code skills 集合，专注于文章写作和内容创作流程。作者是"大齐"，AI 领域资深从业者和技术博主。

## 项目结构

```
skills/
├── article-analyzer/    # 文章深度分析（核心论点、逻辑、价值提取）
├── article-outliner/    # 生成写作提纲（多方案、差异化策略）
├── article-writer/      # 大齐风格初稿撰写
├── article-polish/      # 润色校对（去 AI 味、格式标准化）
├── article-producer/    # 一站式全流程（分析→策划→撰写→打磨）
├── html-parser-rule/    # HTML 解析规则编写与测试
└── skill-manager/       # skill 查询与管理
```

## 文章创作流水线

主要工作流：素材 → `article-analyzer` → `article-outliner` → `article-writer` → `article-polish`

- **article-producer** 封装了完整的一键流程
- 所有产物存储在 `posts/YYYY/MM/DD/[slug]/` 目录
- 文件命名：`source-*.md`（素材）、`analysis.md`、`outline-*.md`、`article-*.md`

## 大齐写作风格要点

- 语调：像老朋友聊天，平和、真诚、自信
- 禁止 AI 味用语："综上所述"、"首先其次最后"、"众所周知"
- 必须：使用生活比喻解释技术概念
- 格式：中英文间加空格，中文语境用全角标点

## 术语表

- Token → Token
- AI Agent → AI 智能体
- Vibe Coding → 凭感觉编程
- LLM → 大模型

## 发布流程

使用 `/release-skills` 执行发布，会自动：
1. 检测 `.claude-plugin/marketplace.json` 中的版本
2. 分析 git 提交历史
3. 更新 CHANGELOG.md 和 CHANGELOG.zh.md
4. 创建版本提交和标签
