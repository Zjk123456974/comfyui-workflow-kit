# comfyui-workflow-kit

> 给 ComfyUI 工作流「点名」：核对每个 `.json` 里写死的模型文件名，是否真的躺在正确的目录里。

一个零依赖的 Python 小工具 + 一份可持续维护的工作流登记表。
不依赖 ComfyUI、不下载模型、不联网，Python 3.9+ 直接跑。

## 为什么做这个

ComfyUI 的工作流 `.json` 里**硬编码了模型文件名**。别人分享的「8GB 显存优化」工作流，
引用的是他自己那套量化版（例如 `qwen-image-Q3_K_S.gguf`）；你花几十 GB 下回来的
却是官方 `qwen_image_fp8_e4m3fn.safetensors` —— 名字差一个字，加载节点就报红，
而且往往要等模型全下完才发现。

这个工具把「下载前」和「打开工作流前」的核对变成一条命令：

```bash
python check.py --workflows workflows --models D:/ComfyUI-下载/models
```

## 功能

- 递归扫描 `workflows/` 下所有 `.json`，兼容 ComfyUI 的 **UI 格式**与 **API 格式**
- 提取其中引用的 `.safetensors` / `.gguf` / `.ckpt` 等模型文件名，去重汇总
- 与本地 `models/` 目录比对，标出 `[OK]` / `[MISS]` 缺失 / `[DIR]` 放错目录
- 按文件名关键词给出**推荐子目录**（`diffusion_models` / `text_encoders` / `vae` / `loras`）
- 坏 JSON 单独报错，不中断整批检查；有缺件时退出码 1，方便接进脚本
- `--json` 输出机器可读报告

不指定 `--models` 时只列出引用清单，相当于一份「该下哪些文件」的购物单。

## 快速开始

```bash
# 1. 只看示例工作流引用了哪些模型（不需要装任何东西）
python check.py --workflows examples

# 2. 核对自己的工作流与本地模型
python check.py --workflows workflows --models D:/ComfyUI-下载/models

# 3. 机器可读报告
python check.py --workflows workflows --models D:/ComfyUI-下载/models --json > report.json

# 4. 跑单元测试
python -m unittest discover -s tests -v
```

输出示例（模型尚未下载时，完整内容见 `examples/sample_report.txt`）：

```
[1] sample_workflow.json
    [MISS] Qwen-Image-Lightning-8steps-V1.0.safetensors  -> 放到 models/loras/
    [MISS] qwen-image-Q3_K_S.gguf                        -> 放到 models/diffusion_models/
    [MISS] qwen_2.5_vl_7b_fp8_scaled.safetensors         -> 放到 models/text_encoders/
    [MISS] qwen_image_vae.safetensors                    -> 放到 models/vae/

汇总: 1 个工作流 / 4 项引用 / OK 0 / 缺失 4 / 目录不对 0 / 未核对 0
自检: FAILED（有缺件，退出码 1）
```

## 目录结构

```
comfyui-workflow-kit/
├── check.py                  # 核心核对器（零依赖）
├── README.md                 # 本文件
├── MODELS.md                 # Qwen-Image 模型下载清单与硬件档位
├── WORKFLOWS.md              # 工作流登记表（名称 / 用途 / 来源 / 许可证）
├── workflows/                # 放你自己的 .json（私有放 workflows/private/）
├── examples/
│   └── sample_workflow.json  # 结构样例，用于演示核对器
├── tests/test_check.py       # 单元测试
├── CHANGELOG.md
├── LICENSE                   # MIT
└── .gitignore
```

## 仓库里为什么没有模型文件

GitHub 不是放权重的地方（[官方限制](https://docs.github.com/zh/repositories/working-with-files/managing-large-files/about-large-files-on-github)）：

| 限制 | 数值 |
|---|---|
| 单文件硬上限 | 100 MiB（浏览器上传 25 MiB） |
| 仓库建议大小 | < 1 GB，强烈建议 < 5 GB |
| Git LFS 免费额度 | 1 GB 存储 + 1 GB / 月流量 |

而 Qwen-Image 最小量化版也要 7~12 GB，fp8 版约 20 GB。所以通行做法是
**权重放 Hugging Face / ModelScope，GitHub 放代码、工作流、清单和说明书** ——
本仓库就是后者。所有权重扩展名已被 `.gitignore` 排除，误放也会被挡住。

## 工作流收录与署名

`WORKFLOWS.md` 登记了工作流的名称、用途、模型要求和来源。
**第三方工作流请在确认原作者 LICENSE 后再把 `.json` 放进 `workflows/`**，
并保留署名；没有明确许可证的只登记链接、不收录文件本体。
本仓库自有的代码与文档采用 MIT 许可证，不覆盖第三方内容。

## 常见报红排查

| 现象 | 原因 |
|---|---|
| `Model not found` | 工作流引用的文件名与本地文件名不一致，用本工具 `[MISS]` 定位 |
| 打开一片红节点 | 缺自定义节点（`ComfyUI-GGUF` / `ComfyUI-nunchaku`），用 Manager 的 Install Missing Custom Nodes 补 |
| 连加载节点都没有 | ComfyUI 版本太旧，先更新 |
| 出图最后一步 OOM | 高分辨率下 VAE 解码瞬时占用高，开 tiling 或把 VAE 卸载到 CPU |

## 许可证

[MIT](LICENSE) © 2026 Zjk123456974
