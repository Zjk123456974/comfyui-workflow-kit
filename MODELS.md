# 模型下载清单（以 Qwen-Image 为例）

> 本文件只登记**文件名、目录和来源**，权重本体不进仓库。
> 具体该下哪一个，**永远以你手里工作流 `.json` 里写死的文件名为准**，
> 用 `python check.py --workflows workflows` 先列出来再下。

## 一、先看你的显卡能吃哪一档

| 版本 | 主模型体积 | 显存需求 | 8GB 卡 / 16GB 内存 |
|---|---|---|---|
| BF16 完整 | ~41 GB | 40 GB+ | 不可行 |
| fp8 官方版 | ~20 GB | 16~24 GB | 不可行（内存也不够） |
| GGUF Q4_K_M | ~13 GB | 峰值约 14 GB | 勉强，需激进卸载，极慢 |
| GGUF Q3_K_S | ~9.8 GB | 约 10 GB | 可行，质量有损 |
| GGUF Q2_K | ~7.5 GB | 约 8 GB | 可行，文字渲染明显变糊 |
| Nunchaku int4 | ~11.5~12.7 GB | 8 GB 显存 + 16 GB 内存 | 可行，需装对应自定义节点 |

社区所谓「8GB 显存优化」工作流，基本落在**最后三档**，并搭配
4 步 / 8 步 Lightning LoRA 把采样步数压下来。代价是出图按分钟计，
且 Qwen-Image 最拿手的「图里写中文」会最先退化。

> 实测参考环境：RTX 4060 Laptop（8188 MiB）、16 GB 内存、D 盘剩余 125 GB。
> 模型一律放 D 盘，C 盘只剩 62 GB 不建议装。

## 二、官方四件套（ComfyUI 原生模板用）

文件必须直接放在**一级目录**，塞进子文件夹会检测不到（也可在加载节点里手动选）。

| 文件 | 放到 `models/` 的 | 参考体积 |
|---|---|---|
| `qwen_image_fp8_e4m3fn.safetensors` | `diffusion_models/` | ~20 GB |
| `qwen_2.5_vl_7b_fp8_scaled.safetensors` | `text_encoders/` | ~9 GB |
| `qwen_image_vae.safetensors` | `vae/` | ~0.25 GB |
| `Qwen-Image-Lightning-8steps-V1.0.safetensors` | `loras/` | 数百 MB |

对应加载节点：`Load Diffusion Model` / `Load CLIP` / `Load VAE`，
以及可选的 Lightning LoRA（8 步加速）。蒸馏版与 Lightning LoRA 一般不要同时启用。

## 三、去哪下

| 来源 | 地址 |
|---|---|
| Comfy-Org 官方打包（Hugging Face） | https://huggingface.co/Comfy-Org/Qwen-Image_ComfyUI/tree/main/split_files |
| ModelScope 国内镜像 | https://modelscope.cn/models/Comfy-Org/Qwen-Image_ComfyUI/files |
| Lightning 加速 LoRA | https://huggingface.co/lightx2v/Qwen-Image-Lightning |
| ComfyUI 官方 Qwen-Image 教程 | https://docs.comfy.org/tutorials/image/qwen/qwen-image |

GGUF / Nunchaku 量化版由不同社区作者发布、文件名各不相同，
请以你所使用的工作流作者给出的清单为准，不要照抄本表文件名。

## 四、下载完这样验一遍

```bash
python check.py --workflows workflows --models D:/ComfyUI-下载/models
```

- `[MISS]`：还差这个文件，按提示的 `expect_dir` 补齐
- `[DIR ]`：文件在，但放错子目录，移过去即可
- 全部 `[OK]` 且 `自检: OK` 后，再打开 ComfyUI 加载工作流

## 五、低显存跑不起来的常见原因

1. 量化版需要 `ComfyUI-GGUF` 或 `ComfyUI-nunchaku` 自定义节点，缺了就是一片红节点
2. ComfyUI 版本过旧，没有 Qwen-Image 的加载节点，先更新
3. 文本编码器 fp8 版约 9 GB，内存紧张时会触发大量换页，出图很慢
4. VAE 解码在高分辨率下有瞬时峰值，可开 tiling 或把 VAE 卸载到 CPU
5. 只是想先熟悉流程：先跑 SDXL 一类小模型练手，再上 20B 的 Qwen-Image
