# TikZ 图片转换流程

> PNG 优先策略失效时使用此流程

## 1. 快速转换（推荐）

```bash
# 预览
python3 tools/images/convert_images_to_tikz_templates.py --dry-run <tex_file>

# 执行（自动备份 .bak）
python3 tools/images/convert_images_to_tikz_templates.py <tex_file>
```

**v2.0 特性**: 自动 center 包裹、排除表格、转义 CONTEXT

## 2. Agent 流水线

```bash
# 导出任务
python3 tools/images/export_image_jobs.py --files <tex_file>

# AI 生成 → generated_tikz.jsonl

# 写入片段
python3 tools/images/write_snippets_from_jsonl.py \
  --jobs-file image_jobs.jsonl --tikz-file generated_tikz.jsonl

# 回填 TeX
python3 tools/images/apply_tikz_snippets.py --tex-file <tex_file>
```

## 3. 相关文档

| 文档 | 内容 |
|------|------|
| [TIKZ_AGENT_PROMPT.md](TIKZ_AGENT_PROMPT.md) | AI Agent 系统提示词 |
| [IMAGE_JOBS_FULL.md](IMAGE_JOBS_FULL.md) | JSONL 字段定义 |
| [REFERENCE.md](REFERENCE.md) | IMAGE_TODO 格式规范 |
