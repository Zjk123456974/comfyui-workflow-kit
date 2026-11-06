# Changelog

## [1.0.1] - 2026-11-06

- 新增 `.github/workflows/ci.yml`：push / PR / 手动触发，Python 3.9 / 3.11 / 3.13 矩阵跑单元测试
- CI 增加守卫步骤，禁止 `.safetensors` / `.gguf` 等权重文件被 git 跟踪
- README 增加 CI 状态徽章、目录结构更新与 Actions 工作流说明

## [1.0.0] - 2026-11-06

- 新增 `check.py`：扫描 ComfyUI 工作流 `.json`，提取引用的模型文件名并与本地 `models/` 核对
- 兼容 UI 格式与 API 格式；支持 `--workflows` / `--models` / `--json`
- 区分 `[OK]` / `[MISS]` / `[DIR]`，坏 JSON 单独报告，有缺件时退出码 1
- 新增 `MODELS.md`（Qwen-Image 下载清单与 8GB 显存档位）、`WORKFLOWS.md`（登记表与署名规则）
- 新增示例工作流、示例检查报告、16 项单元测试、MIT 许可证与 `.gitignore`（排除所有权重文件）
